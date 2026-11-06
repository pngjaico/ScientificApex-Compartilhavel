from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

from ..adapters.runtime import resolve_executable
from ..contracts.compute import ContractValidationError, load_compute_contract
from ..runs import close_run, open_run, record_artifact, save_manifest
from .environment import preflight_environment

ALLOWED_EXTENSIONS = {"python": {".py"}, "r": {".r", ".rmd", ".qmd"}}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_script(project_dir: Path, script_path: Path, runtime: str, allowed_directories: tuple[str, ...]) -> Path:
    root = Path(project_dir).resolve()
    candidate = Path(script_path).resolve()
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise ContractValidationError("Script must be inside the active project.") from exc
    if not candidate.is_file():
        raise ContractValidationError("Script does not exist or is not a regular file.")
    if not relative.parts or relative.parts[0] not in set(allowed_directories):
        approved = " or ".join(f"{name}/" for name in allowed_directories)
        raise ContractValidationError(f"Scripts may only run from {approved}.")
    if candidate.suffix.lower() not in ALLOWED_EXTENSIONS[runtime]:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS[runtime]))
        raise ContractValidationError(f"{runtime} runner only accepts: {allowed}.")
    return candidate


def run_script(
    project_dir: Path, script_path: Path, runtime: str, *, subprocess_run: Any = subprocess.run
) -> dict[str, Any]:
    project_dir = Path(project_dir)
    from .protocol_registration import registration_gate
    registration = registration_gate(project_dir, f"run-{runtime}")
    if registration["status"] != "pass":
        return {**registration, "runtime": runtime, "gate_eligible": False}
    preflight = preflight_environment(project_dir)
    if preflight["status"] != "passed":
        return preflight
    try:
        contract = load_compute_contract(project_dir)
        runtime_contract = getattr(contract, runtime)
        script = _safe_script(project_dir, script_path, runtime, runtime_contract.allowed_directories)
    except (ContractValidationError, AttributeError) as exc:
        return {"contract": "ScriptRunReportV2", "status": "blocked", "runtime": runtime, "issues": [str(exc)]}
    executable = resolve_executable(runtime, runtime_contract, project_dir)
    if not executable:
        return {
            "contract": "ScriptRunReportV2",
            "status": "blocked",
            "runtime": runtime,
            "issues": [f"{runtime} executable is unavailable."],
        }

    registration_gate(project_dir, f"run-{runtime}", mark_started=True)
    manifest = open_run(project_dir, mode="analysis", prompt=f"Run {runtime} script {script.name}")
    run_dir = project_dir / ".machine" / "runs" / manifest["run_id"] / "analysis" / runtime / script.stem
    run_dir.mkdir(parents=True, exist_ok=True)
    stdout_log = run_dir / "stdout.log"
    stderr_log = run_dir / "stderr.log"
    environment_log = run_dir / "environment.json"
    command = [executable, str(script)]
    try:
        result = subprocess_run(
            command,
            capture_output=True,
            text=True,
            check=False,
            cwd=project_dir,
            timeout=runtime_contract.timeout_seconds,
        )
        exit_code = result.returncode
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        exit_code = None
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
        timed_out = True
    except OSError as exc:
        exit_code = None
        stdout = ""
        stderr = str(exc)
        timed_out = False
    stdout_log.write_text(stdout, encoding="utf-8")
    stderr_log.write_text(stderr, encoding="utf-8")
    environment_log.write_text(
        __import__("json").dumps(
            {
                "runtime": runtime,
                "runner": runtime_contract.runner,
                "executable": executable,
                "command": command,
                "timeout_seconds": runtime_contract.timeout_seconds,
                "script_sha256": _sha256(script),
                "timed_out": timed_out,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    for artifact in (stdout_log, stderr_log, environment_log):
        record_artifact(project_dir, manifest["run_id"], artifact)
    current = __import__("article_machine.runs", fromlist=["load_manifest"]).load_manifest(
        project_dir, manifest["run_id"]
    )
    current["execution"] = {
        "runtime": runtime,
        "command": command,
        "script": script.relative_to(project_dir).as_posix(),
        "script_sha256": _sha256(script),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "timeout_seconds": runtime_contract.timeout_seconds,
    }
    save_manifest(project_dir, manifest["run_id"], current)
    status = "passed" if exit_code == 0 and not timed_out else "failed"
    close_run(project_dir, manifest["run_id"], status=status)
    return {
        "contract": "ScriptRunReportV2",
        "status": status,
        "runtime": runtime,
        "run_id": manifest["run_id"],
        "exit_code": exit_code,
        "timed_out": timed_out,
        "stdout_log": stdout_log.relative_to(project_dir).as_posix(),
        "stderr_log": stderr_log.relative_to(project_dir).as_posix(),
        "environment_log": environment_log.relative_to(project_dir).as_posix(),
    }


def run_python_script(project_dir: Path, script_path: Path, **kwargs: Any) -> dict[str, Any]:
    return run_script(project_dir, script_path, "python", **kwargs)


def run_r_script(project_dir: Path, script_path: Path, **kwargs: Any) -> dict[str, Any]:
    return run_script(project_dir, script_path, "r", **kwargs)
