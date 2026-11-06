"""Render paired, editable DOCX templates using project-local Quarto."""
from pathlib import Path
import json
import subprocess
import zipfile

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
QUARTO = ROOT / "ferramentas/quarto-1.10.20/bin/quarto.cmd"


def main():
    if not QUARTO.is_file():
        print(json.dumps({"status": "SKIPPED", "reason": "project-local Quarto is absent"}))
        return 2
    results = []
    pt = {p.name for p in (BASE / "portugues").glob("*.md")}
    en = {p.name for p in (BASE / "ingles").glob("*.md")}
    if pt != en:
        raise ValueError("Template pairs are incomplete")
    for language, locale in (("portugues", "pt-BR"), ("ingles", "en")):
        for name in sorted(pt):
            source = BASE / language / name
            destination = BASE / "editaveis" / language / source.with_suffix(".docx").name
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                raise FileExistsError(f"Preserved existing render: {destination}")
            result = subprocess.run(
                [str(QUARTO), "pandoc", str(source), "--to", "docx", "--output", str(destination),
                 "--metadata", f"lang:{locale}"],
                cwd=BASE, capture_output=True, text=True, timeout=90,
            )
            valid = False
            if result.returncode == 0 and destination.is_file():
                with zipfile.ZipFile(destination) as archive:
                    valid = archive.testzip() is None and "word/document.xml" in archive.namelist()
            results.append({"file": str(destination.relative_to(BASE)), "exit_code": result.returncode,
                            "docx_structure_valid": valid, "status": "PASS" if valid else "FAIL",
                            "stderr": result.stderr[-1200:] if not valid else ""})
            if not valid:
                break
    report = {"renders": results, "human_layout_review": "SKIPPED", "clinical_content": "unfilled-template",
              "status": "PASS" if len(results) == 2 * len(pt) and all(r["status"] == "PASS" for r in results) else "FAIL"}
    (BASE / "registro_renderizacao.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "docx_files": len(results), "human_layout_review": "SKIPPED"}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
