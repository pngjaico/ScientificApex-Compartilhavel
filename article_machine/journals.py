from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path
import re
from typing import Any
import yaml

from .evidence import validate_evidence_lock
from .serialization import load_structured_file, save_structured_file


REQUIRED_JOURNAL_KEYS = [
    "journal_id",
    "title",
    "issn",
    "publisher",
    "society",
    "domains",
    "tier",
    "indexing",
    "metrics",
    "article_types",
    "scope_fit",
    "format_rules",
    "open_access",
    "apc",
    "turnaround",
    "source_urls",
    "last_verified_at",
    "verification_status",
    "red_flags",
]

ALLOWED_TIERS = {"A", "B", "C"}
ALLOWED_VERIFICATION_STATUS = {"verified", "seeded-needs-refresh", "unverified"}
FRESHNESS_DAYS = 365

DOMAIN_TERMS = {
    "plastic-surgery": ("plastic", "reconstructive", "aesthetic", "craniofacial", "microsurgery", "breast"),
    "general-surgery": ("surgery", "surgical", "operative", "general surgery"),
    "transplant": ("transplant", "graft", "donor", "recipient", "liver transplant", "kidney transplant"),
    "digestive-surgery": ("gastrointestinal surgery", "digestive", "colorectal", "endoscopy", "colon", "rectum", "visceral"),
    "gastroenterology": ("gastroenterology", "hepatology", "endoscopy", "intestinal", "gut", "digestive"),
}

ARTICLE_TYPE_TERMS = {
    "network-meta-analysis": ("meta-analysis", "systematic review", "review"),
    "systematic-review": ("systematic review", "meta-analysis", "review"),
    "diagnostic-study": ("diagnostic accuracy", "original research", "clinical study"),
    "observational-study": ("original research", "cohort", "registry"),
    "clinical-trial": ("clinical trial", "original research"),
    "thesis-chapter": ("review", "original research", "methods"),
}


def _presets_dir(presets_dir: Path | None = None) -> Path:
    return Path(presets_dir) if presets_dir else Path(__file__).resolve().parent / "journal_presets"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(str(value))
        except ValueError:
            return None


def _days_since(value: str) -> int | None:
    parsed = _parse_date(value)
    if parsed is None:
        return None
    return (date.today() - parsed).days


def load_journal_presets(presets_dir: Path | None = None) -> list[dict[str, Any]]:
    root = _presets_dir(presets_dir)
    journals: list[dict[str, Any]] = []
    if not root.exists():
        return journals

    for preset_file in sorted(root.glob("*.yaml")):
        payload = _load_preset_file(preset_file)
        if payload.get("journal_id"):
            payload["_preset_file"] = preset_file.name
            journals.append(payload)
            continue
        entries = payload.get("journals", [])
        if isinstance(entries, list):
            for entry in entries:
                if isinstance(entry, dict):
                    entry = dict(entry)
                    entry["_preset_file"] = preset_file.name
                    journals.append(entry)
        elif payload.get("journal_id"):
            payload["_preset_file"] = preset_file.name
            journals.append(payload)
    return journals


def _load_preset_file(path: Path) -> dict[str, Any]:
    # PyYAML is a required dependency. A malformed document must not be
    # reinterpreted by the old permissive subset parser as a passing preset.
    payload = load_structured_file(path)
    if not payload or (not payload.get("journal_id") and not isinstance(payload.get("journals"), list)):
        raise ValueError(f"Malformed or empty journal preset: {path.name}")
    return payload


