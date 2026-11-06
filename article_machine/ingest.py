from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import hashlib


def register_source(project_dir: Path, source: str, source_kind: str) -> dict:
    project_dir = Path(project_dir)
    from .services.protocol_registration import registration_gate
    registration = registration_gate(project_dir, "ingest", mark_started=True)
    if registration["status"] != "pass":
        return registration
    registry_path = project_dir / "sources" / "registry.jsonl"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    if source_kind not in {"file", "url", "doi", "note"}:
        raise ValueError("source kind must be file, url, doi or note")
    observed_at = datetime.now(timezone.utc).isoformat()

    entry = {
        "registered_at": observed_at,
        "source": source,
        "source_kind": source_kind,
    }

    if source_kind == "file":
        src = Path(source)
        if not src.is_file():
            raise ValueError("source file is absent or not a regular file")
        digest = hashlib.sha256(src.read_bytes()).hexdigest()
        destination = project_dir / "sources" / "raw" / f"{digest[:16]}_{src.name}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            shutil.copy2(src, destination)
        elif hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
            raise ValueError("registered source destination was changed; preserve and investigate it")
        entry.update(source_id=f"source-{digest[:16]}", sha256=digest, observed_at=observed_at,
                     copied_to=destination.relative_to(project_dir).as_posix(), retrieval_status="retrieved-local")
    else:
        digest = hashlib.sha256((source_kind + ":" + source).encode("utf-8")).hexdigest()
        entry.update(source_id=f"source-{digest[:16]}", retrieval_status="registered-not-retrieved")
        if source_kind == "note":
            entry.update(observed_at=observed_at, note_sha256=digest)

    with registry_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry
