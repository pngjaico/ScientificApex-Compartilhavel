"""PRISMA-S & PRISMA 2020 Multi-Database Search, Drop-Folder Import & Zero-Loss Deduplication Engine.

Handles:
1. Search string compilation across PubMed, Scopus, Embase, Cochrane CENTRAL, Europe PMC, OpenAlex, and LILACS/BVS.
2. Creation of explicit manual drop-folders (e.g., sources/manual_imports/embase/) with bilingual instructions.
3. Live API retrieval for PubMed (NCBI E-utilities) and Scopus (Elsevier API when SCOPUS_API_KEY is present).
4. Zero-loss parsing of .ris, .nbib/.medline, .csv, and .json/.jsonl files preserving all raw fields.
5. 3-stage deterministic deduplication (DOI -> PMID/EID/PUI -> Normalized Title+Year+Author) with field enrichment.
6. PRISMA 2020 flow accounting (prisma_flow_counts.json) and bilingual search reports.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..ingest import register_source
from ..serialization import load_structured_file, save_structured_file
from ..zero_trust import COMPILED_QUERY_PATH, build_retrieval_plan, compile_query_plan
from .protocol_registration import registration_gate

MANUAL_DROP_PROVIDERS = ("embase", "scopus", "cochrane_central", "lilacs_bvs", "pubmed", "europe_pmc", "openalex")
NCBI_EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
SCOPUS_SEARCH_URL = "https://api.elsevier.com/content/search/scopus"
USER_AGENT = "ArticleMachine/0.3.0"


def _get_env_secret(key_name: str, workspace_root: Path | None = None) -> str | None:
    val = os.environ.get(key_name)
    if val and val.strip():
        return val.strip()
    root = Path(workspace_root) if workspace_root else Path.cwd()
    for candidate in (root / ".env", Path.cwd() / ".env"):
        if candidate.is_file():
            try:
                for line in candidate.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    if k.strip() == key_name and v.strip().strip("'\""):
                        return v.strip().strip("'\"")
            except OSError:
                pass
    return None


def normalize_doi(raw_doi: Any) -> str:
    if not raw_doi:
        return ""
    val = str(raw_doi).strip().lower()
    val = re.sub(r"^https?://(dx\.)?doi\.org/", "", val)
    val = re.sub(r"^doi:\s*", "", val)
    val = re.sub(r"\s*\[doi\]$", "", val)
    val = val.strip(" .,;)")
    return val if val.startswith("10.") and "/" in val else ""


def normalize_title_key(title: Any) -> str:
    if not title:
        return ""
    cleaned = re.sub(r"[^a-z0-9]+", " ", str(title).lower()).strip()
    return re.sub(r"\s+", " ", cleaned)


def _first_author_surname(authors: list[str] | str | None) -> str:
    if not authors:
        return ""
    first = authors[0] if isinstance(authors, list) else str(authors).split(";")[0]
    first = str(first).strip().lower()
    if "," in first:
        surname = first.split(",", 1)[0].strip()
    else:
        parts = first.split()
        surname = parts[0] if parts else ""
    return re.sub(r"[^a-z0-9]", "", surname)


def prepare_search_workspace(project_dir: Path) -> dict[str, Any]:
    """Compile query strings for all configured providers and create manual drop-folders with PT/EN guides."""
    root = Path(project_dir).resolve()
    plan_report = build_retrieval_plan(root)
    if plan_report.get("status") != "pass":
        return plan_report

    compiled_queries: list[dict[str, Any]] = plan_report.get("compiled_queries", [])
    drop_folders: dict[str, str] = {}
    for item in compiled_queries:
        prov = str(item.get("provider"))
        folder = root / "sources" / "manual_imports" / prov
        folder.mkdir(parents=True, exist_ok=True)
        drop_folders[prov] = folder.relative_to(root).as_posix()

    scopus_key_present = bool(_get_env_secret("SCOPUS_API_KEY", root))
    ncbi_key_present = bool(_get_env_secret("NCBI_API_KEY", root))

    scopus_pt = "Configurada" if scopus_key_present else "Ausente (usar pasta de importação manual)"
    ncbi_pt = "Configurada (10 req/s)" if ncbi_key_present else "Pública padrão (3 req/s)"
    scopus_en = "Configured" if scopus_key_present else "Absent (use manual drop-folder)"
    ncbi_en = "Configured (10 req/s)" if ncbi_key_present else "Public default (3 req/s)"

    pt_lines = [
        "# Guia de Strings de Busca e Pastas de Coleta (PRISMA-S / PRISMA 2020)\n",
        f"- **Projeto:** `{root.name}`",
        f"- **Scopus API Key (`SCOPUS_API_KEY`):** `{scopus_pt}`",
        f"- **NCBI/PubMed API Key (`NCBI_API_KEY`):** `{ncbi_pt}`\n",
        "## Strings Compiladas e Pastas de Exportação por Base\n",
    ]
    en_lines = [
        "# Search Strings & Drop-Folder Collection Guide (PRISMA-S / PRISMA 2020)\n",
        f"- **Project:** `{root.name}`",
        f"- **Scopus API Key (`SCOPUS_API_KEY`):** `{scopus_en}`",
        f"- **NCBI/PubMed API Key (`NCBI_API_KEY`):** `{ncbi_en}`\n",
        "## Compiled Search Strings and Export Folders by Database\n",
    ]

    for item in compiled_queries:
        prov = str(item["provider"])
        q_str = str(item["query"])
        q_hash = str(item["query_hash"])
        rel_drop = drop_folders[prov]
        abs_drop = (root / rel_drop).as_posix()

        pt_lines.extend(
            [
                f"### Base: `{prov}`",
                f"- **Hash da Query (`query_hash`):** `{q_hash}`",
                f"- **Pasta para soltar arquivos exportados (`.ris`, `.nbib`, `.csv`, `.json`):** `{abs_drop}`",
                "- **String de busca exata (copiar e colar):**",
                f"```text\n{q_str}\n```\n",
            ]
        )
        en_lines.extend(
            [
                f"### Database: `{prov}`",
                f"- **Query Hash (`query_hash`):** `{q_hash}`",
                f"- **Drop-folder for exported files (`.ris`, `.nbib`, `.csv`, `.json`):** `{abs_drop}`",
                "- **Exact search string (copy and paste):**",
                f"```text\n{q_str}\n```\n",
            ]
        )

    pt_guide = root / "context" / "retrieval" / "portugues" / "guia_strings_e_pastas_de_coleta.md"
    en_guide = root / "context" / "retrieval" / "ingles" / "guia_strings_e_pastas_de_coleta.md"
    pt_guide.parent.mkdir(parents=True, exist_ok=True)
    en_guide.parent.mkdir(parents=True, exist_ok=True)
    pt_guide.write_text("\n".join(pt_lines), encoding="utf-8")
    en_guide.write_text("\n".join(en_lines), encoding="utf-8")

    return {
        "contract": "SearchWorkspacePreparationV1",
        "status": "pass",
        "providers": [item["provider"] for item in compiled_queries],
        "drop_folders": drop_folders,
        "scopus_api_configured": scopus_key_present,
        "guides": {
            "portugues": pt_guide.relative_to(root).as_posix(),
            "ingles": en_guide.relative_to(root).as_posix(),
        },
        "compiled_queries": compiled_queries,
    }


def parse_ris_text(text: str, provider: str) -> list[dict[str, Any]]:
    """Parse RIS bibliographic records preserving all raw tags."""
    records: list[dict[str, Any]] = []
    current_tags: dict[str, list[str]] = {}
    last_tag: str | None = None

    def _finalize(tags: dict[str, list[str]]) -> dict[str, Any] | None:
        if not tags:
            return None
        title = (tags.get("TI") or tags.get("T1") or tags.get("ST") or [""])[0]
        abstract = " ".join(tags.get("AB") or tags.get("N2") or [])
        authors = tags.get("AU") or tags.get("A1") or []
        raw_year = (tags.get("PY") or tags.get("Y1") or tags.get("DA") or [""])[0]
        year_match = re.search(r"\b(19\d{2}|20\d{2})\b", str(raw_year))
        year = year_match.group(1) if year_match else ""
        journal = (tags.get("JO") or tags.get("JF") or tags.get("T2") or tags.get("JA") or [""])[0]
        raw_doi = (tags.get("DO") or tags.get("DI") or [""])[0]
        if not raw_doi:
            for note in tags.get("N1", []) + tags.get("UR", []) + tags.get("L3", []):
                m = re.search(r"(10\.\d{4,9}/[^\s;]+)", note)
                if m:
                    raw_doi = m.group(1)
                    break
        doi = normalize_doi(raw_doi)
        accession = (tags.get("AN") or tags.get("ID") or tags.get("C1") or [""])[0].strip()
        pmid = ""
        embase_id = ""
        scopus_eid = ""
        if re.fullmatch(r"\d{5,10}", accession) and provider in {"pubmed", "medline"}:
            pmid = accession
        elif accession.startswith("2-s2.0-"):
            scopus_eid = accession
        elif provider == "embase" and accession:
            embase_id = accession

        keywords = tags.get("KW") or []
        return {
            "source_database": provider,
            "title": title.strip(),
            "abstract": abstract.strip(),
            "authors": [a.strip() for a in authors if a.strip()],
            "year": year,
            "journal": journal.strip(),
            "doi": doi,
            "pmid": pmid,
            "embase_id": embase_id,
            "scopus_eid": scopus_eid,
            "accession_number": accession,
            "keywords": [k.strip() for k in keywords if k.strip()],
            "publication_type": (tags.get("TY") or [""])[0].strip(),
            "volume": (tags.get("VL") or [""])[0].strip(),
            "issue": (tags.get("IS") or [""])[0].strip(),
            "pages": "-".join(
                p for p in [(tags.get("SP") or [""])[0].strip(), (tags.get("EP") or [""])[0].strip()] if p
            ),
            "raw_fields": tags,
        }

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\r\n")
        if not line.strip():
            continue
        m = re.match(r"^([A-Z0-9]{2})\s{2}-\s?(.*)$", line)
        if m:
            tag, val = m.group(1), m.group(2).strip()
            if tag == "ER":
                rec = _finalize(current_tags)
                if rec and (rec["title"] or rec["doi"] or rec["accession_number"]):
                    records.append(rec)
                current_tags = {}
                last_tag = None
            else:
                current_tags.setdefault(tag, []).append(val)
                last_tag = tag
        elif last_tag and line.startswith("  "):
            current_tags[last_tag][-1] += " " + line.strip()

    if current_tags:
        rec = _finalize(current_tags)
        if rec and (rec["title"] or rec["doi"] or rec["accession_number"]):
            records.append(rec)
    return records


def parse_nbib_text(text: str, provider: str = "pubmed") -> list[dict[str, Any]]:
    """Parse PubMed/MEDLINE (.nbib / .txt) records preserving all raw tags."""
    records: list[dict[str, Any]] = []
    current_tags: dict[str, list[str]] = {}
    last_tag: str | None = None

    def _finalize(tags: dict[str, list[str]]) -> dict[str, Any] | None:
        if not tags:
            return None
        pmid = (tags.get("PMID") or [""])[0].strip()
        title = " ".join(tags.get("TI") or tags.get("BTI") or []).strip()
        abstract = " ".join(tags.get("AB") or []).strip()
        authors = tags.get("FAU") or tags.get("AU") or []
        dp = (tags.get("DP") or [""])[0]
        year_match = re.search(r"\b(19\d{2}|20\d{2})\b", dp)
        year = year_match.group(1) if year_match else ""
        journal = (tags.get("JT") or tags.get("TA") or [""])[0].strip()
        doi = ""
        for id_str in tags.get("LID", []) + tags.get("AID", []):
            if "[doi]" in id_str.lower() or id_str.strip().startswith("10."):
                doi = normalize_doi(id_str)
                if doi:
                    break
        mesh = tags.get("MH") or tags.get("OT") or []
        return {
            "source_database": provider,
            "title": title,
            "abstract": abstract,
            "authors": [a.strip() for a in authors if a.strip()],
            "year": year,
            "journal": journal,
            "doi": doi,
            "pmid": pmid,
            "embase_id": "",
            "scopus_eid": "",
            "accession_number": pmid,
            "keywords": [m.strip() for m in mesh if m.strip()],
            "publication_type": "; ".join(tags.get("PT") or []),
            "volume": (tags.get("VI") or [""])[0].strip(),
            "issue": (tags.get("IP") or [""])[0].strip(),
            "pages": (tags.get("PG") or [""])[0].strip(),
            "raw_fields": tags,
        }

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\r\n")
        if not line.strip():
            rec = _finalize(current_tags)
            if rec and (rec["title"] or rec["pmid"] or rec["doi"]):
                records.append(rec)
            current_tags = {}
            last_tag = None
            continue
        m = re.match(r"^([A-Z]{2,4})\s*-\s(.*)$", line)
        if m:
            tag, val = m.group(1).strip(), m.group(2).strip()
            current_tags.setdefault(tag, []).append(val)
            last_tag = tag
        elif last_tag and line.startswith("      "):
            current_tags[last_tag][-1] += " " + line.strip()

    if current_tags:
        rec = _finalize(current_tags)
        if rec and (rec["title"] or rec["pmid"] or rec["doi"]):
            records.append(rec)
    return records


def parse_bibliographic_file(file_path: Path, provider: str) -> list[dict[str, Any]]:
    """Universal zero-loss parser for .ris, .nbib, .csv, .json, and .jsonl files."""
    path = Path(file_path).resolve()
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8-sig", errors="replace")

    if suffix == ".ris":
        return parse_ris_text(text, provider)
    if suffix in {".nbib", ".medline"} or (suffix == ".txt" and "PMID-" in text[:500]):
        return parse_nbib_text(text, provider)
    if suffix == ".json":
        payload = json.loads(text)
        raw_list = payload.get("records", payload) if isinstance(payload, dict) else payload
        if not isinstance(raw_list, list):
            return []
        return [_normalize_dict_record(dict(item), provider) for item in raw_list]
    if suffix == ".jsonl":
        return [_normalize_dict_record(json.loads(line), provider) for line in text.splitlines() if line.strip()]
    if suffix in {".csv", ".tsv"}:
        delim = "\t" if suffix == ".tsv" else ","
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [_normalize_dict_record(dict(row), provider) for row in csv.DictReader(handle, delimiter=delim)]
    return []


def _normalize_dict_record(row: dict[str, Any], provider: str) -> dict[str, Any]:
    lower_map = {str(k).strip().lower(): v for k, v in row.items()}
    title = str(
        lower_map.get("title")
        or lower_map.get("article title")
        or lower_map.get("document title")
        or lower_map.get("titulo")
        or ""
    ).strip()
    abstract = str(lower_map.get("abstract") or lower_map.get("resumo") or "").strip()
    raw_authors = lower_map.get("authors") or lower_map.get("author") or []
    if isinstance(raw_authors, str):
        authors = [a.strip() for a in re.split(r";|\band\b", raw_authors) if a.strip()]
    elif isinstance(raw_authors, list):
        authors = [str(a).strip() for a in raw_authors if str(a).strip()]
    else:
        authors = []
    year_raw = str(lower_map.get("year") or lower_map.get("pubyear") or lower_map.get("publication year") or "")
    ym = re.search(r"\b(19\d{2}|20\d{2})\b", year_raw)
    year = ym.group(1) if ym else ""
    journal = str(lower_map.get("journal") or lower_map.get("source title") or "").strip()
    doi = normalize_doi(lower_map.get("doi"))
    pmid = str(lower_map.get("pmid") or lower_map.get("pubmed id") or "").strip()
    embase_id = str(lower_map.get("embase_id") or lower_map.get("pui") or "").strip()
    scopus_eid = str(lower_map.get("scopus_eid") or lower_map.get("eid") or "").strip()
    accession = str(lower_map.get("accession_number") or pmid or embase_id or scopus_eid or "").strip()
    kw_raw = lower_map.get("keywords") or lower_map.get("author keywords") or lower_map.get("index keywords") or []
    if isinstance(kw_raw, str):
        keywords = [k.strip() for k in kw_raw.split(";") if k.strip()]
    elif isinstance(kw_raw, list):
        keywords = [str(k).strip() for k in kw_raw if str(k).strip()]
    else:
        keywords = []

    return {
        "source_database": str(row.get("source_database") or provider),
        "title": title,
        "abstract": abstract,
        "authors": authors,
        "year": year,
        "journal": journal,
        "doi": doi,
        "pmid": pmid,
        "embase_id": embase_id,
        "scopus_eid": scopus_eid,
        "accession_number": accession,
        "keywords": keywords,
        "publication_type": str(lower_map.get("publication_type") or lower_map.get("document type") or ""),
        "volume": str(lower_map.get("volume") or ""),
        "issue": str(lower_map.get("issue") or ""),
        "pages": str(lower_map.get("pages") or ""),
        "raw_fields": row.get("raw_fields") if isinstance(row.get("raw_fields"), dict) else row,
    }


def execute_pubmed_api_search(project_dir: Path, max_records: int = 200, timeout: float = 15.0) -> dict[str, Any]:
    """Execute compiled PubMed query via NCBI E-utilities and write records + manifest."""
    root = Path(project_dir).resolve()
    gate = registration_gate(root, "corpus-build", mark_started=True)
    if gate["status"] != "pass":
        return gate

    compiled_report = compile_query_plan(root)
    if compiled_report.get("status") != "pass":
        return compiled_report

    pubmed_q = next(
        (item for item in compiled_report.get("compiled_queries", []) if item.get("provider") == "pubmed"),
        None,
    )
    if not pubmed_q:
        return {"status": "blocked", "issues": ["No compiled PubMed query found in query_plan.yaml."]}

    query_str = str(pubmed_q["query"])
    query_hash = str(pubmed_q["query_hash"])
    api_key = _get_env_secret("NCBI_API_KEY", root)

    params: dict[str, Any] = {
        "db": "pubmed",
        "term": query_str,
        "retmode": "json",
        "retmax": max_records,
    }
    if api_key:
        params["api_key"] = api_key

    esearch_url = f"{NCBI_EUTILS_BASE}/esearch.fcgi?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(esearch_url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            esearch_data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
        return {"status": "blocked", "issues": [f"PubMed ESearch failed: {exc}"]}

    esearch_res = esearch_data.get("esearchresult", {})
    id_list: list[str] = esearch_res.get("idlist", [])
    total_hits = int(esearch_res.get("count") or len(id_list))

    records: list[dict[str, Any]] = []
    chunk_size = 150
    for chunk_start in range(0, len(id_list), chunk_size):
        chunk_ids = id_list[chunk_start : chunk_start + chunk_size]
        efetch_params: dict[str, Any] = {
            "db": "pubmed",
            "id": ",".join(chunk_ids),
            "rettype": "medline",
            "retmode": "text",
        }
        if api_key:
            efetch_params["api_key"] = api_key
        efetch_url = f"{NCBI_EUTILS_BASE}/efetch.fcgi?{urllib.parse.urlencode(efetch_params)}"
        efetch_req = urllib.request.Request(efetch_url, headers={"User-Agent": USER_AGENT})
        chunk_records: list[dict[str, Any]] = []
        try:
            with urllib.request.urlopen(efetch_req, timeout=timeout) as resp:
                medline_text = resp.read().decode("utf-8", errors="replace")
            chunk_records = parse_nbib_text(medline_text, provider="pubmed")
        except (urllib.error.URLError, OSError):
            chunk_records = []

        if not chunk_records:
            sum_params: dict[str, Any] = {
                "db": "pubmed",
                "id": ",".join(chunk_ids),
                "retmode": "json",
            }
            if api_key:
                sum_params["api_key"] = api_key
            esum_url = f"{NCBI_EUTILS_BASE}/esummary.fcgi?{urllib.parse.urlencode(sum_params)}"
            sum_req = urllib.request.Request(esum_url, headers={"User-Agent": USER_AGENT})
            try:
                with urllib.request.urlopen(sum_req, timeout=timeout) as resp:
                    esum_data = json.loads(resp.read().decode("utf-8")).get("result", {})
                for pmid in chunk_ids:
                    item = esum_data.get(pmid)
                    if not isinstance(item, dict):
                        continue
                    doi = ""
                    for aid in item.get("articleids", []):
                        if isinstance(aid, dict) and aid.get("idtype") == "doi":
                            doi = normalize_doi(aid.get("value"))
                            break
                    pubdate = str(item.get("pubdate") or "")
                    ym = re.search(r"\b(19\d{2}|20\d{2})\b", pubdate)
                    chunk_records.append(
                        {
                            "source_database": "pubmed",
                            "title": str(item.get("title") or "").strip(),
                            "abstract": "",
                            "authors": [a.get("name", "") for a in item.get("authors", []) if isinstance(a, dict)],
                            "year": ym.group(1) if ym else "",
                            "journal": str(item.get("fulljournalname") or item.get("source") or "").strip(),
                            "doi": doi,
                            "pmid": str(pmid),
                            "embase_id": "",
                            "scopus_eid": "",
                            "accession_number": str(pmid),
                            "keywords": [],
                            "publication_type": "; ".join(item.get("pubtype", [])),
                            "volume": str(item.get("volume") or ""),
                            "issue": str(item.get("issue") or ""),
                            "pages": str(item.get("pages") or ""),
                            "raw_fields": item,
                        }
                    )
            except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
                return {"status": "blocked", "issues": [f"PubMed ESummary failed: {exc}"]}
        records.extend(chunk_records)

    drop_dir = root / "sources" / "manual_imports" / "pubmed"
    drop_dir.mkdir(parents=True, exist_ok=True)
    out_file = drop_dir / "pubmed_api_retrieved.json"
    out_file.write_text(json.dumps({"records": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "status": "pass",
        "provider": "pubmed",
        "query_hash": query_hash,
        "total_database_hits": total_hits,
        "retrieved_count": len(records),
        "saved_to": out_file.relative_to(root).as_posix(),
    }


def verify_scopus_connection(project_dir: Path | None = None, timeout: float = 15.0) -> dict[str, Any]:
    """Verify Elsevier Scopus API key connectivity using a lightweight test query."""
    root = Path(project_dir).resolve() if project_dir else Path.cwd().resolve()
    api_key = _get_env_secret("SCOPUS_API_KEY", root) or _get_env_secret("ELSEVIER_API_KEY", root)
    if not api_key:
        return {"status": "blocked", "authenticated": False, "issues": ["Missing SCOPUS_API_KEY in .env."]}

    params = {"query": "TITLE(mesenteric ischemia)", "count": 1, "httpAccept": "application/json"}
    url = f"https://api.elsevier.com/content/search/scopus?{urllib.parse.urlencode(params)}"
    headers = {"X-ELS-APIKey": api_key, "Accept": "application/json", "User-Agent": USER_AGENT}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        sr = data.get("search-results", {})
        total = int(sr.get("opensearch:totalResults") or 0)
        return {
            "status": "pass",
            "authenticated": True,
            "provider": "scopus",
            "sample_query": "TITLE(mesenteric ischemia)",
            "total_results_available": total,
        }
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
        return {"status": "blocked", "authenticated": False, "issues": [f"Scopus API check failed: {exc}"]}


def execute_scopus_api_search(project_dir: Path, max_records: int = 200, timeout: float = 15.0) -> dict[str, Any]:
    """Execute compiled Scopus query via Elsevier Scopus Search API using SCOPUS_API_KEY from .env."""
    root = Path(project_dir).resolve()
    gate = registration_gate(root, "corpus-build", mark_started=True)
    if gate["status"] != "pass":
        return gate

    api_key = _get_env_secret("SCOPUS_API_KEY", root) or _get_env_secret("ELSEVIER_API_KEY", root)
    if not api_key:
        return {
            "status": "blocked",
            "issues": ["Missing SCOPUS_API_KEY in .env or environment. Add SCOPUS_API_KEY=<key> to .env."],
        }

    compiled_report = compile_query_plan(root)
    if compiled_report.get("status") != "pass":
        return compiled_report

    scopus_q = next(
        (item for item in compiled_report.get("compiled_queries", []) if item.get("provider") == "scopus"),
        None,
    )
    if not scopus_q:
        return {"status": "blocked", "issues": ["No compiled Scopus query found in query_plan.yaml."]}

    query_str = str(scopus_q["query"])
    query_hash = str(scopus_q["query_hash"])
    page_size = 25
    headers = {"X-ELS-APIKey": api_key, "Accept": "application/json", "User-Agent": USER_AGENT}
    inst_token = _get_env_secret("SCOPUS_INST_TOKEN", root)
    if inst_token:
        headers["X-ELS-Insttoken"] = inst_token

    start = 0
    records: list[dict[str, Any]] = []
    total_hits = 0

    while len(records) < max_records:
        fetch_count = min(page_size, max_records - len(records))
        params = {"query": query_str, "count": fetch_count, "start": start, "httpAccept": "application/json"}
        url = f"https://api.elsevier.com/content/search/scopus?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
            if not records:
                return {"status": "blocked", "issues": [f"Scopus API search failed: {exc}"]}
            break

        sr = data.get("search-results", {})
        if not total_hits:
            total_hits = int(sr.get("opensearch:totalResults") or 0)
        entries = sr.get("entry", [])
        if not entries:
            break

        for entry in entries:
            if not isinstance(entry, dict) or entry.get("error"):
                continue
            title = str(entry.get("dc:title") or "").strip()
            creator = str(entry.get("dc:creator") or "").strip()
            cover_date = str(entry.get("prism:coverDate") or "")
            ym = re.search(r"\b(19\d{2}|20\d{2})\b", cover_date)
            eid = str(entry.get("eid") or "").strip()
            pmid = str(entry.get("pubmed-id") or "").strip()
            doi = normalize_doi(entry.get("prism:doi"))
            records.append(
                {
                    "source_database": "scopus",
                    "title": title,
                    "abstract": str(entry.get("dc:description") or "").strip(),
                    "authors": [creator] if creator else [],
                    "year": ym.group(1) if ym else "",
                    "journal": str(entry.get("prism:publicationName") or "").strip(),
                    "doi": doi,
                    "pmid": pmid,
                    "embase_id": "",
                    "scopus_eid": eid,
                    "accession_number": eid or pmid,
                    "keywords": [],
                    "publication_type": str(entry.get("prism:aggregationType") or ""),
                    "volume": str(entry.get("prism:volume") or ""),
                    "issue": str(entry.get("prism:issueIdentifier") or ""),
                    "pages": str(entry.get("prism:pageRange") or ""),
                    "raw_fields": entry,
                }
            )

        start += len(entries)
        if start >= total_hits or len(entries) < fetch_count:
            break
        import time
        time.sleep(0.05)

    drop_dir = root / "sources" / "manual_imports" / "scopus"
    drop_dir.mkdir(parents=True, exist_ok=True)
    out_file = drop_dir / "scopus_api_retrieved.json"
    out_file.write_text(json.dumps({"records": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "status": "pass",
        "provider": "scopus",
        "query_hash": query_hash,
        "total_database_hits": total_hits,
        "retrieved_count": len(records),
        "saved_to": out_file.relative_to(root).as_posix(),
    }


def ingest_drop_folders_and_deduplicate(project_dir: Path) -> dict[str, Any]:
    """Ingest all database files from sources/manual_imports/*, write retrieval manifests, and deduplicate."""
    root = Path(project_dir).resolve()
    gate = registration_gate(root, "corpus-build", mark_started=True)
    if gate["status"] != "pass":
        return gate

    compiled_report = load_structured_file(root / COMPILED_QUERY_PATH)
    if not compiled_report or compiled_report.get("status") != "pass":
        compiled_report = compile_query_plan(root)
        if compiled_report.get("status") != "pass":
            return compiled_report

    query_hashes: dict[str, str] = {
        str(item["provider"]): str(item["query_hash"])
        for item in compiled_report.get("compiled_queries", [])
        if isinstance(item, dict) and item.get("provider") and item.get("query_hash")
    }

    manual_root = root / "sources" / "manual_imports"
    all_raw_records: list[dict[str, Any]] = []
    counts_by_db: dict[str, int] = {}
    manifests_written: list[str] = []

    if manual_root.is_dir():
        for prov_dir in sorted(p for p in manual_root.iterdir() if p.is_dir()):
            prov = prov_dir.name.lower()
            prov_records: list[dict[str, Any]] = []
            for file_path in sorted(p for p in prov_dir.iterdir() if p.is_file()):
                if file_path.suffix.lower() not in {
                    ".ris",
                    ".nbib",
                    ".medline",
                    ".txt",
                    ".csv",
                    ".tsv",
                    ".json",
                    ".jsonl",
                }:
                    continue
                register_source(root, str(file_path), "file")
                parsed = parse_bibliographic_file(file_path, prov)
                prov_records.extend(parsed)

            if prov_records or prov in query_hashes:
                counts_by_db[prov] = len(prov_records)
                all_raw_records.extend(prov_records)

                # Write canonical provider records & retrieval manifest for audit_retrieval
                prov_dump_dir = root / "sources" / "parsed_by_provider"
                prov_dump_dir.mkdir(parents=True, exist_ok=True)
                prov_dump_path = prov_dump_dir / f"{prov}_records.json"
                prov_dump_bytes = (
                    json.dumps(prov_records, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
                ).encode("utf-8")
                prov_dump_path.write_bytes(prov_dump_bytes)
                records_sha256 = hashlib.sha256(prov_dump_bytes).hexdigest()

                if prov in query_hashes:
                    manifest_dir = root / "evidence" / "retrieval"
                    manifest_dir.mkdir(parents=True, exist_ok=True)
                    manifest_path = manifest_dir / f"{prov}_manifest.json"
                    manifest_payload = {
                        "contract": "RetrievalManifest",
                        "provider": prov,
                        "query_hash": query_hashes[prov],
                        "retrieved_at": datetime.now(UTC).isoformat(),
                        "record_count": len(prov_records),
                        "records_sha256": records_sha256,
                        "records_path": prov_dump_path.relative_to(root).as_posix(),
                    }
                    save_structured_file(manifest_path, manifest_payload)
                    manifests_written.append(manifest_path.relative_to(root).as_posix())

    # 3-Stage Deterministic Zero-Loss Deduplication
    unique_records: list[dict[str, Any]] = []
    doi_index: dict[str, int] = {}
    ext_id_index: dict[str, int] = {}
    title_year_author_index: dict[str, int] = {}

    dedup_log: list[dict[str, Any]] = []
    stage_counts = {"doi_exact": 0, "identifier_exact": 0, "title_year_author": 0}

    for raw_idx, rec in enumerate(all_raw_records, start=1):
        doi = normalize_doi(rec.get("doi"))
        pmid = str(rec.get("pmid") or "").strip()
        embase_id = str(rec.get("embase_id") or "").strip()
        scopus_eid = str(rec.get("scopus_eid") or "").strip()
        norm_title = normalize_title_key(rec.get("title"))
        year = str(rec.get("year") or "").strip()
        surname = _first_author_surname(rec.get("authors"))

        ext_keys = []
        if pmid:
            ext_keys.append(f"pmid:{pmid}")
        if embase_id:
            ext_keys.append(f"embase:{embase_id}")
        if scopus_eid:
            ext_keys.append(f"scopus:{scopus_eid}")

        tya_key = f"{norm_title}|{year}|{surname}" if len(norm_title) >= 12 and year else ""

        match_idx: int | None = None
        match_stage = ""

        if doi and doi in doi_index:
            match_idx = doi_index[doi]
            match_stage = "doi_exact"
        else:
            for ek in ext_keys:
                if ek in ext_id_index:
                    match_idx = ext_id_index[ek]
                    match_stage = "identifier_exact"
                    break
            if match_idx is None and tya_key and tya_key in title_year_author_index:
                match_idx = title_year_author_index[tya_key]
                match_stage = "title_year_author"

        if match_idx is not None:
            stage_counts[match_stage] += 1
            master = unique_records[match_idx]
            db_name = str(rec.get("source_database") or "unknown")
            if db_name not in master["sources_databases"]:
                master["sources_databases"].append(db_name)
            # Zero-loss field enrichment
            if len(str(rec.get("abstract") or "")) > len(str(master.get("abstract") or "")):
                master["abstract"] = rec["abstract"]
            for id_field in ("doi", "pmid", "embase_id", "scopus_eid", "year", "journal", "volume", "issue", "pages"):
                if not master.get(id_field) and rec.get(id_field):
                    master[id_field] = rec[id_field]
            existing_kw = {k.lower() for k in master.get("keywords", [])}
            for kw in rec.get("keywords", []):
                if kw.lower() not in existing_kw:
                    master.setdefault("keywords", []).append(kw)
                    existing_kw.add(kw.lower())
            master["merged_raw_records"].append(
                {
                    "source_database": db_name,
                    "accession_number": rec.get("accession_number", ""),
                    "matched_by": match_stage,
                }
            )
            dedup_log.append(
                {
                    "duplicate_index": raw_idx,
                    "master_record_id": master["record_id"],
                    "matched_by": match_stage,
                    "duplicate_database": db_name,
                    "title": rec.get("title", ""),
                    "doi": doi,
                }
            )
        else:
            new_idx = len(unique_records)
            record_id = f"STUDY-{new_idx + 1:04d}"
            db_name = str(rec.get("source_database") or "unknown")
            enriched = dict(rec)
            enriched["record_id"] = record_id
            enriched["sources_databases"] = [db_name]
            enriched["merged_raw_records"] = []
            unique_records.append(enriched)

            if doi:
                doi_index[doi] = new_idx
            for ek in ext_keys:
                ext_id_index[ek] = new_idx
            if tya_key:
                title_year_author_index[tya_key] = new_idx

    total_identified = len(all_raw_records)
    total_duplicates = sum(stage_counts.values())
    total_unique = len(unique_records)

    retrieval_ev_dir = root / "evidence" / "retrieval"
    retrieval_ev_dir.mkdir(parents=True, exist_ok=True)

    # Save deduplication log
    dedup_log_path = retrieval_ev_dir / "deduplication_log.jsonl"
    dedup_log_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in dedup_log),
        encoding="utf-8",
    )

    # Save screening queue
    screening_dir = root / "screening"
    screening_dir.mkdir(parents=True, exist_ok=True)
    queue_path = screening_dir / "title_abstract_queue.jsonl"
    queue_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in unique_records),
        encoding="utf-8",
    )

    prisma_counts = {
        "contract": "PRISMAFlowCountsV1",
        "generated_at": datetime.now(UTC).isoformat(),
        "identification": {
            "records_identified_per_database": counts_by_db,
            "total_records_identified": total_identified,
            "duplicates_removed_by_stage": stage_counts,
            "total_duplicates_removed": total_duplicates,
        },
        "screening": {
            "records_screened": total_unique,
            "screening_queue_path": queue_path.relative_to(root).as_posix(),
        },
        "manifests_written": manifests_written,
        "deduplication_log_path": dedup_log_path.relative_to(root).as_posix(),
    }
    prisma_ev_dir = root / "evidence" / "prisma"
    prisma_ev_dir.mkdir(parents=True, exist_ok=True)
    prisma_counts_path = prisma_ev_dir / "prisma_flow_counts.json"
    save_structured_file(prisma_counts_path, prisma_counts)

    # Paired PT-BR and EN PRISMA-S reports
    pt_rep_dir = retrieval_ev_dir / "portugues"
    en_rep_dir = retrieval_ev_dir / "ingles"
    pt_rep_dir.mkdir(parents=True, exist_ok=True)
    en_rep_dir.mkdir(parents=True, exist_ok=True)

    db_lines_pt = (
        "\n".join(f"- **{db}:** {cnt} registros" for db, cnt in sorted(counts_by_db.items()))
        or "- Nenhum arquivo importado ainda"
    )
    db_lines_en = (
        "\n".join(f"- **{db}:** {cnt} records" for db, cnt in sorted(counts_by_db.items())) or "- No files imported yet"
    )

    pt_md = (
        f"# Relatório de Coleta e Deduplicação PRISMA 2020 / PRISMA-S\n\n"
        f"## 1. Registros Identificados por Base\n{db_lines_pt}\n"
        f"- **Total bruto identificado:** {total_identified}\n\n"
        f"## 2. Deduplicação Determinística (Zero Perda de Metadados)\n"
        f"- **Estágio 1 (DOI exato normalizado):** {stage_counts['doi_exact']}\n"
        f"- **Estágio 2 (PMID / Embase PUI / Scopus EID):** {stage_counts['identifier_exact']}\n"
        f"- **Estágio 3 (Título normalizado + Ano + Sobrenome 1º Autor):** {stage_counts['title_year_author']}\n"
        f"- **Total de duplicatas removidas:** {total_duplicates}\n\n"
        f"## 3. Fila de Triagem (Título e Resumo)\n"
        f"- **Registros únicos para triagem (`records_screened`):** {total_unique}\n"
        f"- **Arquivo da fila:** `{queue_path.relative_to(root).as_posix()}`\n"
    )
    en_md = (
        f"# PRISMA 2020 / PRISMA-S Search Collection & Deduplication Report\n\n"
        f"## 1. Records Identified per Database\n{db_lines_en}\n"
        f"- **Total raw records identified:** {total_identified}\n\n"
        f"## 2. Deterministic Deduplication (Zero Metadata Loss)\n"
        f"- **Stage 1 (Exact normalized DOI):** {stage_counts['doi_exact']}\n"
        f"- **Stage 2 (PMID / Embase PUI / Scopus EID):** {stage_counts['identifier_exact']}\n"
        f"- **Stage 3 (Normalized Title + Year + First Author Surname):** {stage_counts['title_year_author']}\n"
        f"- **Total duplicates removed:** {total_duplicates}\n\n"
        f"## 3. Screening Queue (Title & Abstract)\n"
        f"- **Unique records for screening (`records_screened`):** {total_unique}\n"
        f"- **Queue file:** `{queue_path.relative_to(root).as_posix()}`\n"
    )

    (pt_rep_dir / "relatorio_busca_prisma.md").write_text(pt_md, encoding="utf-8")
    (en_rep_dir / "relatorio_busca_prisma.md").write_text(en_md, encoding="utf-8")

    return {
        "contract": "CorpusDeduplicationReportV1",
        "status": "pass",
        "counts_by_database": counts_by_db,
        "total_identified": total_identified,
        "duplicates_removed_by_stage": stage_counts,
        "total_duplicates_removed": total_duplicates,
        "unique_records_for_screening": total_unique,
        "prisma_flow_counts_path": prisma_counts_path.relative_to(root).as_posix(),
        "screening_queue_path": queue_path.relative_to(root).as_posix(),
        "deduplication_log_path": dedup_log_path.relative_to(root).as_posix(),
        "manifests_written": manifests_written,
    }