def validate_journal_preset(journal: dict[str, Any], today: date | None = None) -> list[str]:
    today = today or date.today()
    issues: list[str] = []
    label = str(journal.get("journal_id") or journal.get("title") or "<unknown>")

    for key in REQUIRED_JOURNAL_KEYS:
        if key not in journal:
            issues.append(f"{label}: missing required key '{key}'.")

    if journal.get("tier") not in ALLOWED_TIERS:
        issues.append(f"{label}: tier must be one of {sorted(ALLOWED_TIERS)}.")

    verification_status = journal.get("verification_status")
    if verification_status not in ALLOWED_VERIFICATION_STATUS:
        issues.append(f"{label}: verification_status must be one of {sorted(ALLOWED_VERIFICATION_STATUS)}.")

    source_urls = journal.get("source_urls")
    if not isinstance(source_urls, list) or not source_urls:
        issues.append(f"{label}: source_urls must be a non-empty list.")

    if not _parse_date(str(journal.get("last_verified_at") or "")):
        issues.append(f"{label}: last_verified_at must be an ISO date.")

    if verification_status == "verified":
        if not source_urls:
            issues.append(f"{label}: verified presets require source_urls.")
        if not journal.get("last_verified_at"):
            issues.append(f"{label}: verified presets require last_verified_at.")
        verified_at = _parse_date(str(journal.get("last_verified_at") or ""))
        if verified_at and (today - verified_at).days > FRESHNESS_DAYS:
            issues.append(f"{label}: verified metrics are stale; refresh before journal routing.")

    metrics = journal.get("metrics")
    if not isinstance(metrics, dict):
        issues.append(f"{label}: metrics must be an object.")
    else:
        metric_year = metrics.get("impact_factor_year")
        if metric_year is not None and int(metric_year) < today.year - 2:
            issues.append(f"{label}: impact_factor_year is stale for current routing.")
        if metrics.get("impact_factor") is not None and not metrics.get("source"):
            issues.append(f"{label}: impact_factor requires metrics.source.")

    for list_key in ["domains", "indexing", "article_types", "red_flags"]:
        if list_key in journal and not isinstance(journal.get(list_key), list):
            issues.append(f"{label}: {list_key} must be a list.")

    for object_key in ["format_rules", "open_access", "apc", "turnaround"]:
        if object_key in journal and not isinstance(journal.get(object_key), dict):
            issues.append(f"{label}: {object_key} must be an object.")

    return issues


def verify_journal_presets(presets_dir: Path | None = None) -> dict[str, Any]:
    try:
        journals = load_journal_presets(presets_dir)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return {"status": "block", "preset_dir": str(_presets_dir(presets_dir)), "journal_count": 0,
                "red_flagged_journals": [], "issues": [str(exc)]}
    issues: list[str] = []
    if not journals:
        issues.append("No journal presets were found; journal verification is blocked.")
    seen_ids: set[str] = set()
    red_flagged: list[str] = []
    for journal in journals:
        journal_id = str(journal.get("journal_id") or "")
        if journal_id in seen_ids:
            issues.append(f"{journal_id}: duplicate journal_id.")
        seen_ids.add(journal_id)
        if journal.get("red_flags"):
            red_flagged.append(journal_id)
        issues.extend(validate_journal_preset(journal))

    return {
        "status": "pass" if not issues else "block",
        "preset_dir": str(_presets_dir(presets_dir)),
        "journal_count": len(journals),
        "red_flagged_journals": red_flagged,
        "issues": issues,
    }


def catalog_journals(
    domain: str | None = None,
    tier: str | None = None,
    presets_dir: Path | None = None,
) -> dict[str, Any]:
    journals = load_journal_presets(presets_dir)
    if domain:
        journals = [journal for journal in journals if domain in journal.get("domains", [])]
    if tier:
        journals = [journal for journal in journals if str(journal.get("tier")) == tier]

    public_journals = [_public_journal_payload(journal) for journal in journals]
    return {
        "status": "available",
        "journal_count": len(public_journals),
        "journals": public_journals,
    }


def _public_journal_payload(journal: dict[str, Any]) -> dict[str, Any]:
    return {
        "journal_id": journal.get("journal_id"),
        "title": journal.get("title"),
        "domains": journal.get("domains", []),
        "tier": journal.get("tier"),
        "verification_status": journal.get("verification_status"),
        "impact_factor": journal.get("metrics", {}).get("impact_factor"),
        "impact_factor_year": journal.get("metrics", {}).get("impact_factor_year"),
        "last_verified_at": journal.get("last_verified_at"),
        "red_flags": journal.get("red_flags", []),
    }


