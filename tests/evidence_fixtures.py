"""Synthetic, file-backed V2 provenance for scientific regression tests."""

import hashlib
import json
from pathlib import Path


def register_claim_sources(project: Path) -> None:
    claim_path = project / "evidence" / "claim_map.jsonl"
    claims = [json.loads(line) for line in claim_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    registry = []
    for index, claim in enumerate(claims):
        source = project / claim["source_path"]
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        source_id = f"source-{index}"
        observed_at = "2026-01-01T00:00:00Z"
        claim.update(source_id=source_id, source_hash=digest, observed_at=observed_at,
                     locator="synthetic paragraph 1", freshness_policy="immutable", support="supported")
        registry.append({"source_id": source_id, "sha256": digest, "observed_at": observed_at, "path": claim["source_path"]})
    claim_path.write_text("".join(json.dumps(claim) + "\n" for claim in claims), encoding="utf-8-sig")
    (project / "sources" / "registry.jsonl").write_text("".join(json.dumps(source) + "\n" for source in registry), encoding="utf-8")
