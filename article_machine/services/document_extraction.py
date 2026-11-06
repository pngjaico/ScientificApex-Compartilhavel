"""Document extraction: PDF/DOCX/image -> text, tables and page-level provenance.

Design rules (to avoid future conflicts):
- Originals are never modified; outputs go to a separate folder keyed by source SHA-256.
- Runs are idempotent: same source hash + extractor version + options => cached result.
- Per page, native text (pdfplumber, with duplicate-glyph removal) is scored; pages with
  no/garbled text fall back to Tesseract OCR (por+eng when available).
- Tesseract is called via CLI on images written to an ASCII-only temp dir (Windows paths
  with accents break some Tesseract builds) and with a per-page timeout.
- Every OCR page and every extracted table is flagged ``needs_human_verification``:
  OCR/table output is never evidence by itself (Evidence Lock still applies).
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .scientific_execution import project_ancestor, scientific_execution_gate

EXTRACTOR_VERSION = "document-extraction/1.1"
PDF_SUFFIXES = {".pdf"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
DOCX_SUFFIXES = {".docx"}
SUPPORTED_SUFFIXES = PDF_SUFFIXES | IMAGE_SUFFIXES | DOCX_SUFFIXES
DEFAULT_TESSERACT_PATHS = (
    Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
    Path("C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"),
    Path("/usr/bin/tesseract"),
    Path("/usr/local/bin/tesseract"),
    Path("/opt/homebrew/bin/tesseract"),
)
MIN_NATIVE_CHARS = 40
OCR_TIMEOUT_SECONDS = 180


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ascii_slug(text: str, max_len: int = 60) -> str:
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", norm).strip("_").lower()
    return (slug or "documento")[:max_len]


# --------------------------------------------------------------------------- Tesseract


def resolve_tesseract() -> dict[str, Any]:
    """Locate tesseract binary, tessdata dir and installed languages."""
    candidates: list[Path] = []
    env_cmd = os.environ.get("TESSERACT_CMD")
    if env_cmd:
        candidates.append(Path(env_cmd))
    which = shutil.which("tesseract")
    if which:
        candidates.append(Path(which))
    candidates.extend(DEFAULT_TESSERACT_PATHS)
    cmd = next((c for c in candidates if c.is_file()), None)
    if cmd is None:
        return {"available": False, "issues": ["Tesseract not found (set TESSERACT_CMD or install it)."]}

    tessdata: Path | None = None
    for raw in (os.environ.get("ARTICLE_MACHINE_TESSDATA"), str(_workspace_root() / "ferramentas" / "tessdata")):
        if raw and Path(raw).is_dir() and any(Path(raw).glob("*.traineddata")):
            tessdata = Path(raw)
            break

    args = [str(cmd)]
    if tessdata:
        args += ["--tessdata-dir", str(tessdata)]
    try:
        version_out = subprocess.run([str(cmd), "--version"], capture_output=True, text=True, timeout=20, check=False)
        langs_out = subprocess.run([*args, "--list-langs"], capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "cmd": str(cmd), "issues": [f"Tesseract failed to start: {exc}"]}

    version_text = (version_out.stdout or version_out.stderr or "").strip().splitlines()
    langs = [
        line.strip()
        for line in (langs_out.stdout or "").splitlines()[1:]
        if line.strip() and not line.lower().startswith("list of")
    ]
    issues = []
    if "por" not in langs:
        issues.append("Portuguese model (por.traineddata) missing: OCR of PT-BR documents will lose accents.")
    return {
        "available": True,
        "cmd": str(cmd),
        "tessdata_dir": str(tessdata) if tessdata else None,
        "version": version_text[0] if version_text else "unknown",
        "languages": langs,
        "default_lang": "+".join(lang for lang in ("por", "eng") if lang in langs) or "eng",
        "issues": issues,
    }


def _ocr_image_file(image_path: Path, tess: dict[str, Any], lang: str, psm: int = 3) -> tuple[str, float | None]:
    """Run tesseract TSV on an image; return (text, mean word confidence 0-100)."""
    args = [tess["cmd"]]
    if tess.get("tessdata_dir"):
        args += ["--tessdata-dir", tess["tessdata_dir"]]
    args += [str(image_path), "stdout", "-l", lang, "--psm", str(psm), "-c", "tessedit_create_tsv=1"]
    proc = subprocess.run(
        args, capture_output=True, timeout=OCR_TIMEOUT_SECONDS, check=False, encoding="utf-8", errors="replace"
    )
    if proc.returncode != 0:
        raise RuntimeError(f"tesseract exit {proc.returncode}: {proc.stderr.strip()[:300]}")
    lines: dict[tuple[str, str, str, str], list[str]] = {}
    order: list[tuple[str, str, str, str]] = []
    confs: list[float] = []
    reader = csv.DictReader(proc.stdout.splitlines(), delimiter="\t", quoting=csv.QUOTE_NONE)
    for row in reader:
        word = (row.get("text") or "").strip()
        if not word:
            continue
        try:
            conf = float(row.get("conf") or -1)
        except ValueError:
            conf = -1
        if conf >= 0:
            confs.append(conf)
        key = (row.get("page_num", ""), row.get("block_num", ""), row.get("par_num", ""), row.get("line_num", ""))
        if key not in lines:
            lines[key] = []
            order.append(key)
        lines[key].append(word)
    text_lines: list[str] = []
    prev_par: tuple[str, str, str] | None = None
    for key in order:
        par = key[:3]
        if prev_par is not None and par != prev_par:
            text_lines.append("")
        text_lines.append(" ".join(lines[key]))
        prev_par = par
    mean_conf = round(sum(confs) / len(confs), 1) if confs else None
    return "\n".join(text_lines).strip(), mean_conf


def _ocr_pil_image(image: Any, tess: dict[str, Any], lang: str) -> tuple[str, float | None]:
    # ASCII-only temp path: avoids Tesseract failures on accented Windows paths.
    tmp_dir = Path(tempfile.mkdtemp(prefix="am_ocr_"))
    try:
        img_path = tmp_dir / "page.png"
        image.convert("L").save(img_path, format="PNG")
        return _ocr_image_file(img_path, tess, lang)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# --------------------------------------------------------------------------- Text quality


_DOUBLED_TOKEN = re.compile(r"\b(\S{4,})\b")


def collapse_doubled_glyphs(text: str) -> str:
    """Fix fake-bold PDFs where each glyph is drawn twice ('CCEERRTTIIFF' -> 'CERTIF')."""

    def fix(match: re.Match[str]) -> str:
        token = match.group(1)
        if len(token) % 2 == 0 and token[0::2] == token[1::2]:
            return token[0::2]
        return token

    return _DOUBLED_TOKEN.sub(fix, text)


def text_quality(text: str) -> dict[str, Any]:
    """Heuristic score for extracted text (0-1). Low = empty, garbled or scrambled."""
    stripped = text.strip()
    tokens = stripped.split()
    chars = len(stripped)
    if not tokens:
        return {"chars": 0, "score": 0.0, "single_char_ratio": 1.0, "alpha_ratio": 0.0}
    alpha = sum(ch.isalpha() for ch in stripped)
    alpha_ratio = alpha / max(chars, 1)
    single = sum(1 for t in tokens if len(t) == 1 and t.isalpha())
    single_ratio = single / len(tokens)
    replacement = stripped.count("\ufffd") + stripped.count("(cid:")
    score = alpha_ratio * (1 - min(single_ratio * 2, 1)) * (1 - min(replacement / max(len(tokens), 1), 1))
    if chars < MIN_NATIVE_CHARS:
        score *= chars / MIN_NATIVE_CHARS
    return {
        "chars": chars,
        "score": round(score, 3),
        "single_char_ratio": round(single_ratio, 3),
        "alpha_ratio": round(alpha_ratio, 3),
    }


def _needs_ocr(quality: dict[str, Any]) -> bool:
    return bool(quality["chars"] < MIN_NATIVE_CHARS or quality["score"] < 0.45 or quality["single_char_ratio"] > 0.25)


# --------------------------------------------------------------------------- Tables


def _write_table_csv(rows: list[list[Any]], target: Path) -> dict[str, Any]:
    clean = [["" if cell is None else " ".join(str(cell).split()) for cell in row] for row in rows]
    clean = [row for row in clean if any(cell for cell in row)]
    target.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig so Excel (pt-BR) opens accents correctly.
    with target.open("w", encoding="utf-8-sig", newline="") as handle:
        csv.writer(handle).writerows(clean)
    n_cols = max((len(r) for r in clean), default=0)
    filled = sum(1 for r in clean for c in r if c)
    total = sum(len(r) for r in clean) or 1
    return {"rows": len(clean), "cols": n_cols, "fill_ratio": round(filled / total, 3)}


def _extract_page_tables(page: Any, strategy: str) -> list[list[list[Any]]]:
    settings_by_strategy = {
        "lines": {"vertical_strategy": "lines", "horizontal_strategy": "lines"},
        "text": {"vertical_strategy": "text", "horizontal_strategy": "text", "min_words_vertical": 3},
    }
    strategies = ["lines", "text"] if strategy == "both" else [strategy]
    for strat in strategies:
        tables = page.extract_tables(table_settings=settings_by_strategy[strat])
        tables = [t for t in tables if t and len(t) >= 2 and max(len(r) for r in t) >= 2]
        if tables:
            return tables
    return []


# --------------------------------------------------------------------------- Extractors


def _extract_pdf(
    source: Path,
    out_dir: Path,
    *,
    ocr: str,
    lang: str | None,
    dpi: int,
    table_strategy: str,
    max_pages: int | None,
) -> dict[str, Any]:
    import pdfplumber
    import pypdfium2 as pdfium  # type: ignore[import-untyped]

    tess = resolve_tesseract() if ocr != "off" else {"available": False, "issues": ["OCR disabled."]}
    ocr_lang = lang or tess.get("default_lang", "eng")
    pages: list[dict[str, Any]] = []
    tables_meta: list[dict[str, Any]] = []
    raw_issues = tess.get("issues")
    warnings: list[str] = [str(x) for x in raw_issues] if ocr != "off" and isinstance(raw_issues, list) else []

    with pdfplumber.open(str(source)) as pdf:
        pdf_doc = pdfium.PdfDocument(str(source))
        try:
            n_pages = len(pdf.pages)
            limit = min(n_pages, max_pages) if max_pages else n_pages
            for idx in range(limit):
                page = pdf.pages[idx].dedupe_chars()
                native = collapse_doubled_glyphs(page.extract_text(layout=False) or "")
                native_q = text_quality(native)
                method, text, conf = "native", native, None
                do_ocr = ocr == "force" or (ocr == "auto" and _needs_ocr(native_q))
                if do_ocr and tess.get("available"):
                    try:
                        bitmap = pdf_doc[idx].render(scale=dpi / 72)
                        ocr_text, conf = _ocr_pil_image(bitmap.to_pil(), tess, str(ocr_lang))
                        ocr_q = text_quality(ocr_text)
                        if ocr == "force" or ocr_q["score"] >= native_q["score"]:
                            method, text = "ocr", ocr_text
                        else:
                            method = "native(ocr_rejected)"
                    except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
                        warnings.append(f"Page {idx + 1}: OCR failed ({exc}); kept native text.")
                elif do_ocr:
                    warnings.append(f"Page {idx + 1}: needs OCR but Tesseract unavailable.")

                page_tables: list[str] = []
                if table_strategy != "off" and method.startswith("native"):
                    for t_idx, rows in enumerate(_extract_page_tables(page, table_strategy), start=1):
                        rel = Path("tables") / f"p{idx + 1:03d}_t{t_idx:02d}.csv"
                        meta = _write_table_csv(rows, out_dir / rel)
                        meta.update({"page": idx + 1, "path": rel.as_posix(), "needs_human_verification": True})
                        tables_meta.append(meta)
                        page_tables.append(rel.as_posix())
                elif table_strategy != "off" and method == "ocr":
                    warnings.append(f"Page {idx + 1}: scanned page - tables not extracted (transcribe manually).")

                final_q = text_quality(text)
                pages.append(
                    {
                        "page": idx + 1,
                        "method": method,
                        "chars": final_q["chars"],
                        "quality_score": final_q["score"],
                        "native_quality_score": native_q["score"],
                        "ocr_mean_confidence": conf,
                        "tables": page_tables,
                        "needs_human_verification": method == "ocr" or final_q["score"] < 0.45,
                        "text": text,
                    }
                )
            if limit < n_pages:
                warnings.append(f"Only first {limit} of {n_pages} pages processed (max_pages).")
        finally:
            pdf_doc.close()

    return {
        "page_count_total": n_pages,
        "pages": pages,
        "tables": tables_meta,
        "warnings": warnings,
        "ocr_engine": {k: tess.get(k) for k in ("version", "tessdata_dir")} | {"lang": ocr_lang}
        if tess.get("available")
        else None,
    }


def _extract_image(source: Path, *, lang: str | None) -> dict[str, Any]:
    from PIL import Image

    tess = resolve_tesseract()
    if not tess.get("available"):
        raise RuntimeError("; ".join(tess.get("issues", ["Tesseract unavailable"])))
    ocr_lang = lang or tess["default_lang"]
    with Image.open(source) as img:
        text, conf = _ocr_pil_image(img, tess, ocr_lang)
    q = text_quality(text)
    return {
        "page_count_total": 1,
        "pages": [
            {
                "page": 1,
                "method": "ocr",
                "chars": q["chars"],
                "quality_score": q["score"],
                "native_quality_score": 0.0,
                "ocr_mean_confidence": conf,
                "tables": [],
                "needs_human_verification": True,
                "text": text,
            }
        ],
        "tables": [],
        "warnings": list(tess.get("issues", [])),
        "ocr_engine": {"version": tess["version"], "tessdata_dir": tess["tessdata_dir"], "lang": ocr_lang},
    }


def _extract_docx(source: Path, out_dir: Path) -> dict[str, Any]:
    import docx

    document = docx.Document(str(source))
    text = "\n".join(p.text for p in document.paragraphs)
    tables_meta: list[dict[str, Any]] = []
    for t_idx, table in enumerate(document.tables, start=1):
        rows = [[cell.text for cell in row.cells] for row in table.rows]
        rel = Path("tables") / f"docx_t{t_idx:02d}.csv"
        meta = _write_table_csv(rows, out_dir / rel)
        meta.update({"page": None, "path": rel.as_posix(), "needs_human_verification": False})
        tables_meta.append(meta)
    q = text_quality(text)
    return {
        "page_count_total": 1,
        "pages": [
            {
                "page": 1,
                "method": "docx",
                "chars": q["chars"],
                "quality_score": q["score"],
                "native_quality_score": q["score"],
                "ocr_mean_confidence": None,
                "tables": [t["path"] for t in tables_meta],
                "needs_human_verification": False,
                "text": text,
            }
        ],
        "tables": tables_meta,
        "warnings": [],
        "ocr_engine": None,
    }


# --------------------------------------------------------------------------- Public API


def extract_document(
    source: Path,
    output_root: Path,
    *,
    ocr: str = "auto",
    lang: str | None = None,
    dpi: int = 300,
    table_strategy: str = "lines",
    max_pages: int | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Extract one document into ``output_root/<slug>_<sha8>/`` (text.md, pages.jsonl, tables/, manifest.json)."""
    source = Path(source).resolve()
    for project in {project_ancestor(source), project_ancestor(output_root)} - {None}:
        if project is None:
            continue
        gate = scientific_execution_gate(project, "document-extraction", mark_started=True)
        if gate["status"] != "pass":
            return gate
    if ocr not in {"auto", "force", "off"}:
        raise ValueError("ocr must be auto|force|off")
    if table_strategy not in {"lines", "text", "both", "off"}:
        raise ValueError("table_strategy must be lines|text|both|off")
    if not source.is_file():
        return {"contract": "DocumentExtractionV1", "status": "blocked", "issues": [f"File not found: {source}"]}
    suffix = source.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        return {
            "contract": "DocumentExtractionV1",
            "status": "skipped",
            "source": str(source),
            "issues": [f"Unsupported type '{suffix}'."],
        }

    sha = _sha256(source)
    out_dir = Path(output_root).resolve() / f"{_ascii_slug(source.stem)}_{sha[:8]}"
    manifest_path = out_dir / "manifest.json"
    options = {"ocr": ocr, "lang": lang, "dpi": dpi, "table_strategy": table_strategy, "max_pages": max_pages}

    if manifest_path.is_file() and not force:
        try:
            cached: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
            if (
                cached.get("source_sha256") == sha
                and cached.get("extractor_version") == EXTRACTOR_VERSION
                and cached.get("options") == options
                and isinstance(cached.get("derived_sha256"), dict)
                and bool(cached["derived_sha256"])
                and {"text.md", "pages.jsonl"}.issubset(cached["derived_sha256"])
                and set(cached["derived_sha256"])
                == {p.relative_to(out_dir).as_posix() for p in out_dir.rglob("*") if p.is_file() and p != manifest_path}
                and all(
                    (out_dir / rel).resolve().is_relative_to(out_dir)
                    and (out_dir / rel).is_file()
                    and _sha256(out_dir / rel) == digest
                    for rel, digest in cached["derived_sha256"].items()
                )
            ):
                cached["cached"] = True
                return cached
        except (OSError, json.JSONDecodeError):
            pass

    archived_output = None
    if out_dir.exists():
        if source.is_relative_to(out_dir) or out_dir.is_symlink() or out_dir.is_junction():
            return {
                "contract": "DocumentExtractionV1",
                "status": "blocked",
                "issues": ["Unsafe derived output path; originals and links are preserved."],
            }
        try:
            previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            previous = {}
        if not isinstance(previous, dict) or previous.get("source_sha256") != sha:
            return {
                "contract": "DocumentExtractionV1",
                "status": "blocked",
                "issues": ["Existing output is not identifiable as this extractor's artifact; preserved."],
            }
        archived = out_dir.with_name(out_dir.name + "_anterior_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f"))
        if not archived.resolve().is_relative_to(Path(output_root).resolve()):
            raise ValueError("Archive must remain within the explicit output root")
        out_dir.rename(archived)
        archived_output = str(archived)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        if suffix in PDF_SUFFIXES:
            result = _extract_pdf(
                source,
                out_dir,
                ocr=ocr,
                lang=lang,
                dpi=dpi,
                table_strategy=table_strategy,
                max_pages=max_pages,
            )
        elif suffix in IMAGE_SUFFIXES:
            result = _extract_image(source, lang=lang)
        else:
            result = _extract_docx(source, out_dir)
    except Exception as exc:  # encrypted/corrupted files must not abort a batch
        # Preserve partial derived artifacts for diagnosis; no recursive deletion.
        return {
            "contract": "DocumentExtractionV1",
            "status": "blocked",
            "source": str(source),
            "source_sha256": sha,
            "failed_output_dir": str(out_dir),
            "issues": [f"{type(exc).__name__}: {exc}"],
        }

    pages = result["pages"]
    with (out_dir / "pages.jsonl").open("w", encoding="utf-8") as handle:
        for page in pages:
            handle.write(json.dumps(page, ensure_ascii=False) + "\n")
    md_parts = [f"# {source.name}\n"]
    for page in pages:
        conf = page["ocr_mean_confidence"]
        conf_txt = f" | ocr_conf={conf}" if conf is not None else ""
        md_parts.append(f"\n<!-- page {page['page']} | {page['method']} | q={page['quality_score']}{conf_txt} -->\n")
        md_parts.append(page["text"])
    (out_dir / "text.md").write_text("\n".join(md_parts).strip() + "\n", encoding="utf-8")

    methods = [p["method"] for p in pages]
    flagged = [p["page"] for p in pages if p["needs_human_verification"]]
    manifest = {
        "contract": "DocumentExtractionV1",
        "status": "pass",
        "cached": False,
        "archived_previous_output": archived_output,
        "extractor_version": EXTRACTOR_VERSION,
        "extracted_at": datetime.now(UTC).isoformat(),
        "source": str(source),
        "source_name": source.name,
        "source_sha256": sha,
        "source_size_bytes": source.stat().st_size,
        "options": options,
        "output_dir": str(out_dir),
        "page_count_total": result["page_count_total"],
        "pages_processed": len(pages),
        "pages_by_method": {m: methods.count(m) for m in sorted(set(methods))},
        "pages_needing_verification": flagged,
        "table_count": len(result["tables"]),
        "tables": result["tables"],
        "ocr_engine": result["ocr_engine"],
        "warnings": result["warnings"],
        "derived_sha256": {
            p.relative_to(out_dir).as_posix(): _sha256(p)
            for p in sorted(out_dir.rglob("*"))
            if p.is_file() and p != manifest_path
        },
        "evidence_policy": (
            "Derived text. OCR pages and all PDF tables must be checked against the original before any "
            "number enters extraction sheets or claim_map (Evidence Lock)."
        ),
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def extract_documents(
    input_path: Path,
    output_root: Path,
    **kwargs: Any,
) -> dict[str, Any]:
    """Extract a file or every supported file in a folder (recursive); writes an index.json."""
    input_path = Path(input_path).resolve()
    for project in {project_ancestor(input_path), project_ancestor(output_root)} - {None}:
        if project is None:
            continue
        gate = scientific_execution_gate(project, "document-batch-extraction")
        if gate["status"] != "pass":
            return gate
    if input_path.is_dir():
        files = sorted(p for p in input_path.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES)
    else:
        files = [input_path]
    output_root = Path(output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    results = [extract_document(f, output_root, **kwargs) for f in files]
    summary = [
        {
            "source": r.get("source_name") or r.get("source"),
            "status": r.get("status"),
            "cached": r.get("cached", False),
            "pages_by_method": r.get("pages_by_method"),
            "pages_needing_verification": r.get("pages_needing_verification"),
            "table_count": r.get("table_count"),
            "output_dir": r.get("output_dir"),
            "issues": r.get("issues", []) + r.get("warnings", []),
        }
        for r in results
    ]
    index: dict[str, Any] = {
        "contract": "DocumentExtractionIndexV1",
        "status": "pass" if results and all(r.get("status") in {"pass", "skipped"} for r in results) else "blocked",
        "generated_at": datetime.now(UTC).isoformat(),
        "extractor_version": EXTRACTOR_VERSION,
        "input": str(input_path),
        "output_root": str(output_root),
        "file_count": len(files),
        "documents": summary,
    }
    if not files:
        index["status"] = "blocked"
        index["issues"] = [f"No supported files in {input_path} ({sorted(SUPPORTED_SUFFIXES)})."]
    (output_root / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return index


def extract_project_documents(project_dir: Path, input_path: Path | None = None, **kwargs: Any) -> dict[str, Any]:
    """Project wrapper: default input ``sources/fulltext`` (or sources/), output ``sources/extracted/``."""
    root = Path(project_dir).resolve()
    gate = scientific_execution_gate(root, "project-document-extraction")
    if gate["status"] != "pass":
        return gate
    if not (root / "project.yaml").is_file():
        return {"contract": "DocumentExtractionIndexV1", "status": "blocked", "issues": [f"Not a project: {root}"]}
    if input_path is None:
        candidates = [root / "sources" / "fulltext", root / "sources" / "fulltexts", root / "sources"]
        input_path = next((c for c in candidates if c.is_dir()), root / "sources")
    else:
        input_path = Path(input_path)
        if not input_path.is_absolute():
            input_path = root / input_path
    output_root = root / "sources" / "extracted"
    if input_path.resolve().is_relative_to(output_root.resolve()):
        return {
            "contract": "DocumentExtractionIndexV1",
            "status": "blocked",
            "issues": ["Input is inside sources/extracted (would re-extract derived files)."],
        }
    if input_path.resolve() == (root / "sources").resolve():
        # never recurse into our own outputs or dataset dumps
        files = [
            p
            for p in input_path.rglob("*")
            if p.is_file()
            and p.suffix.lower() in SUPPORTED_SUFFIXES
            and "extracted" not in p.relative_to(input_path).parts
            and "datasets" not in p.relative_to(input_path).parts
        ]
        output_root.mkdir(parents=True, exist_ok=True)
        results = [extract_document(f, output_root, **kwargs) for f in sorted(files)]
        index: dict[str, Any] = {
            "contract": "DocumentExtractionIndexV1",
            "status": "pass" if results and all(r.get("status") in {"pass", "skipped"} for r in results) else "blocked",
            "generated_at": datetime.now(UTC).isoformat(),
            "extractor_version": EXTRACTOR_VERSION,
            "input": str(input_path),
            "output_root": str(output_root),
            "file_count": len(files),
            "documents": [
                {
                    "source": r.get("source_name") or r.get("source"),
                    "status": r.get("status"),
                    "pages_by_method": r.get("pages_by_method"),
                    "pages_needing_verification": r.get("pages_needing_verification"),
                    "table_count": r.get("table_count"),
                    "output_dir": r.get("output_dir"),
                    "issues": r.get("issues", []) + r.get("warnings", []),
                }
                for r in results
            ],
        }
        if not files:
            index["status"] = "blocked"
            index["issues"] = ["No supported documents found under sources/."]
        (output_root / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
        return index
    return extract_documents(input_path, output_root, **kwargs)
