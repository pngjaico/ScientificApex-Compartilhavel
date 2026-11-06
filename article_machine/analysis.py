"""Compatibility facade for analysis execution.

V2 projects are served by ``services.environment`` and ``services.runners``.
The small V1 branch remains readable for historical projects only; it is never
reported as a V2 gate-eligible contract.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from .serialization import load_structured_file, save_structured_file
from .services.environment import preflight_environment
from .services.runners import run_python_script as _run_python_v2
from .services.runners import run_r_script as _run_r_v2


def _legacy_preflight(project_dir: Path) -> dict:
    """Read-only historical compatibility for V1 projects.

    New projects must use contract_version: 2 and are validated by the real
    four-contract preflight below.
    """
    rscript = shutil.which("Rscript")
    compute = load_structured_file(project_dir / "compute.yaml")
    r_required = bool(compute.get("r", {}).get("required"))
    required_files = ("project.yaml", "protocol.yaml", "standards.yaml", "compute.yaml")
    missing = [name for name in required_files if not (project_dir / name).is_file()]
    r_check = {
        "status": "pass" if rscript else ("blocked" if r_required else "warning"),
        "path": rscript,
        "message": f"Rscript detected at {rscript}." if rscript else (
            "Rscript is not available. Install R for Windows and ensure `Rscript` is on PATH before running `.R`, `.Rmd`, or `.qmd` pipelines."
            if r_required else "Rscript is not available, but this historical project does not currently require R."
        ),
    }
    issues = [f"{name} is missing." for name in missing]
    if r_required and not rscript:
        issues.append("Rscript is unavailable.")
    report = {
        "contract": "PreflightReportV1Historical",
        "status": "passed" if not issues else "blocked",
        "gate_eligible": False,
        "checks": {
            "rscript": r_check,
            "project_files": {"status": "pass" if not missing else "blocked", "missing": missing},
        },
        "issues": issues,
    }
    save_structured_file(project_dir / "analysis" / "preflight.json", report)
    return report


def preflight(project_dir: Path) -> dict:
    project_dir = Path(project_dir)
    try:
        compute = load_structured_file(project_dir / "compute.yaml")
    except (OSError, ValueError):
        return preflight_environment(project_dir)
    if compute.get("contract_version") != 2:
        return _legacy_preflight(project_dir)
    return preflight_environment(project_dir)


def run_r_script(project_dir: Path, script_path: Path) -> dict:
    project_dir = Path(project_dir)
    if load_structured_file(project_dir / "compute.yaml").get("contract_version") != 2:
        return {"contract": "ScriptRunReportV2", "status": "blocked", "gate_eligible": False,
                "issues": ["Historical V1 compute contracts are readable but cannot execute; migrate to ComputeContractV2."]}
    # Keep the public facade stable; V2 captures timeout, hashes and environment.
    return _run_r_v2(project_dir, script_path, subprocess_run=subprocess.run)


def run_python_script(project_dir: Path, script_path: Path) -> dict:
    project_dir = Path(project_dir)
    if load_structured_file(project_dir / "compute.yaml").get("contract_version") != 2:
        return {"contract": "ScriptRunReportV2", "status": "blocked", "runtime": "python", "issues": ["run-python requires ComputeContractV2."]}
    return _run_python_v2(project_dir, script_path, subprocess_run=subprocess.run)
