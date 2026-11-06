from pathlib import Path

import pytest

from article_machine.contracts import ContractValidationError, load_compute_contract
from article_machine.projects import init_project
from article_machine.serialization import load_structured_file, save_structured_file


def _v2_project(tmp_path: Path) -> Path:
    project = init_project(tmp_path, "V2 Contract", "systematic-review")
    for name in ("project.yaml", "protocol.yaml", "standards.yaml"):
        payload = load_structured_file(project / name)
        payload["contract_version"] = 2
        save_structured_file(project / name, payload)
    (project / "uv.lock").write_text("version = 1\n", encoding="utf-8")
    compute = {
        "contract_version": 2,
        "python": {
            "required": True,
            "version": "3.13",
            "runner": "python",
            "package_manager": "uv",
            "package_manager_version": "0.11.31",
            "timeout_seconds": 30,
            "allowed_directories": ["analysis", "scripts"],
            "lockfile": "uv.lock",
        },
        "r": {
            "required": False,
            "runner": "Rscript",
            "timeout_seconds": 30,
            "allowed_directories": ["analysis", "scripts"],
            "lockfile": "renv.lock",
        },
        "browser": {
            "required": False,
            "runner": "node",
            "timeout_seconds": 30,
            "allowed_directories": ["analysis", "scripts"],
            "lockfile": "tools/playwright/package-lock.json",
        },
        "required_plugins": [],
    }
    save_structured_file(project / "compute.yaml", compute)
    from registration_fixtures import reviewed_registration_fixture
    reviewed_registration_fixture(project)
    return project


def test_compute_contract_v2_loads_fail_closed(tmp_path: Path) -> None:
    project = _v2_project(tmp_path)
    contract = load_compute_contract(project)
    assert contract.contract_version == 2
    assert contract.python.lockfile == "uv.lock"


def test_compute_contract_v2_rejects_unconfined_directories(tmp_path: Path) -> None:
    project = _v2_project(tmp_path)
    compute = load_structured_file(project / "compute.yaml")
    compute["python"]["allowed_directories"] = ["../outside"]
    save_structured_file(project / "compute.yaml", compute)
    with pytest.raises(ContractValidationError, match="invalid entry"):
        load_compute_contract(project)
