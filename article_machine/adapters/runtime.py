from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from ..contracts.compute import RuntimeContract


def _workspace_root(project_dir: Path | None) -> Path | None:
    if project_dir is None:
        return None
    project = Path(project_dir).resolve()
    return next((parent for parent in (project, *project.parents) if (parent / "pyproject.toml").is_file()), None)


def _resolve_declared(value: str | None, project_dir: Path | None) -> str | None:
    if not value:
        return None
    declared = Path(value)
    candidates = [declared] if declared.is_absolute() else []
    if project_dir is not None:
        candidates.append(Path(project_dir).resolve() / declared)
        workspace = _workspace_root(project_dir)
        if workspace is not None:
            candidates.append(workspace / declared)
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate.resolve())
    return shutil.which(value)


def resolve_executable(runtime: str, contract: RuntimeContract, project_dir: Path | None = None) -> str | None:
    if runtime == "r" and contract.version:
        versioned_roots = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "R",
            Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "R",
        ]
        for root in versioned_roots:
            candidate = root / f"R-{contract.version}" / "bin" / "x64" / "Rscript.exe"
            if candidate.is_file():
                return str(candidate.resolve())
    for declared in (contract.executable, contract.runner):
        resolved = _resolve_declared(declared, project_dir)
        if resolved:
            return resolved
    candidates = {
        "python": [sys.executable, "python"],
        "r": ["Rscript"],
        "browser": ["node"],
    }.get(runtime, [])
    for candidate_name in candidates:
        resolved = shutil.which(candidate_name) if candidate_name != sys.executable else candidate_name
        if resolved:
            return str(resolved)
    return None


def resolve_lockfile(project_dir: Path, contract: RuntimeContract) -> Path | None:
    if not contract.lockfile:
        return None
    project = Path(project_dir).resolve()
    workspace = _workspace_root(project) or project
    declared = Path(contract.lockfile)
    candidates = [project / declared, workspace / declared] if not declared.is_absolute() else [declared]
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved == workspace or workspace in resolved.parents:
            if resolved.is_file():
                return resolved
    fallback = candidates[0].resolve()
    return fallback if fallback == workspace or workspace in fallback.parents else None


def runtime_version(runtime: str, executable: str) -> str | None:
    try:
        command = [executable, "--version"]
        completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    output = f"{completed.stdout}\n{completed.stderr}"
    if completed.returncode != 0:
        return None
    import re

    patterns = {
        "python": r"Python\s+([0-9]+(?:\.[0-9]+)+)",
        "r": r"version\s+([0-9]+(?:\.[0-9]+)+)",
        "browser": r"Version\s+([0-9]+(?:\.[0-9]+)+)",
    }
    pattern = patterns.get(runtime)
    if pattern is None:
        return None
    match = re.search(pattern, output, flags=re.IGNORECASE)
    return match.group(1) if match else None


def package_manager_version(runtime: str, contract: RuntimeContract, executable: str) -> str | None:
    manager = contract.package_manager
    if manager in {"uv", "npm"}:
        resolved = shutil.which(manager)
        if not resolved:
            return None
        try:
            completed = subprocess.run([resolved, "--version"], capture_output=True, text=True, check=False, timeout=20)
        except (OSError, subprocess.SubprocessError):
            return None
        if completed.returncode != 0:
            return None
        import re

        match = re.search(r"([0-9]+(?:\.[0-9]+)+)", completed.stdout)
        return match.group(1) if match else None
    if manager == "renv":
        expression = (
            "if (requireNamespace('renv', quietly=TRUE)) cat(as.character(packageVersion('renv'))) else quit(status=2)"
        )
        try:
            completed = subprocess.run(
                [executable, "-e", expression], capture_output=True, text=True, check=False, timeout=30
            )
        except (OSError, subprocess.SubprocessError):
            return None
        return completed.stdout.strip() if completed.returncode == 0 else None
    return None
