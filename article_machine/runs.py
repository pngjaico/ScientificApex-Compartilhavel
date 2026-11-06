from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets

from .projects import load_project
from .serialization import load_structured_file, save_structured_file


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_id() -> str:
    return f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}"


def _manifest_path(project_dir: Path, run_id: str) -> Path:
    return Path(project_dir) / ".machine" / "runs" / run_id / "manifest.json"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def open_run(project_dir: Path, mode: str, prompt: str) -> dict:
    project = load_project(project_dir)
    run_id = _run_id()
    manifest = {
        "run_id": run_id,
        "mode": mode,
        "prompt": prompt,
        "status": "running",
        "started_at": _now_iso(),
        "finished_at": None,
        "project": {
            "id": project.get("id"),
            "name": project.get("name"),
            "project_type": project.get("project_type"),
            "lane": project.get("lane"),
        },
        "artifacts": [],
    }
    save_structured_file(_manifest_path(project_dir, run_id), manifest)
    return manifest


def load_manifest(project_dir: Path, run_id: str) -> dict:
    return load_structured_file(_manifest_path(project_dir, run_id))


def save_manifest(project_dir: Path, run_id: str, manifest: dict) -> dict:
    save_structured_file(_manifest_path(project_dir, run_id), manifest)
    return manifest


def record_artifact(project_dir: Path, run_id: str, artifact_path: Path) -> dict:
    artifact_path = Path(artifact_path)
    manifest = load_manifest(project_dir, run_id)
    rel_path = artifact_path.relative_to(Path(project_dir)).as_posix()
    manifest["artifacts"].append(
        {
            "path": rel_path,
            "sha256": _sha256_file(artifact_path),
            "bytes": artifact_path.stat().st_size,
            "recorded_at": _now_iso(),
        }
    )
    return save_manifest(project_dir, run_id, manifest)


def close_run(project_dir: Path, run_id: str, status: str) -> dict:
    manifest = load_manifest(project_dir, run_id)
    manifest["status"] = status
    manifest["finished_at"] = _now_iso()
    return save_manifest(project_dir, run_id, manifest)


def replay_run(project_dir: Path, run_id: str) -> dict:
    manifest = load_manifest(project_dir, run_id)
    replay_path = Path(project_dir) / ".machine" / "runs" / run_id / "replay.json"
    replay_payload = {
        "run_id": run_id,
        "mode": manifest.get("mode"),
        "status": manifest.get("status"),
        "project": manifest.get("project"),
        "artifacts": manifest.get("artifacts", []),
    }
    replay_path.write_text(json.dumps(replay_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return replay_payload