def _text_for_project(project_dir: Path) -> str:
    project = load_structured_file(project_dir / "project.yaml")
    protocol = load_structured_file(project_dir / "protocol.yaml")
    manuscript_path = project_dir / "drafts" / "manuscript.md"
    manuscript = manuscript_path.read_text(encoding="utf-8") if manuscript_path.exists() else ""
    parts = [
        str(project.get("name", "")),
        str(project.get("project_type", "")),
        str(project.get("type", "")),
        str(project.get("description", "")),
        " ".join(str(tag) for tag in project.get("tags", [])),
        str(protocol.get("research_question", "")),
        str(protocol.get("hypothesis", "")),
        manuscript[:4000],
    ]
    return _normalize_text(" ".join(parts))


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).lower()).strip()


def _infer_project_domains(project_text: str) -> set[str]:
    domains: set[str] = set()
    for domain, terms in DOMAIN_TERMS.items():
        if any(term in project_text for term in terms):
            domains.add(domain)
    if "network meta-analysis" in project_text or "meta-analysis" in project_text:
        domains.add("gastroenterology")
        domains.add("digestive-surgery")
    return domains


def _scope_score(project_domains: set[str], journal: dict[str, Any]) -> int:
    journal_domains = set(journal.get("domains", []))
    overlap = project_domains & journal_domains
    if not project_domains:
        return 10
    if overlap:
        return min(25, 12 + 7 * len(overlap))
    return 4


def _methodology_score(project_type: str, journal: dict[str, Any]) -> int:
    project_type = project_type.strip().lower()
    wanted_terms = ARTICLE_TYPE_TERMS.get(project_type, ("original research", "review"))
    article_types = " ".join(str(item).lower() for item in journal.get("article_types", []))
    if any(term in article_types for term in wanted_terms):
        return 20
    if "original research" in article_types:
        return 14
    if "review" in article_types:
        return 11
    return 6


def _tier_score(journal: dict[str, Any]) -> int:
    return {"A": 15, "B": 11, "C": 7}.get(str(journal.get("tier")), 0)


def _readiness_score(evidence_status: str, project_dir: Path) -> int:
    manuscript_path = project_dir / "drafts" / "manuscript.md"
    if evidence_status == "pass":
        return 10
    if manuscript_path.exists() and manuscript_path.read_text(encoding="utf-8").strip():
        return 2
    return 0


def _cost_time_score(journal: dict[str, Any]) -> int:
    red_flags = journal.get("red_flags", [])
    if red_flags:
        return 1
    apc = journal.get("apc", {})
    if apc.get("amount_usd") in {None, 0, "unknown"}:
        return 5
    return 3


def _score_journal(project_dir: Path, journal: dict[str, Any], evidence_status: str) -> dict[str, Any]:
    project = load_structured_file(project_dir / "project.yaml")
    project_text = _text_for_project(project_dir)
    project_domains = _infer_project_domains(project_text)
    project_type = str(project.get("project_type") or project.get("type") or "")

    components = {
        "scope": _scope_score(project_domains, journal),
        "methodology": _methodology_score(project_type, journal),
        "evidence_strength": 15 if evidence_status == "pass" else 0,
        "tier_indexing": _tier_score(journal),
        "readiness": _readiness_score(evidence_status, project_dir),
        "author_fit": 5,
        "cost_time": _cost_time_score(journal),
    }
    score = sum(components.values())
    return {
        "journal_id": journal.get("journal_id"),
        "title": journal.get("title"),
        "tier": journal.get("tier"),
        "domains": journal.get("domains", []),
        "score": score,
        "score_components": components,
        "verification_status": journal.get("verification_status"),
        "impact_factor": journal.get("metrics", {}).get("impact_factor"),
        "red_team_notes": [
            "Do not submit here until Evidence Lock and journal-specific author instructions are current.",
            "Author fit is deliberately capped at medium weight unless ORCID/PubMed evidence is verified.",
        ],
    }


