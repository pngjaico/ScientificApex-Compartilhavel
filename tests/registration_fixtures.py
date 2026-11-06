"""Synthetic registry fixtures for local gate tests; never external registrations."""

import hashlib
import json
from pathlib import Path

from article_machine.projects import register_review_protocol
from article_machine.services.protocol_registration import protocol_fingerprint, verify_protocol_registration


def reviewed_registration_fixture(project: Path) -> dict:
    from article_machine.serialization import load_structured_file, save_structured_file
    protocol = load_structured_file(project / "protocol.yaml")
    protocol["status"] = "frozen"
    save_structured_file(project / "protocol.yaml", protocol)
    register_review_protocol(project, "OSF", "abc12", "https://osf.io/abc12/", "2020-01-01")
    folder = project / "evidence" / "protocol_registration"
    folder.mkdir(parents=True, exist_ok=True)
    source = folder / "synthetic_registry_record.txt"
    source.write_text(
        "SYNTHETIC UNIT TEST RECORD. Not a real OSF registration; never cite or publish.", encoding="utf-8"
    )
    record = {
        "registry": "OSF",
        "registry_id": "abc12",
        "registry_url": "https://osf.io/abc12/",
        "registered_at": "2020-01-01",
        "record_kind": "registration",
        "registration_final": True,
        "protocol_matches_record": True,
        "protocol_sha256": protocol_fingerprint(project),
        "reviewer": "synthetic test reviewer; not a real attestation",
        "verified_at": "2020-01-02",
        "scientific_work_not_started_before_registration": True,
        "verification_method": "reviewed-hashed-registry-record",
        "source_record_path": source.relative_to(project).as_posix(),
        "source_record_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }
    path = folder / "synthetic_review_record.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    result = verify_protocol_registration(project, path)
    assert result["status"] == "pass", result
    return record
