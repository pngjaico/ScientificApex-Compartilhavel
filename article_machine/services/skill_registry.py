"""Deterministic skill provenance and plugin binding checks.

The registry is deliberately data-first: routing remains compatible with the
existing hand-maintained rules, while promotion to a critical capability is
audited from a complete on-disk tree rather than a single ``SKILL.md`` file.
"""

from __future__ import annotations

import json
from datetime import date
from hashlib import sha256
from pathlib import Path
from typing import Any

REGISTRY_SCHEMA_VERSION = 1
REQUIRED_PROVENANCE = {
    "origin",
    "pinned_revision",
    "license",
    "tree_hash",
    "dependencies",
    "credentials",
    "network_domains",
    "human_data_policy",
    "routes",
    "artifact_destination",
    "status",
    "next_review",
}


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[2]


def registry_path(root: Path | None = None) -> Path:
    base = root or workspace_root()
    return base / "skills" / "registry.json"


def plugin_bindings_path(root: Path | None = None) -> Path:
    base = root or workspace_root()
    return base / ".machine" / "plugin_bindings.json"


def tree_hash(path: Path) -> str:
    """Hash paths and bytes; canonicalize Git text line endings for portability."""

    digest = sha256()
    if not path.is_dir():
        return ""
    for child in sorted((item for item in path.rglob("*") if item.is_file()), key=lambda item: item.as_posix()):
        relative = child.relative_to(path).as_posix()
        if "__pycache__" in child.relative_to(path).parts or child.suffix in {".pyc", ".pyo"}:
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        content = child.read_bytes()
        # Git also normalizes extensionless instructions and text templates.
        # Binary bytes remain exact; only valid, NUL-free UTF-8 is canonicalized.
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            pass
        else:
            if b"\0" not in content:
                content = content.replace(b"\r\n", b"\n")
        digest.update(content)
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def load_registry(root: Path | None = None) -> dict[str, Any]:
    path = registry_path(root)
    if not path.exists():
        return {"schema_version": REGISTRY_SCHEMA_VERSION, "skills": {}}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("skills"), dict):
        raise ValueError(f"invalid skill registry: {path}")
    return payload


def _tree_contains_absolute_cache(skill_dir: Path) -> bool:
    markers = (".codex\\plugins\\cache", ".codex/plugins/cache")
    for file_path in skill_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in {".md", ".json", ".yaml", ".yml", ".toml", ".py"}:
            try:
                value = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if any(marker.lower() in value.lower() for marker in markers):
                return True
    return False


def audit_skill_provenance(
    skills_dir: Path | None = None,
    *,
    root: Path | None = None,
    strict: bool = False,
) -> dict[str, Any]:
    """Audit registry provenance and the complete tree of active skills.

    ``strict`` makes an unregistered installed skill a blocker. Non-strict
    mode remains useful during migration and reports it as an issue.
    """

    base = root or workspace_root()
    skill_root = skills_dir or base / "skills"
    registry = load_registry(base)
    entries = registry.get("skills", {})
    issues: list[str] = []
    checked: list[str] = []
    for skill_md in sorted(skill_root.glob("*/SKILL.md")):
        name = skill_md.parent.name
        checked.append(name)
        entry = entries.get(name)
        if not entry:
            issues.append(f"{name}: missing registry entry")
            continue
        missing = sorted(field for field in REQUIRED_PROVENANCE if field not in entry)
        if missing:
            issues.append(f"{name}: missing provenance fields: {', '.join(missing)}")
            continue
        actual_hash = tree_hash(skill_md.parent)
        if entry["tree_hash"] != actual_hash:
            issues.append(f"{name}: tree hash mismatch")
        if _tree_contains_absolute_cache(skill_md.parent):
            issues.append(f"{name}: absolute plugin-cache path present")
        if entry.get("status") == "active":
            origin = entry.get("origin") or {}
            if not isinstance(origin, dict) or not origin.get("url"):
                issues.append(f"{name}: active skill has no origin URL")
            if entry.get("license") in {None, "", "NOASSERTION"}:
                issues.append(f"{name}: active skill has no declared license")

    installed = set(checked)
    for name in sorted(set(entries) - installed):
        if entries[name].get("required_for_clone") or entries[name].get("status") == "active":
            issues.append(f"{name}: required registry entry has no installed SKILL.md")
    if strict and installed - set(entries):
        issues.append("registry does not cover all installed skills")
    return {
        "status": "pass" if not issues else "block",
        "schema_version": registry.get("schema_version"),
        "checked_skill_count": len(checked),
        "registry_skill_count": len(entries),
        "strict": strict,
        "issues": issues,
    }


def resolve_plugin_binding(plugin_id: str, root: Path | None = None) -> dict[str, Any]:
    """Resolve exactly one explicit plugin binding; fail closed otherwise."""

    path = plugin_bindings_path(root)
    if not path.exists():
        raise ValueError(f"plugin bindings are absent: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    candidates = payload.get("bindings", {}).get(plugin_id, [])
    if not isinstance(candidates, list) or len(candidates) != 1:
        candidate_count = len(candidates) if isinstance(candidates, list) else 0
        raise ValueError(f"plugin '{plugin_id}' requires exactly one explicit binding; found {candidate_count}")
    binding = candidates[0]
    if not isinstance(binding, dict):
        raise ValueError(f"plugin '{plugin_id}' binding must be an object")
    root_value = Path(str(binding.get("root", "")))
    if not root_value.is_dir():
        raise ValueError(f"plugin '{plugin_id}' binding root is unavailable: {root_value}")
    return dict(binding)


def build_skill_update_plan(root: Path | None = None) -> dict[str, Any]:
    """Return a review plan from registry state without installing anything."""

    base = root or workspace_root()
    registry = load_registry(base)
    today = date.today().isoformat()
    items: list[dict[str, Any]] = []
    for name, entry in sorted(registry.get("skills", {}).items()):
        status = entry.get("status")
        review_due = str(entry.get("next_review") or "") <= today
        if status in {"pilot", "quarantine"} or review_due:
            items.append(
                {
                    "skill": name,
                    "status": status,
                    "pinned_revision": entry.get("pinned_revision"),
                    "next_review": entry.get("next_review"),
                    "review_due": review_due,
                    "action": (
                        "benchmark-before-promotion"
                        if status == "pilot"
                        else "keep-isolated-pending-benchmark"
                        if status == "quarantine"
                        else "review-provenance-and-diff"
                    ),
                }
            )
    provenance = audit_skill_provenance(root=base, strict=True)
    return {
        "contract": "SkillUpdatePlanV2",
        "status": "pass" if provenance["status"] == "pass" else "block",
        "generated_from": str(registry_path(base)),
        "install_authorized": False,
        "bulk_sync_authorized": False,
        "items": items,
        "provenance_audit": provenance,
    }
