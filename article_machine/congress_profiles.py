from __future__ import annotations

from pathlib import Path

from .serialization import load_structured_file, save_structured_file


def _profiles_dir_from_project(project_dir: Path) -> Path:
    project_dir = Path(project_dir)
    return project_dir.parent / ".machine" / "congress_profiles"


def _profiles_dir_from_deliverable(deliverable_dir: Path) -> Path:
    deliverable_dir = Path(deliverable_dir)
    return _profiles_dir_from_project(deliverable_dir.parent.parent)


def save_congress_profile(deliverable_dir: Path, profile_name: str) -> dict:
    deliverable_dir = Path(deliverable_dir)
    profile_slug = profile_name.strip().lower().replace(" ", "-")
    if not profile_slug:
        return {"status": "blocked", "message": "profile_name cannot be empty."}

    conference = load_structured_file(deliverable_dir / "conference.yaml")
    theme = load_structured_file(deliverable_dir / "theme.yaml")
    profile = {
        "schema_version": 1,
        "profile_name": profile_slug,
        "source_deliverable": str(deliverable_dir),
        "conference": conference,
        "theme": theme,
    }
    profile_path = _profiles_dir_from_deliverable(deliverable_dir) / f"{profile_slug}.yaml"
    save_structured_file(profile_path, profile)
    return {"status": "saved", "profile": profile_slug, "path": str(profile_path)}


def use_congress_profile(project_dir: Path, profile_name: str, slug: str) -> dict:
    project_dir = Path(project_dir)
    profile_slug = profile_name.strip().lower().replace(" ", "-")
    profile_path = _profiles_dir_from_project(project_dir) / f"{profile_slug}.yaml"
    profile = load_structured_file(profile_path)
    if not profile:
        return {"status": "blocked", "message": f"Congress profile '{profile_slug}' was not found."}

    deliverable_dir = project_dir / "deliverables" / slug
    for rel in ["assets", "layouts", "exports", "qa", "submission", "submission_pack"]:
        (deliverable_dir / rel).mkdir(parents=True, exist_ok=True)

    conference = profile.get("conference", {})
    conference["source"] = {
        **conference.get("source", {}),
        "profile_name": profile_slug,
        "profile_path": str(profile_path),
    }
    save_structured_file(deliverable_dir / "conference.yaml", conference)
    save_structured_file(deliverable_dir / "theme.yaml", profile.get("theme", {}))
    save_structured_file(
        deliverable_dir / "storyboard.yaml",
        {
            "schema_version": 1,
            "status": "imported",
            "kind": conference.get("kind", "deck"),
            "profile": conference.get("profile", "10-min"),
            "claim_policy": "only evidence/claim_map.jsonl entries with status=supported may appear",
            "approved_claim_ids": [],
            "scenes": [],
            "assets": [],
        },
    )
    save_structured_file(
        deliverable_dir / "qa_report.json",
        {
            "status": "pending",
            "issues": [],
            "checks": {
                "claim_safe_visuals": "pending",
                "layout": "pending",
                "playwright": "pending",
                "export": "pending",
            },
        },
    )
    save_structured_file(
        deliverable_dir / "manifest.json",
        {
            "schema_version": 1,
            "deliverable_id": slug,
            "kind": conference.get("kind", "deck"),
            "profile_source": str(profile_path),
            "state": {
                "current_stage": "brief-import",
                "stage_history": ["brief-import"],
                "allowed_next_stages": ["storyboard-lock"],
            },
            "artifacts": [],
            "exports": [],
        },
    )
    return {"status": "created", "deliverable_dir": str(deliverable_dir), "profile": profile_slug}