def _verification_rank(value: str | None) -> int:
    return {"verified": 0, "seeded-needs-refresh": 1, "unverified": 2}.get(str(value), 3)


def _fallback_ladder(scored: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    ladder: dict[str, list[dict[str, Any]]] = {"A": [], "B": [], "C": []}
    for tier in ladder:
        ladder[tier] = [item for item in scored if item["tier"] == tier][:3]
    return ladder


def route_journals(
    project_dir: Path,
    domain: str | None = None,
    limit: int = 10,
    presets_dir: Path | None = None,
) -> dict[str, Any]:
    project_dir = Path(project_dir)
    verify_report = verify_journal_presets(presets_dir)
    if verify_report["status"] != "pass":
        return {"status": "blocked", "issues": verify_report["issues"], "ranked_journals": []}

    journals = load_journal_presets(presets_dir)
    if domain:
        journals = [journal for journal in journals if domain in journal.get("domains", [])]

    evidence_report = validate_evidence_lock(project_dir)
    evidence_status = evidence_report["status"]
    scored = [_score_journal(project_dir, journal, evidence_status) for journal in journals]
    scored.sort(
        key=lambda item: (
            -item["score"],
            _verification_rank(item.get("verification_status")),
            -(item.get("impact_factor") or 0),
            item["tier"],
            item["title"],
        )
    )

    payload = {
        "status": "routed" if evidence_status == "pass" else "blocked",
        "project_dir": str(project_dir),
        "evidence_lock_status": evidence_status,
        "evidence_lock_issues": evidence_report["issues"],
        "ranked_journals": scored[:limit],
        "fallback_ladder": _fallback_ladder(scored),
        "red_team_notes": [
            "No journal recommendation is final without a fresh author-instructions check.",
            "Impact factor is not a quality guarantee; method fit and desk-reject risk must be reviewed.",
            "Predatory or journal-mimic risk must be checked before any portal submission.",
        ],
    }
    if evidence_status != "pass":
        payload["message"] = "Journal recommendation blocked until Evidence Lock passes."
    return payload


def write_journal_report(
    project_dir: Path,
    domain: str | None = None,
    presets_dir: Path | None = None,
) -> dict[str, Any]:
    project_dir = Path(project_dir)
    route_report = route_journals(project_dir, domain=domain, limit=15, presets_dir=presets_dir)
    report_path = project_dir / "analysis" / "journal_strategy_report.md"
    json_path = project_dir / "analysis" / "journal_strategy_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Journal Strategy Report",
        "",
        f"Generated at: {_now_iso()}",
        f"Status: {route_report['status']}",
        f"Evidence Lock: {route_report.get('evidence_lock_status', 'unknown')}",
        "",
        "## Gate",
    ]
    if route_report["status"] != "routed":
        lines.append("Journal recommendation is blocked until Evidence Lock passes.")
    else:
        lines.append("Evidence Lock passed; candidates are ranked but still require fresh author-instructions review.")

    lines.extend(["", "## Ranked Candidates"])
    for item in route_report.get("ranked_journals", []):
        lines.append(f"- {item['score']:03d} | Tier {item['tier']} | {item['title']} | {', '.join(item['domains'])}")

    lines.extend(["", "## Fallback Ladder"])
    for tier, items in route_report.get("fallback_ladder", {}).items():
        titles = ", ".join(item["title"] for item in items) or "none"
        lines.append(f"- Tier {tier}: {titles}")

    lines.extend(["", "## Red Team Notes"])
    for note in route_report.get("red_team_notes", []):
        lines.append(f"- {note}")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    save_structured_file(json_path, route_report)
    return {
        "status": route_report["status"],
        "report_path": str(report_path),
        "json_path": str(json_path),
        "route_report": route_report,
    }
