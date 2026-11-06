from __future__ import annotations

from pathlib import Path

from .serialization import load_structured_file, save_structured_file


REQUIRED_CONFERENCE_KEYS = [
    "schema_version",
    "event_name",
    "kind",
    "profile",
    "source",
    "presentation",
    "limits",
    "dimensions",
    "requirements_confidence",
]

REQUIRED_STORYBOARD_KEYS = [
    "schema_version",
    "status",
    "kind",
    "profile",
    "approved_claim_ids",
    "scenes",
    "assets",
]

REQUIRED_THEME_KEYS = [
    "schema_version",
    "name",
    "html_first",
    "palette",
    "typography",
    "accessibility",
    "branding",
]


def _missing_keys(payload: dict, required: list[str], label: str) -> list[str]:
    return [f"{label} is missing required key '{key}'." for key in required if key not in payload]


def validate_deliverable_contract(deliverable_dir: Path, strict: bool = False) -> dict:
    deliverable_dir = Path(deliverable_dir)
    conference = load_structured_file(deliverable_dir / "conference.yaml")
    storyboard = load_structured_file(deliverable_dir / "storyboard.yaml")
    theme = load_structured_file(deliverable_dir / "theme.yaml")
    qa_report = load_structured_file(deliverable_dir / "qa_report.json")
    issues: list[str] = []

    issues.extend(_missing_keys(conference, REQUIRED_CONFERENCE_KEYS, "conference.yaml"))
    issues.extend(_missing_keys(storyboard, REQUIRED_STORYBOARD_KEYS, "storyboard.yaml"))
    issues.extend(_missing_keys(theme, REQUIRED_THEME_KEYS, "theme.yaml"))

    if conference.get("kind") not in {"deck", "poster", "abstract"}:
        issues.append("conference.yaml kind must be deck, poster, or abstract.")
    if theme.get("html_first") is not True:
        issues.append("theme.yaml must declare html_first: true.")
    if not isinstance(storyboard.get("scenes", []), list):
        issues.append("storyboard.yaml scenes must be a list.")
    if not isinstance(storyboard.get("assets", []), list):
        issues.append("storyboard.yaml assets must be a list.")

    confidence = conference.get("requirements_confidence", {})
    if strict and confidence.get("status") != "pass":
        issues.append(
            "Strict export blocked because requirements confidence is not pass. "
            "Import clearer congress rules or disable strict export."
        )
    if qa_report and qa_report.get("status") not in {"pending", "pass", "block"}:
        issues.append("qa_report.json status must be pending, pass, or block.")

    report = {
        "status": "pass" if not issues else "block",
        "strict": strict,
        "issues": issues,
        "files_checked": [
            "conference.yaml",
            "storyboard.yaml",
            "theme.yaml",
            "qa_report.json",
        ],
    }
    save_structured_file(deliverable_dir / "contract_report.json", report)
    return report
