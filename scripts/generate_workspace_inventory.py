"""Generate a non-destructive worktree and legacy-area inventory.

The inventory reads paths and filesystem metadata only. It deliberately does
not open scientific, clinical, PDF, or source files.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
from typing import Any


SENSITIVE_ROOTS = (
    ".env",
    "Correção Orientador",
    "Doutorado",
    "Leitor de Artigos",
    "NMA_OSA_VPI",
    "PDFS DR ANDRÉ",
    "REVISÃO LIGA",
    "Revisões Sistemáticas",
    "Submissão Final",
    "sources",
)

EXCLUDED_ROOTS = (
    ".git",
    ".venv",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".playwright-osf",
    "node_modules",
    "tmp",
)

KEEP_PREFIXES = (
    ".agents/",
    ".codex/",
    ".github/",
    "article_machine/",
    "docs/",
    "scripts/",
    "skills/",
    "tests/",
    "tools/playwright/",
    "projects/article-machine-governance-2026/",
)

KEEP_FILES = {
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "AGENT_MANIFEST.md",
    "README.md",
    "SKILL_INDEX.md",
    "SKILLS_CANON.md",
    "pyproject.toml",
    "uv.lock",
}


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout.strip()


def _classify(path: str) -> tuple[str, str]:
    normalized = path.replace("\\", "/")
    lowered = normalized.casefold()
    if normalized == ".env" or normalized.startswith(".env."):
        return "sensitive", "secret-bearing environment file"
    if lowered.endswith(".pdf") or any(token in lowered for token in ("patient", "paciente", "fulltext", "raw/")):
        return "sensitive", "scientific or clinical source material"
    if any(normalized == root or normalized.startswith(f"{root}/") for root in SENSITIVE_ROOTS):
        return "sensitive", "protected legacy, source, or clinical area"
    if any(normalized == root or normalized.startswith(f"{root}/") for root in EXCLUDED_ROOTS):
        return "exclude", "local runtime, cache, or transient output"
    if normalized.startswith("graphify-out/"):
        return "review", "generated graph must be regenerated from a clean candidate commit"
    if normalized in KEEP_FILES or normalized.startswith(KEEP_PREFIXES):
        return "keep", "code, policy, test, lock, or curated operational artifact"
    return "review", "ambiguous root artifact requires explicit human review"


def _worktree_entries(root: Path) -> list[dict[str, str]]:
    raw = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout
    records: list[dict[str, str]] = []
    fields = raw.decode("utf-8", errors="replace").split("\0")
    index = 0
    while index < len(fields):
        item = fields[index]
        index += 1
        if not item:
            continue
        status = item[:2]
        path = item[3:]
        if status[0] in {"R", "C"} and index < len(fields):
            previous_path = fields[index]
            index += 1
        else:
            previous_path = ""
        classification, rationale = _classify(path)
        record = {
            "path": path.replace("\\", "/"),
            "git_status": status,
            "classification": classification,
            "rationale": rationale,
        }
        if previous_path:
            record["previous_path"] = previous_path.replace("\\", "/")
        records.append(record)
    return sorted(records, key=lambda item: item["path"].casefold())


def _metadata_only(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    result: dict[str, Any] = {
        "path": relative,
        "classification": "sensitive" if relative in SENSITIVE_ROOTS else "exclude",
        "exists": path.exists(),
        "content_read": False,
        "move_authorized": False,
        "decision": "preserve-in-place",
    }
    if not path.exists():
        return result
    stat = path.stat()
    result["modified_at"] = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
    if path.is_file():
        result.update({"kind": "file", "file_count": 1, "size_bytes": stat.st_size})
        return result
    file_count = 0
    directory_count = 1
    total_size = 0
    for current, directories, files in os.walk(path, followlinks=False):
        directory_count += len(directories)
        file_count += len(files)
        for filename in files:
            try:
                total_size += (Path(current) / filename).stat().st_size
            except OSError:
                continue
    result.update(
        {
            "kind": "directory",
            "file_count": file_count,
            "directory_count": directory_count,
            "size_bytes": total_size,
            "related_project": "unresolved-manual-triage",
        }
    )
    return result


def build_inventory(root: Path) -> dict[str, Any]:
    entries = _worktree_entries(root)
    areas = [_metadata_only(root, name) for name in (*SENSITIVE_ROOTS, *EXCLUDED_ROOTS)]
    counts = {name: 0 for name in ("keep", "review", "exclude", "sensitive")}
    for entry in entries:
        counts[entry["classification"]] += 1
    return {
        "contract": "WorkspacePreservationManifestV1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(root.resolve()),
        "branch": _git(root, "branch", "--show-current"),
        "head": _git(root, "rev-parse", "HEAD"),
        "dirty": bool(entries),
        "staging_policy": {
            "git_add_dot_prohibited": True,
            "explicit_pathspec_required": True,
            "sensitive_files_must_remain_untracked": True,
        },
        "classification_counts": counts,
        "worktree_entries": entries,
        "protected_areas": areas,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.workspace_root).resolve()
    output = Path(args.output)
    if not output.is_absolute():
        output = root / output
    payload = build_inventory(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "written", "path": str(output), "counts": payload["classification_counts"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
