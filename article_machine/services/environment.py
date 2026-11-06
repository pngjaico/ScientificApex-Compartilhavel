from __future__ import annotations

import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from ..adapters.runtime import package_manager_version, resolve_executable, resolve_lockfile, runtime_version
from ..contracts.compute import ComputeContractV2, ContractValidationError, RuntimeContract, load_compute_contract
from ..serialization import load_structured_file, save_structured_file
from .skill_registry import resolve_plugin_binding

RUNTIMES = ("python", "r", "browser")
PROJECT_CONTRACTS = ("project.yaml", "protocol.yaml", "standards.yaml", "compute.yaml")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _runtime(contract: ComputeContractV2, runtime: str) -> RuntimeContract:
    if runtime not in RUNTIMES:
        raise ContractValidationError(f"runtime must be one of: {', '.join(RUNTIMES)}.")
    return {"python": contract.python, "r": contract.r, "browser": contract.browser}[runtime]


def check_environment(project_dir: Path, runtime: str) -> dict[str, Any]:
    """Inspect one runtime only. This function has no download/install side effects."""
    project_dir = Path(project_dir)
    try:
        contract = load_compute_contract(project_dir)
        runtime_contract = _runtime(contract, runtime)
    except ContractValidationError as exc:
        return {
            "contract": "EnvironmentCheckV2",
            "status": "blocked",
            "runtime": runtime,
            "issues": [str(exc)],
            "checked_at": _now(),
        }
    executable = resolve_executable(runtime, runtime_contract, project_dir)
    lockfile = resolve_lockfile(project_dir, runtime_contract)
    issues: list[str] = []
    if runtime_contract.required and not executable:
        issues.append(f"{runtime} executable is unavailable.")
    if runtime_contract.required and (lockfile is None or not lockfile.is_file()):
        issues.append(f"{runtime} lockfile is missing: {runtime_contract.lockfile!r}.")
    detected_version = runtime_version(runtime, executable) if executable else None
    if (
        runtime_contract.required
        and runtime_contract.version
        and not (detected_version and detected_version.startswith(runtime_contract.version))
    ):
        issues.append(
            f"{runtime} version mismatch: expected {runtime_contract.version}, found {detected_version or 'unknown'}."
        )
    detected_manager_version = package_manager_version(runtime, runtime_contract, executable) if executable else None
    if (
        runtime_contract.required
        and runtime_contract.package_manager_version
        and not (
            detected_manager_version and detected_manager_version.startswith(runtime_contract.package_manager_version)
        )
    ):
        issues.append(
            f"{runtime} package manager {runtime_contract.package_manager or 'unknown'} version mismatch: "
            f"expected {runtime_contract.package_manager_version}, found {detected_manager_version or 'unavailable'}."
        )
    browser_cache = Path(project_dir).resolve().parent.parent / "tools" / "playwright" / ".playwright"
    browser_installed = runtime != "browser" or any(browser_cache.glob("chromium-*"))
    if runtime == "browser" and runtime_contract.required and not browser_installed:
        issues.append("browser binaries are absent from the locked workspace Playwright cache.")
    status = "passed" if not issues else "blocked"
    return {
        "contract": "EnvironmentCheckV2",
        "status": status,
        "runtime": runtime,
        "required": runtime_contract.required,
        "runner": runtime_contract.runner,
        "executable": executable,
        "expected_version": runtime_contract.version,
        "detected_version": detected_version,
        "package_manager": runtime_contract.package_manager,
        "expected_package_manager_version": runtime_contract.package_manager_version,
        "detected_package_manager_version": detected_manager_version,
        "browser_cache": str(browser_cache) if runtime == "browser" else None,
        "browser_installed": browser_installed if runtime == "browser" else None,
        "lockfile": str(lockfile) if lockfile else None,
        "lockfile_present": bool(lockfile and lockfile.is_file()),
        "timeout_seconds": runtime_contract.timeout_seconds,
        "allowed_directories": list(runtime_contract.allowed_directories),
        "issues": issues,
        "checked_at": _now(),
    }


