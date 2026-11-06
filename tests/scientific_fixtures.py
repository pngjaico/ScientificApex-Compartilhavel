"""Synthetic evidence for software tests only; never real human/clinical approval."""

import json
from pathlib import Path

from evidence_fixtures import register_claim_sources


def supported_synthetic_claim(project: Path) -> str:
    source = project / "sources" / "synthetic_software_fixture.md"
    excerpt = "Synthetic software fixture only. No clinical evidence or human review is asserted."
    source.write_text(excerpt, encoding="utf-8")
    claim_id = "synthetic-software-result"
    claim = {
        "claim_id": claim_id,
        "statement": excerpt,
        "source_path": "sources/synthetic_software_fixture.md",
        "source_excerpt": excerpt,
        "reference_key": "software-fixture",
        "status": "supported",
    }
    (project / "drafts/manuscript.md").write_text("{{claim:" + claim_id + "}}", encoding="utf-8")
    (project / "drafts/references.bib").write_text(
        "@misc{software-fixture, title={Synthetic software fixture}}", encoding="utf-8"
    )
    (project / "evidence/claim_map.jsonl").write_text(json.dumps(claim) + "\n", encoding="utf-8")
    register_claim_sources(project)
    return claim_id
