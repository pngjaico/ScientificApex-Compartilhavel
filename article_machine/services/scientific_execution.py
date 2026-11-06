"""Shared scientific entrypoint policy; standalone document utilities remain usable."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .protocol_registration import registration_gate


def scientific_execution_gate(project_dir: Path, action: str, *, mark_started: bool = False) -> dict[str, Any]:
    """Fail closed on missing/malformed contracts, without guessing an exemption."""
    try:
        return registration_gate(Path(project_dir), action, mark_started=mark_started)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, yaml.YAMLError) as exc:
        return {
            "contract": "ScientificExecutionGateV1",
            "status": "blocked",
            "required": True,
            "action": action,
            "issues": [f"Scientific project/registration could not be verified: {type(exc).__name__}."],
        }


def project_ancestor(path: Path) -> Path | None:
    """Discover a project from explicit input/output paths; never scan a corpus."""
    candidate = Path(path).resolve()
    for parent in (candidate, *candidate.parents):
        if (parent / "project.yaml").is_file():
            return parent
    return None
