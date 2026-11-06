from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

from .graph_query import query_operational_graph
from .skill_registry import audit_skill_provenance


def _run(command: list[str], cwd: Path, timeout: int = 600) -> dict[str, Any]:
    started = perf_counter()
    executable = shutil.which(command[0])
    if executable:
        command = [executable, *command[1:]]
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout,
        )
        return {
            "status": "pass" if completed.returncode == 0 else "block",
            "command": command,
            "exit_code": completed.returncode,
            "duration_seconds": round(perf_counter() - started, 3),
            "stdout_tail": completed.stdout[-6000:],
            "stdout": completed.stdout,
            "stderr_tail": completed.stderr[-6000:],
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "status": "block",
            "command": command,
            "exit_code": None,
            "duration_seconds": round(perf_counter() - started, 3),
            "stdout_tail": "",
            "stderr_tail": str(exc),
        }


def _git_status(root: Path) -> dict[str, Any]:
    result = _run(["git", "status", "--porcelain=v1"], root, timeout=30)
    entries = [line for line in result.get("stdout", result["stdout_tail"]).splitlines() if line.strip()]
    return {**result, "clean": result["status"] == "pass" and not entries, "entry_count": len(entries)}


def _tracked_sensitive(root: Path) -> dict[str, Any]:
    result = _run(["git", "ls-files", "-z"], root, timeout=30)
    paths = [item for item in result.get("stdout", result["stdout_tail"]).split("\0") if item]
    blocked = []
    for path in paths:
        normalized = path.replace("\\", "/").lower()
        # Curated instructions about patients/fulltext are not patient records.
        instruction_document = normalized.startswith("skills/") and normalized.endswith(".md")
        basename = normalized.rsplit("/", 1)[-1]
        sanitized_template = normalized == "skills/tooluniverse-clinical-trial-design/.env.template"
        if (
            (basename == ".env" or basename.startswith(".env.")) and not sanitized_template
            or normalized.endswith(".pdf")
            or "/raw/" in normalized
            or (
                not instruction_document
                and any(token in normalized for token in ("patient", "pacient", "fulltext", "full-text"))
            )
        ):
            blocked.append(path)
    return {
        "status": "pass" if result["status"] == "pass" and not blocked else "block",
        "tracked_sensitive_paths": blocked,
        "issues": ["Sensitive or raw paths are tracked."] if blocked else [],
    }


def machine_doctor(workspace_root: Path, project_dir: Path | None = None) -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    checks: dict[str, Any] = {
        "python": {"status": "pass", "version": sys.version.split()[0], "executable": sys.executable},
        "uv": _run(["uv", "--version"], root, timeout=30),
        "node": _run(["node", "--version"], root, timeout=30),
        "npm": _run(["npm", "--version"], root, timeout=30),
        "playwright": _run(
            [str(root / "tools" / "playwright" / "node_modules" / ".bin" / "playwright.cmd"), "--version"],
            root,
            timeout=30,
        ),
        "skill_provenance": audit_skill_provenance(root=root, strict=True),
        "graph_query": query_operational_graph("article machine lifecycle gates", scope="control-plane", limit=10),
        "tracked_sensitive": _tracked_sensitive(root),
    }
    r_461 = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "R" / "R-4.6.1" / "bin" / "x64" / "Rscript.exe"
    if not r_461.is_file():
        r_461 = Path("C:/Program Files/R/R-4.6.1/bin/x64/Rscript.exe")
    checks["r_4_6_1"] = (
        _run([str(r_461), "--version"], root, timeout=30)
        if r_461.is_file()
        else {
            "status": "block",
            "issues": ["R 4.6.1 side-by-side runtime is absent."],
        }
    )
    if project_dir is not None:
        from .environment import preflight_environment

        checks["project_preflight"] = preflight_environment(Path(project_dir))
    status = "pass" if all(check.get("status") in {"pass", "passed", "ok"} for check in checks.values()) else "block"
    return {"contract": "MachineDoctorReportV2", "status": status, "workspace_root": str(root), "checks": checks}


def release_audit(project_dir: Path) -> dict[str, Any]:
    project = Path(project_dir).resolve()
    root = next((parent for parent in (project, *project.parents) if (parent / "pyproject.toml").is_file()), project)
    python = str(root / ".venv" / "Scripts" / "python.exe")
    commands = {
        "uv_lock": ["uv", "lock", "--check"],
        "uv_sync_dry_run": ["uv", "sync", "--locked", "--all-extras", "--dev", "--dry-run"],
        "tests_coverage": [
            python,
            "-m",
            "pytest",
            "--cov=article_machine",
            "--cov-report=term-missing",
            "--cov-fail-under=85",
        ],
        "ruff_new_modules": [
            python,
            "-m",
            "ruff",
            "check",
            "article_machine/contracts",
            "article_machine/adapters",
            "article_machine/services",
            "article_machine/policy",
            "article_machine/commands",
        ],
        "mypy_new_modules": [
            python,
            "-m",
            "mypy",
            "article_machine/contracts",
            "article_machine/adapters",
            "article_machine/services",
            "article_machine/policy",
            "article_machine/commands",
        ],
        "pip_audit": [python, "-m", "pip_audit", "--progress-spinner", "off"],
        "npm_audit": ["npm", "audit", "--prefix", "tools/playwright", "--audit-level=high"],
        "graph_validation": [
            python,
            "-c",
            "import json; from scripts.generate_workspace_graph import validate_operational_graph; "
            "r=validate_operational_graph(); print(json.dumps(r)); "
            "raise SystemExit(0 if r.get('status')=='pass' else 1)",
        ],
        "machine_strict_audit": [
            python,
            "-m",
            "article_machine",
            "machine",
            "audit",
            "--workspace-root",
            ".",
            "--strict",
        ],
    }
    checks = {
        name: _run(command, root, timeout=1200 if name == "tests_coverage" else 600)
        for name, command in commands.items()
    }
    checks["git_clean"] = _git_status(root)
    checks["git_clean"]["status"] = "pass" if checks["git_clean"]["clean"] else "block"
    checks["tracked_sensitive"] = _tracked_sensitive(root)
    checks["skill_provenance"] = audit_skill_provenance(root=root, strict=True)

    from ..benchmarks import validate_benchmark_report
    from ..serialization import load_structured_file
    from ..zero_trust import audit_stage

    project_payload = load_structured_file(project / "project.yaml")
    checks["stage_gate"] = audit_stage(
        project, target_mode="release" if project_payload.get("lane") == "machine-governance" else "submission"
    )
    checks["benchmark"] = validate_benchmark_report(project)
    statuses = [check.get("status") for check in checks.values()]
    passed = all(status in {"pass", "passed"} for status in statuses)
    head = _run(["git", "rev-parse", "HEAD"], root, timeout=30)
    return {
        "contract": "MachineReleaseAuditV2",
        "status": "verified-local" if passed else "blocked",
        "gate_eligible": passed,
        "release_state": "verified-local" if passed else "not-verified",
        "commit": head.get("stdout_tail", "").strip() or None,
        "remote_ci_verified": False,
        "checks": checks,
        "issues": [name for name, check in checks.items() if check.get("status") not in {"pass", "passed"}],
    }
