"""Inspect installed scientific plugin packages without network calls or uploads."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .skill_registry import resolve_plugin_binding, workspace_root

PLUGIN_CAPABILITIES = {
    "life-sciences-literature": ("literature", "pubmed-database", "literature-search-europepmc"),
    "life-sciences-databases": ("biomedical databases", "life-science-router", "database-lookup"),
    "life-science-research": ("biomedical discovery", "life-science-router", "database-lookup"),
    "ngs-analysis": ("sequencing", "ngs-analysis-router", "nextflow-pipeline-runner"),
    "zotero": ("references and attachments", "zotero-reference-manager", "citation-management"),
    "science": ("scientific research & discovery", "life-science-router", "biomolecular_structure_viewer"),
}


def discover_plugin_candidates(plugin_id: str, cache_root: Path | None = None) -> list[Path]:
    codex_root = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    cache = cache_root or codex_root / "plugins" / "cache"
    candidates: list[Path] = []
    for provider in sorted(cache.iterdir()) if cache.is_dir() else []:
        folder = provider / plugin_id
        if not folder.is_dir():
            continue
        if (folder / "skills").is_dir():
            candidates.append(folder)
        candidates.extend(
            version for version in sorted(folder.iterdir()) if version.is_dir() and (version / "skills").is_dir()
        )

    # Also discover Google Antigravity installed plugins
    ag_root = Path(os.environ.get("ANTIGRAVITY_PLUGINS", str(Path.home() / ".gemini" / "config" / "plugins")))
    if ag_root.is_dir():
        ag_folder = ag_root / plugin_id
        if ag_folder.is_dir() and (ag_folder / "skills").is_dir():
            candidates.append(ag_folder)
        elif plugin_id in ("life-science-research", "science"):
            science_dir = ag_root / "science"
            if science_dir.is_dir() and (science_dir / "skills").is_dir() and science_dir not in candidates:
                candidates.append(science_dir)

    return candidates


def resolve_scientific_plugin(plugin_id: str, root: Path | None = None) -> Path:
    """Use explicit binding or the sole detected package, never newest-by-mtime."""
    base = root or workspace_root()
    binding_file = base / ".machine" / "plugin_bindings.json"
    if binding_file.is_file():
        import json

        bindings = json.loads(binding_file.read_text(encoding="utf-8"))
        if plugin_id in bindings.get("bindings", {}):
            binding = resolve_plugin_binding(plugin_id, base)
            package = Path(binding["root"])
            if not (package / "skills").is_dir():
                raise ValueError(f"plugin {plugin_id} binding lacks a skills directory")
            return package
    candidates = discover_plugin_candidates(plugin_id)
    if len(candidates) != 1:
        raise ValueError(
            f"plugin {plugin_id} has {len(candidates)} installed candidates; an explicit binding is required"
        )
    return candidates[0]


def audit_scientific_plugins(root: Path | None = None) -> dict[str, Any]:
    items = []
    for plugin_id, (capability, bridge, fallback) in PLUGIN_CAPABILITIES.items():
        try:
            package = resolve_scientific_plugin(plugin_id, root)
            item = {
                "id": plugin_id,
                "status": "available-local",
                "version": package.name,
                "skill_count": len(list((package / "skills").glob("*/SKILL.md"))),
                "package_path": str(package),
                "issues": [],
            }
        except (OSError, ValueError) as exc:
            item = {"id": plugin_id, "status": "unavailable-or-ambiguous", "issues": [str(exc)]}
        item.update(
            capability=capability,
            bridge=bridge,
            fallback=fallback,
            required_for_core=False,
            credentials_verified=False,
            live_calls_verified=False,
            human_data_upload_authorized=False,
        )
        items.append(item)
    return {
        "contract": "ScientificPluginAuditV1",
        "status": "inspected",
        "plugins": items,
        "limits": [
            "local package availability does not establish authentication, network access or scientific accuracy"
        ],
    }
