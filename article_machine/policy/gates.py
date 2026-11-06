from __future__ import annotations

import hashlib
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

GATE_REPORT_PATH = Path("reviews") / "stage_gate_report_v2.json"
INPUT_PATHS = (
    "project.yaml",
    "protocol.yaml",
    "standards.yaml",
    "compute.yaml",
    "sources/registry.jsonl",
    "evidence/claim_map.jsonl",
    "analysis/manifest.json",
    "drafts/manuscript.md",
    "drafts/references.bib",
)

CONTROL_PLANE_PATTERNS = (
    "article_machine/**/*.py",
    "scripts/*.py",
    ".codex/*.toml",
    ".codex/agents/*.toml",
    "skills/registry.json",
    "skills/*/SKILL.md",
    "skills/*/scripts/*.py",
    "skills/*/references/*.md",
    "pyproject.toml",
    "uv.lock",
    "tools/playwright/package-lock.json",
)


def file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_value(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _control_plane_hash(root: Path) -> str:
    digest = hashlib.sha256()
    paths: set[Path] = set()
    for pattern in CONTROL_PLANE_PATTERNS:
        paths.update(path for path in root.glob(pattern) if path.is_file())
    for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def workspace_snapshot(project_dir: Path) -> dict[str, Any]:
    project_dir = Path(project_dir).resolve()
    root = next((parent for parent in (project_dir, *project_dir.parents) if (parent / ".git").exists()), project_dir)
    hashes = {rel: file_sha256(project_dir / rel) for rel in INPUT_PATHS}
    worktree = _git_value(root, "status", "--porcelain=v1")
    worktree_fingerprint = hashlib.sha256((worktree or "").encode("utf-8")).hexdigest()
    return {
        "commit": _git_value(root, "rev-parse", "HEAD"),
        "worktree": "clean" if worktree == "" else "dirty" if worktree is not None else "unknown",
        "worktree_fingerprint": f"sha256:{worktree_fingerprint}",
        "control_plane_hash": _control_plane_hash(root),
        "input_hashes": hashes,
    }


def canonical_gate(project_dir: Path, target_mode: str, checks: list[dict[str, Any]]) -> dict[str, Any]:
    """Create the only gate report accepted by V2 transitions.

    A report is built from current inputs every time. Therefore a stale report
    cannot be re-used after a protocol, source, manuscript or code change.
    """
    snapshot = workspace_snapshot(project_dir)
    issues = [
        str(check.get("message") or check.get("issue") or check.get("name") or "gate check failed")
        for check in checks
        if check.get("status") != "pass"
    ]
    report = {
        "contract": "StageGateReportV2",
        "contract_version": 2,
        "generated_at": datetime.now(UTC).isoformat(),
        "project_dir": str(Path(project_dir)),
        "target_mode": target_mode,
        **snapshot,
        "checks": checks,
        "issues": issues,
        "status": "pass" if not issues else "block",
        "gate_eligible": not issues,
    }
    from ..serialization import save_structured_file

    save_structured_file(Path(project_dir) / GATE_REPORT_PATH, report)
    return report


def report_is_current(project_dir: Path, report: dict[str, Any]) -> bool:
    """Reject all V1 reports and V2 reports whose protected inputs changed."""
    if report.get("contract") != "StageGateReportV2" or report.get("contract_version") != 2:
        return False
    current = workspace_snapshot(project_dir)
    return all(
        (
            report.get("commit") == current["commit"],
            report.get("input_hashes") == current["input_hashes"],
            report.get("control_plane_hash") == current["control_plane_hash"],
        )
    )