def prepare_environment(project_dir: Path, runtime: str, *, execute: bool = False) -> dict[str, Any]:
    """The sole installation-capable path. Default is an explicit dry run."""
    check = check_environment(project_dir, runtime)
    check["contract"] = "EnvironmentPrepareV2"
    check["prepare_authorized"] = True
    check["executed"] = execute
    if check["status"] == "passed" or not execute:
        check["action"] = "none" if check["status"] == "passed" else "dry-run: runtime preparation required"
        return check
    if not check.get("lockfile_present"):
        check["action"] = "blocked: a declared lockfile is required before preparation"
        return check
    # Actual install commands are deliberately narrow and locked. No runner calls this.
    workspace_root = Path(project_dir).resolve().parent.parent
    commands = {
        "python": [["uv", "sync", "--locked", "--all-extras", "--dev"]],
        "r": [
            [
                check.get("executable") or "Rscript",
                "-e",
                "if (!requireNamespace('renv', quietly=TRUE) || as.character(packageVersion('renv')) != '1.3.1') "
                "install.packages('https://cran.r-project.org/src/contrib/renv_1.3.1.tar.gz', "
                "repos=NULL, type='source'); "
                "renv::restore(lockfile='renv.lock', prompt=FALSE)",
            ]
        ],
        "browser": [
            ["npm", "ci", "--prefix", "tools/playwright", "--ignore-scripts"],
            ["npm", "exec", "--prefix", "tools/playwright", "--", "playwright", "install", "chromium"],
        ],
    }
    cwd = Path(project_dir) if runtime == "r" else workspace_root
    executions: list[dict[str, Any]] = []
    for command in commands[runtime]:
        executable = shutil.which(command[0])
        if executable:
            command = [executable, *command[1:]]
        environment = os.environ.copy()
        if runtime == "browser":
            environment["PLAYWRIGHT_BROWSERS_PATH"] = str(workspace_root / "tools" / "playwright" / ".playwright")
        try:
            completed = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
                env=environment,
            )
        except OSError as exc:
            executions.append({"command": command, "exit_code": None, "stdout": "", "stderr": str(exc)})
            break
        executions.append(
            {
                "command": command,
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        )
        if completed.returncode != 0:
            break
    check["prepare_commands"] = executions
    check["prepare_exit_code"] = executions[-1]["exit_code"] if executions else None
    refreshed = check_environment(project_dir, runtime)
    for key, value in refreshed.items():
        if key not in {"contract", "runtime"}:
            check[key] = value
    return check


def _contract_schema_check(project_dir: Path, name: str) -> list[str]:
    try:
        payload = load_structured_file(Path(project_dir) / name)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [f"{name} cannot be read: {exc}"]
    if not payload:
        return [f"{name} is missing or empty."]
    if payload.get("contract_version") != 2:
        return [f"{name} contract_version must be 2 for a V2 preflight."]
    return []


def preflight_environment(project_dir: Path) -> dict[str, Any]:
    project_dir = Path(project_dir)
    checks: dict[str, Any] = {}
    issues: list[str] = []
    for name in PROJECT_CONTRACTS:
        schema_issues = _contract_schema_check(project_dir, name)
        checks[name] = {"status": "pass" if not schema_issues else "blocked", "issues": schema_issues}
        issues.extend(schema_issues)
    try:
        contract = load_compute_contract(project_dir)
    except (ContractValidationError, OSError, ValueError, yaml.YAMLError) as exc:
        checks["compute_contract"] = {"status": "blocked", "issues": [str(exc)]}
        issues.append(str(exc))
        contract = None
    if contract:
        for runtime in RUNTIMES:
            check = check_environment(project_dir, runtime)
            checks[runtime] = check
            if check["status"] == "blocked":
                issues.extend(check["issues"])
        if contract.required_plugins:
            missing = []
            binding_issues = []
            for plugin in contract.required_plugins:
                try:
                    resolve_plugin_binding(plugin, project_dir)
                except (OSError, ValueError) as exc:
                    missing.append(plugin)
                    binding_issues.append(f"{plugin}: {exc}")
            checks["plugins"] = {
                "status": "pass" if not missing else "blocked",
                "required": list(contract.required_plugins),
                "missing": missing,
                "issues": binding_issues,
            }
            if missing:
                issues.extend(f"Plugin binding unavailable for {detail}." for detail in binding_issues)
        else:
            checks["plugins"] = {"status": "pass", "required": [], "missing": []}
    status = "passed" if not issues else "blocked"
    report = {
        "contract": "PreflightReportV2",
        "status": status,
        "project_dir": str(project_dir),
        "checks": checks,
        "issues": issues,
        "checked_at": _now(),
    }
    save_structured_file(project_dir / "analysis" / "preflight.json", report)
    return report
