import hashlib
import json
from pathlib import Path

from article_machine.evidence import validate_evidence_lock
from article_machine.projects import init_project
from evidence_fixtures import register_claim_sources


def test_evidence_v2_needs_registry_and_hashed_source(tmp_path: Path) -> None:
    project = init_project(tmp_path, "Evidence", "systematic-review")
    source = project / "sources" / "a.md"
    source.write_text("Observed result.", encoding="utf-8")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    (project / "drafts" / "manuscript.md").write_text("{{claim:x}}", encoding="utf-8")
    (project / "drafts" / "references.bib").write_text("@article{k, title={x}}", encoding="utf-8")
    (project / "sources" / "registry.jsonl").write_text(json.dumps({"source_id": "s", "sha256": digest}) + "\n", encoding="utf-8")
    (project / "evidence" / "claim_map.jsonl").write_text(json.dumps({"claim_id":"x","statement":"x","source_path":"sources/a.md","source_excerpt":"Observed result.","reference_key":"k","status":"supported","source_id":"s","source_hash":digest,"observed_at":"2026-01-01T00:00:00Z","locator":"p1","freshness_policy":"static","support":"supported"}) + "\n", encoding="utf-8")
    register_claim_sources(project)
    report = validate_evidence_lock(project)
    assert report["gate_eligible"] is True
