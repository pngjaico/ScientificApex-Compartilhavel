import json
from pathlib import Path

import pytest
from registration_fixtures import reviewed_registration_fixture

from article_machine.projects import gate_mode, init_project, register_review_protocol
from article_machine.serialization import load_structured_file, save_structured_file
from article_machine.services.protocol_registration import (
    START_PATH,
    VERIFICATION_PATH,
    registration_gate,
    verify_protocol_registration,
)


@pytest.mark.parametrize(
    "kind", ["systematic-review", "prediction-model", "observational-study", "clinical-trial", "unknown-type"]
)
def test_registration_is_required_before_scientific_work_even_if_flags_are_false(tmp_path: Path, kind: str):
    project = init_project(tmp_path, "Before registration", kind)
    for name, key in [("protocol.yaml", "registration"), ("standards.yaml", "registration_policy")]:
        payload = load_structured_file(project / name)
        payload[key]["required"] = False
        save_structured_file(project / name, payload)
    assert registration_gate(project, "run-python")["status"] == "blocked"
    payload = load_structured_file(project / "project.yaml")
    payload["state"].update(current_mode="protocol-freeze", allowed_next_modes=["corpus-build"])
    save_structured_file(project / "project.yaml", payload)
    assert gate_mode(project, "corpus-build")["status"] == "blocked"
    assert not (project / START_PATH).exists()


def test_declaring_a_registry_identifier_is_not_verification(tmp_path: Path):
    project = init_project(tmp_path, "Declared only", "systematic-review")
    record = register_review_protocol(project, "OSF", "abc12", "https://osf.io/abc12/", "2020-01-01")
    assert record["status"] == "declared-unverified"
    assert record["registered_before_extraction"] is False
    assert registration_gate(project, "analysis")["status"] == "blocked"


def test_verified_registration_binds_protocol_source_and_start_time(tmp_path: Path):
    project = init_project(tmp_path, "Synthetic gate fixture", "systematic-review")
    reviewed_registration_fixture(project)
    assert registration_gate(project, "ingest", mark_started=True)["status"] == "pass"
    start = json.loads((project / START_PATH).read_text())
    assert registration_gate(project, "analysis", mark_started=True)["status"] == "pass"
    assert json.loads((project / START_PATH).read_text()) == start
    protocol = load_structured_file(project / "protocol.yaml")
    protocol["research_question"] = "Changed outcome after registration"
    save_structured_file(project / "protocol.yaml", protocol)
    assert registration_gate(project, "analysis")["status"] == "blocked"


@pytest.mark.parametrize("change", ["source", "manifest", "draft", "wrong-host", "late", "missing-reviewer", "outside"])
def test_unreviewed_tampered_late_or_nonregistration_records_are_rejected(tmp_path: Path, change: str):
    project = init_project(tmp_path, "Tamper fixture", "systematic-review")
    record = reviewed_registration_fixture(project)
    path = project / "evidence/protocol_registration/synthetic_review_record.json"
    if change == "source":
        (project / record["source_record_path"]).write_text("changed", encoding="utf-8")
    elif change == "manifest":
        (project / VERIFICATION_PATH).write_text("{}", encoding="utf-8")
        assert registration_gate(project, "analysis")["status"] == "blocked"
        return
    elif change == "draft":
        record["record_kind"] = "project"
        record["registration_final"] = False
    elif change == "wrong-host":
        protocol = load_structured_file(project / "protocol.yaml")
        protocol["registration"]["registry_url"] = "https://osf.io.evil.example/abc12/"
        save_structured_file(project / "protocol.yaml", protocol)
        record["registry_url"] = protocol["registration"]["registry_url"]
    elif change == "late":
        (project / START_PATH).parent.mkdir(exist_ok=True)
        (project / START_PATH).write_text(json.dumps({"started_at": "2019-01-01"}), encoding="utf-8")
    elif change == "missing-reviewer":
        record["reviewer"] = ""
    else:
        record["source_record_path"] = "../../outside.txt"
    path.write_text(json.dumps(record), encoding="utf-8")
    assert verify_protocol_registration(project, path)["status"] == "blocked"


def test_governance_smokes_are_exempt_but_lane_spoofing_is_not(tmp_path: Path):
    project = init_project(tmp_path, "Machine tests", "machine-governance")
    assert registration_gate(project, "run-python")["required"] is False
    payload = load_structured_file(project / "project.yaml")
    payload["project_type"] = "prediction-model"
    save_structured_file(project / "project.yaml", payload)
    assert registration_gate(project, "run-python")["status"] == "blocked"


def test_direct_runner_and_ingest_are_blocked_before_any_scientific_side_effect(tmp_path: Path):
    from article_machine.ingest import register_source
    from article_machine.services.runners import run_python_script

    project = init_project(tmp_path, "Not registered", "prediction-model")
    script = project / "analysis" / "must_not_run.py"
    script.write_text("raise RuntimeError('must not run')", encoding="utf-8")

    def forbidden(*args, **kwargs):
        pytest.fail("An unregistered study reached subprocess execution")

    assert run_python_script(project, script, subprocess_run=forbidden)["status"] == "blocked"
    source_registry = project / "sources" / "registry.jsonl"
    before = source_registry.read_bytes() if source_registry.exists() else None
    assert register_source(project, "not copied", "note")["status"] == "blocked"
    after = source_registry.read_bytes() if source_registry.exists() else None
    assert before == after
    assert not (project / START_PATH).exists()


@pytest.mark.parametrize("malformed", [None, [], "registered"])
def test_malformed_registration_declaration_fails_closed(tmp_path: Path, malformed):
    project = init_project(tmp_path, "Malformed", "prediction-model")
    protocol = load_structured_file(project / "protocol.yaml")
    protocol["registration"] = malformed
    save_structured_file(project / "protocol.yaml", protocol)
    assert registration_gate(project, "analysis")["status"] == "blocked"


@pytest.mark.parametrize("activity", ["source", "run", "undated-source"])
def test_legacy_work_before_registration_is_blocked_without_new_start_marker(tmp_path: Path, activity: str):
    project = init_project(tmp_path, "Legacy chronology", "systematic-review")
    reviewed_registration_fixture(project)
    assert not (project / START_PATH).exists()
    if activity in {"source", "undated-source"}:
        payload = {"registered_at": "2019-01-01"} if activity == "source" else {"source": "undated"}
        (project / "sources/registry.jsonl").write_text(json.dumps(payload) + "\n", encoding="utf-8")
    else:
        path = project / ".machine/runs/legacy/manifest.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"mode": "analysis", "started_at": "2019-01-01"}), encoding="utf-8")
    assert registration_gate(project, "analysis")["status"] == "blocked"


@pytest.mark.parametrize("reviewer", [None, False, 123, "  "])
def test_nonstring_or_blank_reviewer_cannot_approve_registration(tmp_path: Path, reviewer):
    project = init_project(tmp_path, "Incomplete reviewer", "systematic-review")
    record = reviewed_registration_fixture(project)
    record["reviewer"] = reviewer
    path = project / "evidence/protocol_registration/synthetic_review_record.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    assert verify_protocol_registration(project, path)["status"] == "blocked"
