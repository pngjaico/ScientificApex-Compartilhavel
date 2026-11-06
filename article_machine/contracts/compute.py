from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ..serialization import load_structured_file


class ContractValidationError(ValueError):
    """Raised when a V2 execution contract is incomplete or ambiguous."""


@dataclass(frozen=True)
class RuntimeContract:
    required: bool
    runner: str
    version: str | None
    timeout_seconds: int
    allowed_directories: tuple[str, ...]
    lockfile: str | None = None
    executable: str | None = None
    package_manager: str | None = None
    package_manager_version: str | None = None
    packages: tuple[str, ...] = ()
    plugins: tuple[str, ...] = ()

    def validate(self, name: str) -> list[str]:
        issues: list[str] = []
        if not isinstance(self.required, bool):
            issues.append(f"{name}.required must be boolean.")
        if not self.runner or not isinstance(self.runner, str):
            issues.append(f"{name}.runner is required.")
        if self.required and not self.version:
            issues.append(f"{name}.version is required when the runtime is required.")
        if self.timeout_seconds < 1:
            issues.append(f"{name}.timeout_seconds must be >= 1.")
        if not self.allowed_directories:
            issues.append(f"{name}.allowed_directories must list approved project-relative directories.")
        for directory in self.allowed_directories:
            candidate = Path(directory)
            if candidate.is_absolute() or ".." in candidate.parts or directory not in {"analysis", "scripts"}:
                issues.append(f"{name}.allowed_directories contains invalid entry '{directory}'.")
        if self.required and not self.lockfile:
            issues.append(f"{name}.lockfile is required when the runtime is required.")
        if self.required and not self.package_manager:
            issues.append(f"{name}.package_manager is required when the runtime is required.")
        if self.required and not self.package_manager_version:
            issues.append(f"{name}.package_manager_version is required when the runtime is required.")
        return issues


@dataclass(frozen=True)
class ComputeContractV2:
    contract_version: int
    python: RuntimeContract
    r: RuntimeContract
    browser: RuntimeContract
    required_plugins: tuple[str, ...] = ()
    source_path: Path | None = field(default=None, compare=False)

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.contract_version != 2:
            issues.append("compute.yaml contract_version must be 2; V1 contracts are historical and not gate eligible.")
        for name, runtime in (("python", self.python), ("r", self.r), ("browser", self.browser)):
            issues.extend(runtime.validate(name))
        for plugin in self.required_plugins:
            if not isinstance(plugin, str) or not plugin.strip():
                issues.append("required_plugins contains an empty plugin identifier.")
        return issues

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("source_path", None)
        return payload


def _runtime_from_payload(name: str, payload: Any) -> RuntimeContract:
    if not isinstance(payload, dict):
        raise ContractValidationError(f"compute.yaml {name} must be an object.")
    allowed = payload.get("allowed_directories", ["analysis", "scripts"])
    if not isinstance(allowed, list):
        raise ContractValidationError(f"compute.yaml {name}.allowed_directories must be a list.")
    packages = payload.get("packages", [])
    plugins = payload.get("plugins", [])
    if not isinstance(packages, list) or not isinstance(plugins, list):
        raise ContractValidationError(f"compute.yaml {name}.packages and plugins must be lists.")
    timeout = payload.get("timeout_seconds", 900)
    if not isinstance(timeout, int) or isinstance(timeout, bool):
        raise ContractValidationError(f"compute.yaml {name}.timeout_seconds must be an integer.")
    lockfile = payload.get("lockfile")
    if lockfile is not None and not isinstance(lockfile, str):
        raise ContractValidationError(f"compute.yaml {name}.lockfile must be a string or null.")
    return RuntimeContract(
        required=payload.get("required", False),
        runner=str(payload.get("runner", "")),
        version=str(payload["version"]) if payload.get("version") is not None else None,
        timeout_seconds=timeout,
        allowed_directories=tuple(str(value) for value in allowed),
        lockfile=lockfile,
        executable=payload.get("executable") if isinstance(payload.get("executable"), str) else None,
        package_manager=payload.get("package_manager") if isinstance(payload.get("package_manager"), str) else None,
        package_manager_version=(
            str(payload["package_manager_version"]) if payload.get("package_manager_version") is not None else None
        ),
        packages=tuple(str(value) for value in packages),
        plugins=tuple(str(value) for value in plugins),
    )


def load_compute_contract(project_dir: Path) -> ComputeContractV2:
    source_path = Path(project_dir) / "compute.yaml"
    payload = load_structured_file(source_path)
    if not payload:
        raise ContractValidationError("compute.yaml is missing or empty.")
    version = payload.get("contract_version")
    if not isinstance(version, int) or isinstance(version, bool):
        raise ContractValidationError("compute.yaml contract_version must be integer 2.")
    plugins = payload.get("required_plugins", [])
    if not isinstance(plugins, list):
        raise ContractValidationError("compute.yaml required_plugins must be a list.")
    contract = ComputeContractV2(
        contract_version=version,
        python=_runtime_from_payload("python", payload.get("python")),
        r=_runtime_from_payload("r", payload.get("r")),
        browser=_runtime_from_payload("browser", payload.get("browser")),
        required_plugins=tuple(str(value) for value in plugins),
        source_path=source_path,
    )
    issues = contract.validate()
    if issues:
        raise ContractValidationError(" ".join(issues))
    return contract
