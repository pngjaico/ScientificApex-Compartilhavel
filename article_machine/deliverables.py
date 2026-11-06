from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import html
import json
import mimetypes
from pathlib import Path
import re
import shutil
from urllib.parse import urlparse

from .evidence import BIB_PATTERN
from . import playwright_ops, pptx_bridge
from .deliverable_contracts import validate_deliverable_contract
from .projects import slugify_project_name
from .serialization import load_structured_file, save_structured_file
from .visuals import route_visual_backend


DELIVERABLE_STAGES = [
    "brief-import",
    "storyboard-lock",
    "asset-build",
    "layout-build",
    "qa",
    "export",
    "submission-dry-run",
    "submission-run",
]

ORAL_PROFILES = {
    "3-min": {"duration_minutes": 3, "max_slides": 4, "target_slides": 3},
    "5-min": {"duration_minutes": 5, "max_slides": 6, "target_slides": 5},
    "10-min": {"duration_minutes": 10, "max_slides": 10, "target_slides": 8},
    "15-min": {"duration_minutes": 15, "max_slides": 15, "target_slides": 12},
    "thesis-defense": {"duration_minutes": 40, "max_slides": 45, "target_slides": 35},
    "seminar": {"duration_minutes": 30, "max_slides": 30, "target_slides": 24},
}

POSTER_PROFILES = {
    "digital 16:9 landscape": {
        "orientation": "landscape",
        "format": "16:9-digital",
        "width_px": 1920,
        "height_px": 1080,
        "submission_hint": "one-page electronic poster in PowerPoint/PDF",
    },
    "A0 portrait": {"orientation": "portrait", "format": "A0", "width_mm": 841, "height_mm": 1189, "width_px": 1440, "height_px": 2036},
    "A0 landscape": {"orientation": "landscape", "format": "A0", "width_mm": 1189, "height_mm": 841, "width_px": 2036, "height_px": 1440},
    "36x48 portrait": {"orientation": "portrait", "format": "36x48", "width_in": 36, "height_in": 48, "width_px": 1440, "height_px": 1920},
    "48x36 landscape": {"orientation": "landscape", "format": "48x36", "width_in": 48, "height_in": 36, "width_px": 1920, "height_px": 1440},
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _save_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _record_artifact(deliverable_dir: Path, artifact_path: Path, role: str, export_version: str | None = None) -> dict:
    manifest_path = Path(deliverable_dir) / "manifest.json"
    manifest = load_structured_file(manifest_path)
    artifact_path = Path(artifact_path)
    rel_path = artifact_path.relative_to(deliverable_dir).as_posix()
    artifacts = manifest.setdefault("artifacts", [])
    artifact = {
        "path": rel_path,
        "role": role,
        "sha256": _sha256_file(artifact_path),
        "bytes": artifact_path.stat().st_size,
        "recorded_at": _now_iso(),
    }
    if export_version:
        artifact["export_version"] = export_version
    artifacts[:] = [existing for existing in artifacts if existing.get("path") != rel_path]
    artifacts.append(artifact)
    manifest["updated_at"] = _now_iso()
    _save_json(manifest_path, manifest)
    return manifest


def _project_dir_from_deliverable(deliverable_dir: Path) -> Path:
    deliverable_dir = Path(deliverable_dir)
    if deliverable_dir.parent.name != "deliverables":
        raise ValueError("deliverable_dir must be projects/<project_id>/deliverables/<slug>.")
    return deliverable_dir.parent.parent


def _source_kind(source: str) -> str:
    source_text = str(source)
    if re.match(r"^https?://", source_text, flags=re.I):
        return "url"
    path = Path(source_text)
    if path.exists():
        suffix = path.suffix.lower().lstrip(".")
        return suffix or "file"
    if source_text.strip().lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        return "screenshot"
    return "text"


def _read_source_text(source: str) -> str:
    source_type = _source_kind(source)
    if source_type in {"url", "screenshot", "pdf"}:
        return str(source)
    path = Path(str(source))
    if path.exists():
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return str(source)
    return str(source)


def _event_name_from_source(source: str, text: str) -> str:
    heading = re.search(r"^\s*#\s+(.+?)\s*$", text, flags=re.M)
    if heading:
        return heading.group(1).strip()
    if re.match(r"^https?://", source, flags=re.I):
        parsed = urlparse(source)
        label = (parsed.netloc + " " + parsed.path.strip("/").replace("/", " ")).strip()
        return label or "Imported Conference"
    return "Imported Conference"


def _parse_duration_minutes(text: str) -> int | None:
    match = re.search(r"(\d{1,3})\s*(?:min|minutes|minuto|minutos)\b", text, flags=re.I)
    return int(match.group(1)) if match else None


def _parse_max_slides(text: str) -> int | None:
    patterns = [
        r"(?:maximum|max|up to|ate|até)\D{0,24}(\d{1,2})\s+slides?",
        r"(\d{1,2})\s+slides?\D{0,24}(?:maximum|max)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return int(match.group(1))
    return None


def _parse_abstract_words(text: str) -> int:
    match = re.search(r"(?:abstract\D{0,30})?(\d{2,4})\s+words?", text, flags=re.I)
    return int(match.group(1)) if match else 300


def _parse_deadline(text: str) -> str:
    match = re.search(r"(?:deadline|due|submission deadline)\D{0,20}(\d{4}-\d{2}-\d{2})", text, flags=re.I)
    return match.group(1) if match else ""


def _parse_portal_url(text: str) -> str:
    portal = re.search(r"(?:portal|submit|submission)\D{0,30}(https?://[^\s,)]+)", text, flags=re.I)
    if portal:
        return portal.group(1).rstrip(".,;")
    generic = re.search(r"https?://[^\s,)]+", text, flags=re.I)
    return generic.group(0).rstrip(".,;") if generic else ""


def _parse_accepted_file_types(text: str) -> list[str]:
    lower = text.lower()
    return [file_type for file_type in ["pdf", "pptx", "ppt", "html", "docx", "png", "jpg"] if re.search(rf"\b{file_type}\b", lower)]


def _requirements_confidence(text: str, kind: str, profile: str, source_type: str) -> dict:
    signals = {
        "kind": kind in {"deck", "poster", "abstract"},
        "profile": bool(profile),
        "duration": _parse_duration_minutes(text) is not None or kind == "poster",
        "slide_limit": _parse_max_slides(text) is not None or kind == "poster",
        "poster_size": kind != "poster" or bool(re.search(r"\b(?:a0|36\s*x\s*48|48\s*x\s*36)\b", text, flags=re.I)),
        "abstract_limit": re.search(r"\d{2,4}\s+words?", text, flags=re.I) is not None,
        "file_types": bool(_parse_accepted_file_types(text)),
        "deadline": bool(_parse_deadline(text)),
        "source_text": source_type in {"text", "md", "markdown", "url"},
    }
    score = round(sum(1 for value in signals.values() if value) / len(signals), 2)
    return {
        "score": score,
        "status": "pass" if score >= 0.65 else "needs-review",
        "signals": signals,
        "missing": [key for key, value in signals.items() if not value],
    }


def _profile_for_deck(text: str, profile: str | None) -> str:
    if profile:
        return profile
    duration = _parse_duration_minutes(text)
    if duration is None:
        return "10-min"
    if duration <= 3:
        return "3-min"
    if duration <= 5:
        return "5-min"
    if duration <= 10:
        return "10-min"
    return "15-min"


def _profile_for_poster(text: str, profile: str | None) -> str:
    if profile:
        return profile
    lower = text.lower()
    if any(term in lower for term in ["electronic poster", "e-poster", "powerpoint", "one-page electronic poster", "digital poster"]):
        return "digital 16:9 landscape"
    if "48x36" in lower or ("48 x 36" in lower):
        return "48x36 landscape"
    if "36x48" in lower or ("36 x 48" in lower):
        return "36x48 portrait"
    if "a0" in lower and any(term in lower for term in ["landscape", "horizontal"]):
        return "A0 landscape"
    if "a0" in lower or "portrait" in lower or "vertical" in lower:
        return "A0 portrait"
    return "digital 16:9 landscape"


def _conference_payload(
    project_dir: Path,
    source: str,
    text: str,
    kind: str,
    profile: str | None,
    authors: list[str] | None = None,
    affiliations: list[str] | None = None,
    qr_url: str = "",
    logos: list[str] | None = None,
) -> dict:
    normalized_kind = (kind or "deck").strip().lower()
    if normalized_kind not in {"deck", "poster", "abstract"}:
        normalized_kind = "deck"

    event_name = _event_name_from_source(source, text)
    source_type = _source_kind(source)
    if normalized_kind == "poster":
        selected_profile = _profile_for_poster(text, profile)
        dimensions = POSTER_PROFILES.get(selected_profile, POSTER_PROFILES["A0 portrait"])
        limits = {
            "max_slides": None,
            "max_words_abstract": _parse_abstract_words(text),
            "max_words_per_block": 90,
            "min_font_px": 24,
        }
        presentation = {"duration_minutes": None, "target_slides": None}
    else:
        selected_profile = _profile_for_deck(text, profile)
        defaults = ORAL_PROFILES.get(selected_profile, ORAL_PROFILES["10-min"])
        max_slides = _parse_max_slides(text) or defaults["max_slides"]
        duration = _parse_duration_minutes(text) or defaults["duration_minutes"]
        dimensions = {"orientation": "landscape", "format": "16:9", "width_px": 1920, "height_px": 1080}
        limits = {
            "max_slides": max_slides,
            "max_words_abstract": _parse_abstract_words(text),
            "max_words_per_slide": 42,
            "min_font_px": 24,
        }
        presentation = {"duration_minutes": duration, "target_slides": min(defaults["target_slides"], max_slides)}

    portal_url = _parse_portal_url(text)
    if source_type == "url" and not portal_url:
        portal_url = source
    return {
        "schema_version": 1,
        "event_name": event_name,
        "kind": normalized_kind,
        "profile": selected_profile,
        "deadline": _parse_deadline(text),
        "accepted_file_types": _parse_accepted_file_types(text),
        "requirements_confidence": _requirements_confidence(text, normalized_kind, selected_profile, source_type),
        "source": {
            "type": source_type,
            "value": source,
            "imported_at": _now_iso(),
            "project_dir": str(project_dir),
        },
        "presentation": presentation,
        "limits": limits,
        "dimensions": dimensions,
        "logos": {"required": "logo" in text.lower(), "files": logos or []},
        "authors": authors or [],
        "affiliations": affiliations or [],
        "qr": {"url": qr_url, "label": "Project resources"},
        "submission": {
            "portal_url": portal_url,
            "requires_human_confirmation": True,
        },
        "requirements_text": text[:8000],
        "requirements": [
            line.strip()
            for line in text.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ][:40],
    }


def _theme_payload(kind: str, conference: dict | None = None) -> dict:
    min_font = 24
    conference = conference or {}
    return {
        "schema_version": 1,
        "name": "agent-native-conference",
        "html_first": True,
        "palette": {
            "ink": "#15211f",
            "paper": "#f7f2e8",
            "accent": "#0d6b5f",
            "accent_2": "#9b3f00",
            "muted": "#5d6b66",
        },
        "typography": {
            "display": "Aptos Display, Georgia, serif",
            "body": "Aptos, Calibri, sans-serif",
            "mono": "Cascadia Mono, Consolas, monospace",
        },
        "accessibility": {
            "min_font_px": min_font,
            "target_contrast_ratio": 4.5,
            "max_words_per_slide": 42,
            "max_words_per_poster_block": 90,
        },
        "branding": {
            "authors": conference.get("authors", []),
            "affiliations": conference.get("affiliations", []),
            "logos": conference.get("logos", {}).get("files", []),
            "qr_url": conference.get("qr", {}).get("url", ""),
        },
        "motion": {
            "html": "staggered section reveals and subtle figure entrance animations",
            "pptx": "degrade complex motion to editable build-step slides",
        },
    }


def _initial_storyboard(kind: str, profile: str) -> dict:
    return {
        "schema_version": 1,
        "status": "imported",
        "kind": kind,
        "profile": profile,
        "claim_policy": "only approved claim-map entries may appear; legacy projects may use audit_top1/analysis_audit/claim_map.jsonl as fallback",
        "approved_claim_ids": [],
        "scenes": [],
        "assets": [],
    }


def _initial_qa_report() -> dict:
    return {
        "status": "pending",
        "issues": [],
        "checks": {
            "claim_safe_visuals": "pending",
            "layout": "pending",
            "playwright": "pending",
            "export": "pending",
        },
    }


def _initial_manifest(project_dir: Path, slug: str, kind: str) -> dict:
    project = load_structured_file(project_dir / "project.yaml")
    return {
        "schema_version": 1,
        "deliverable_id": slug,
        "kind": kind,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "project": {
            "id": project.get("id"),
            "name": project.get("name"),
            "project_type": project.get("project_type"),
        },
        "state": {
            "current_stage": "brief-import",
            "stage_history": ["brief-import"],
            "allowed_next_stages": ["storyboard-lock"],
        },
        "artifacts": [],
        "exports": [],
    }


def _advance_stage(deliverable_dir: Path, stage: str) -> dict:
    manifest_path = Path(deliverable_dir) / "manifest.json"
    manifest = load_structured_file(manifest_path)
    state = manifest.setdefault("state", {})
    history = state.setdefault("stage_history", [])
    if stage not in history:
        history.append(stage)
    state["current_stage"] = stage
    try:
        idx = DELIVERABLE_STAGES.index(stage)
        state["allowed_next_stages"] = DELIVERABLE_STAGES[idx + 1 : idx + 2]
    except ValueError:
        state["allowed_next_stages"] = []
    manifest["updated_at"] = _now_iso()
    _save_json(manifest_path, manifest)
    return manifest


def import_conference_requirements(
    project_dir: Path,
    source: str,
    kind: str = "deck",
    slug: str | None = None,
    profile: str | None = None,
    crawl: bool = False,
    authors: list[str] | None = None,
    affiliations: list[str] | None = None,
    qr_url: str = "",
    logos: list[str] | None = None,
) -> dict:
    project_dir = Path(project_dir)
    source_text = _read_source_text(source)
    crawl_report: dict | None = None
    if crawl and _source_kind(source) == "url":
        crawl_report = playwright_ops.extract_page_text(source, project_dir / "deliverables" / "_crawl")
        if crawl_report.get("status") == "pass":
            source_text = crawl_report.get("text", source_text)

    conference = _conference_payload(
        project_dir,
        source,
        source_text,
        kind,
        profile,
        authors=authors,
        affiliations=affiliations,
        qr_url=qr_url,
        logos=logos,
    )
    deliverable_slug = slug or slugify_project_name(f"{conference['event_name']} {conference['kind']}")
    deliverable_dir = project_dir / "deliverables" / deliverable_slug
    for rel in ["assets", "layouts", "exports", "qa", "submission", "submission_pack"]:
        (deliverable_dir / rel).mkdir(parents=True, exist_ok=True)

    save_structured_file(deliverable_dir / "conference.yaml", conference)
    save_structured_file(deliverable_dir / "storyboard.yaml", _initial_storyboard(conference["kind"], conference["profile"]))
    save_structured_file(deliverable_dir / "theme.yaml", _theme_payload(conference["kind"], conference))
    _save_json(deliverable_dir / "qa_report.json", _initial_qa_report())
    _save_json(deliverable_dir / "manifest.json", _initial_manifest(project_dir, deliverable_slug, conference["kind"]))

    report = {
        "status": "created",
        "deliverable_dir": str(deliverable_dir),
        "conference": str(deliverable_dir / "conference.yaml"),
        "profile": conference["profile"],
    }
    if crawl_report:
        report["crawl"] = crawl_report
    return report


def _load_bib_keys(project_dir: Path) -> set[str]:
    bib_path = Path(project_dir) / "drafts" / "references.bib"
    if not bib_path.exists():
        return set()
    text = bib_path.read_text(encoding="utf-8")
    return {match.group(1).strip() for match in BIB_PATTERN.finditer(text)}


def _claim_map_candidates(project_dir: Path) -> list[Path]:
    project_dir = Path(project_dir)
    return [
        project_dir / "evidence" / "claim_map.jsonl",
        project_dir / "audit_top1" / "analysis_audit" / "claim_map.jsonl",
    ]


def _normalize_claim_payload(payload: dict, source_path: Path) -> dict:
    claim = {
        "claim_id": payload.get("claim_id"),
        "statement": payload.get("statement") or payload.get("claim") or "",
        "source_excerpt": payload.get("source_excerpt") or payload.get("support") or "",
        "source_path": payload.get("source_path") or payload.get("support") or str(source_path),
        "reference_key": payload.get("reference_key"),
        "status": payload.get("status") or "",
        "claim_source": source_path.name,
    }
    if "support" in payload:
        claim["support"] = payload.get("support")
    return claim


def _claim_is_allowed(payload: dict, bib_keys: set[str], source_path: Path) -> bool:
    status = str(payload.get("status") or "").strip().lower()
    if status == "supported":
        reference_key = payload.get("reference_key")
        if not reference_key:
            return False
        if source_path.name == "claim_map.jsonl" and source_path.parent.name == "evidence":
            return reference_key in bib_keys
        return True
    return status.startswith("allowed")


def _load_supported_claims(project_dir: Path) -> list[dict]:
    bib_keys = _load_bib_keys(project_dir)
    claims: list[dict] = []
    seen_ids: set[str] = set()
    for claim_path in _claim_map_candidates(project_dir):
        if not claim_path.exists():
            continue
        for line in claim_path.read_text(encoding="utf-8-sig").splitlines():
            content = line.strip()
            if not content:
                continue
            payload = json.loads(content)
            normalized = _normalize_claim_payload(payload, claim_path)
            claim_id = normalized.get("claim_id")
            if not claim_id or claim_id in seen_ids:
                continue
            if _claim_is_allowed(payload, bib_keys, claim_path):
                claims.append(normalized)
                seen_ids.add(claim_id)
    return claims


def _story_duration_seconds(conference: dict, scene_count: int) -> int:
    duration = conference.get("presentation", {}).get("duration_minutes")
    if not duration or not scene_count:
        return 0
    return max(20, int((int(duration) * 60) / scene_count))


def _build_deck_scenes(conference: dict, claims: list[dict]) -> list[dict]:
    max_slides = int(conference.get("limits", {}).get("max_slides") or 8)
    claim_capacity = max(0, max_slides - 3)
    selected_claims = claims[:claim_capacity]
    scene_count = 3 + len(selected_claims)
    duration = _story_duration_seconds(conference, scene_count)
    scenes = [
        {
            "scene_id": "slide-001",
            "role": "title",
            "title": conference.get("event_name", "Conference Presentation"),
            "body": "Claim-safe scientific story derived from the active project.",
            "source_claim_ids": [],
            "speaker_notes": "Open with the clinical or scientific problem, not a methods list.",
            "duration_seconds": duration,
            "animation": "fade-in",
        },
        {
            "scene_id": "slide-002",
            "role": "methods",
            "title": "Study Design and Evidence Base",
            "body": "Summarize protocol, corpus, analysis status, and evidence-lock policy.",
            "source_claim_ids": [],
            "speaker_notes": "Keep methods tight and focus on why the evidence is reliable.",
            "duration_seconds": duration,
            "animation": "stagger",
        },
    ]
    for idx, claim in enumerate(selected_claims, start=3):
        scenes.append(
            {
                "scene_id": f"slide-{idx:03d}",
                "role": "finding",
                "title": f"Finding {idx - 2}",
                "body": claim.get("statement", ""),
                "source_claim_ids": [claim.get("claim_id")],
                "speaker_notes": claim.get("source_excerpt", ""),
                "duration_seconds": duration,
                "animation": "chart-build",
            }
        )
    scenes.append(
        {
            "scene_id": f"slide-{len(scenes) + 1:03d}",
            "role": "close",
            "title": "Implications",
            "body": "State what can be concluded now, what remains uncertain, and what should happen next.",
            "source_claim_ids": [],
            "speaker_notes": "Avoid overclaiming beyond the supported evidence.",
            "duration_seconds": duration,
            "animation": "fade-in",
        }
    )
    return scenes[:max_slides]


def _build_poster_scenes(conference: dict, claims: list[dict]) -> list[dict]:
    finding_claims = claims[:4]
    scenes = [
        {
            "scene_id": "block-001",
            "role": "title",
            "title": conference.get("event_name", "Conference Poster"),
            "body": "Editable HTML-first scientific poster.",
            "source_claim_ids": [],
        },
        {
            "scene_id": "block-002",
            "role": "background",
            "title": "Background",
            "body": "Briefly frame the problem, population, and knowledge gap.",
            "source_claim_ids": [],
        },
        {
            "scene_id": "block-003",
            "role": "methods",
            "title": "Methods",
            "body": "Protocol, data sources, analysis plan, and evidence-lock status.",
            "source_claim_ids": [],
        },
    ]
    for idx, claim in enumerate(finding_claims, start=4):
        scenes.append(
            {
                "scene_id": f"block-{idx:03d}",
                "role": "finding",
                "title": f"Key finding {idx - 3}",
                "body": claim.get("statement", ""),
                "source_claim_ids": [claim.get("claim_id")],
            }
        )
    scenes.append(
        {
            "scene_id": f"block-{len(scenes) + 1:03d}",
            "role": "conclusion",
            "title": "Conclusion",
            "body": "Conclusions are limited to claim-supported findings and labeled uncertainties.",
            "source_claim_ids": [],
        }
    )
    return scenes


def _assets_for_claims(claims: list[dict], kind: str) -> list[dict]:
    assets = []
    for idx, claim in enumerate(claims[:6], start=1):
        asset_type = "chart" if kind in {"deck", "poster"} else "table"
        routed = route_visual_backend(asset_type)
        assets.append(
            {
                "asset_id": f"asset-{idx:03d}",
                "type": asset_type,
                "purpose": "Visualize an evidence-locked finding.",
                "source_claim_ids": [claim.get("claim_id")],
                "backend": routed["backend"],
                "skill": routed["skill"],
                "status": "planned",
            }
        )
    if not assets:
        routed = route_visual_backend("technical-diagram")
        assets.append(
            {
                "asset_id": "asset-001",
                "type": "technical-diagram",
                "purpose": "Explain study design without unsupported factual claims.",
                "source_claim_ids": [],
                "backend": routed["backend"],
                "skill": routed["skill"],
                "status": "planned",
            }
        )
    return assets


def _write_conference_abstract(deliverable_dir: Path, conference: dict, claims: list[dict]) -> Path:
    max_words = int(conference.get("limits", {}).get("max_words_abstract") or 300)
    statements = [claim.get("statement", "") for claim in claims if claim.get("statement")]
    body = " ".join(statements) or "No supported claims are available yet. Complete Evidence Lock before final submission."
    words = body.split()[: max(25, max_words - 40)]
    text = (
        f"# {conference.get('event_name', 'Conference')} Abstract\n\n"
        "Background: This abstract is generated from the active project and restricted to evidence-locked claims.\n\n"
        f"Results: {' '.join(words)}\n\n"
        "Conclusion: Interpretations remain bounded by the approved claim map and conference requirements.\n"
    )
    path = deliverable_dir / "conference_abstract.md"
    path.write_text(text, encoding="utf-8")
    return path


def _write_handout_and_pack(deliverable_dir: Path, conference: dict) -> None:
    authors = ", ".join(conference.get("authors", [])) or "Authors pending"
    affiliations = "; ".join(conference.get("affiliations", [])) or "Affiliations pending"
    qr_url = conference.get("qr", {}).get("url") or "Replace with final DOI, OSF, repository, or project landing URL before printing."
    (deliverable_dir / "handout.md").write_text(
        f"# One-Page Handout\n\nEvent: {conference.get('event_name')}\nProfile: {conference.get('profile')}\n\n"
        f"Authors: {authors}\nAffiliations: {affiliations}\n\n"
        "Use this handout as a claim-safe summary after QA passes.\n",
        encoding="utf-8",
    )
    (deliverable_dir / "submission_pack" / "README.md").write_text(
        "# Submission Pack\n\n"
        "- HTML is the canonical source.\n"
        "- PDF is print/presentation output.\n"
        "- PPTX is editable fallback with simplified animations.\n"
        "- Submission automation requires explicit dry-run and final confirmation.\n",
        encoding="utf-8",
    )
    (deliverable_dir / "submission_pack" / "qr_payload.txt").write_text(
        f"{qr_url}\n",
        encoding="utf-8",
    )


def plan_deliverable(deliverable_dir: Path) -> dict:
    deliverable_dir = Path(deliverable_dir)
    project_dir = _project_dir_from_deliverable(deliverable_dir)
    conference = load_structured_file(deliverable_dir / "conference.yaml")
    kind = conference.get("kind", "deck")
    claims = _load_supported_claims(project_dir)
    scenes = _build_poster_scenes(conference, claims) if kind == "poster" else _build_deck_scenes(conference, claims)
    assets = _assets_for_claims(claims, kind)

    storyboard = load_structured_file(deliverable_dir / "storyboard.yaml")
    storyboard.update(
        {
            "status": "locked",
            "approved_claim_ids": [claim.get("claim_id") for claim in claims],
            "scenes": scenes,
            "assets": assets,
            "updated_at": _now_iso(),
        }
    )
    save_structured_file(deliverable_dir / "storyboard.yaml", storyboard)
    abstract_path = _write_conference_abstract(deliverable_dir, conference, claims)
    _write_handout_and_pack(deliverable_dir, conference)
    _advance_stage(deliverable_dir, "storyboard-lock")
    _record_artifact(deliverable_dir, deliverable_dir / "storyboard.yaml", "storyboard")
    _record_artifact(deliverable_dir, abstract_path, "abstract")

    return {
        "status": "planned",
        "deliverable_dir": str(deliverable_dir),
        "kind": kind,
        "scene_count": len(scenes),
        "approved_claim_count": len(claims),
        "approved_claim_ids": [claim.get("claim_id") for claim in claims],
    }


def _resolve_storyboard_path(deliverable_dir: Path, raw_path: str | None) -> Path | None:
    if not raw_path:
        return None
    candidate = Path(str(raw_path))
    if candidate.is_absolute():
        return candidate if candidate.exists() else None
    resolved = Path(deliverable_dir) / candidate
    return resolved if resolved.exists() else None


def _asset_data_uri(path: Path | None) -> str:
    if path is None or not Path(path).exists():
        return ""
    mime_type, _ = mimetypes.guess_type(str(path))
    payload = base64.b64encode(Path(path).read_bytes()).decode("ascii")
    return f"data:{mime_type or 'application/octet-stream'};base64,{payload}"


def _poster_span(scene: dict) -> int:
    try:
        span = int(scene.get("span") or 3)
    except (TypeError, ValueError):
        span = 3
    return max(2, min(12, span))


def _storyboard_asset_manifest(deliverable_dir: Path, storyboard: dict) -> dict:
    files: list[dict] = []
    seen_paths: set[str] = set()
    for scene in storyboard.get("scenes", []):
        for key in ["image_path", "qr_path", "asset_path"]:
            resolved = _resolve_storyboard_path(deliverable_dir, scene.get(key))
            if not resolved:
                continue
            rel = resolved.relative_to(deliverable_dir).as_posix()
            if rel in seen_paths:
                continue
            seen_paths.add(rel)
            files.append(
                {
                    "path": rel,
                    "bytes": resolved.stat().st_size,
                    "sha256": _sha256_file(resolved),
                    "scene_id": scene.get("scene_id"),
                    "role": scene.get("role"),
                }
            )
    return {
        "assets": storyboard.get("assets", []),
        "files": files,
    }


def _css(theme: dict, conference: dict) -> str:
    palette = theme.get("palette", {})
    min_font = theme.get("accessibility", {}).get("min_font_px", 22)
    dimensions = conference.get("dimensions", {})
    width = dimensions.get("width_px", 1920)
    height = dimensions.get("height_px", 1080)
    return f"""
:root {{
  --ink: {palette.get('ink', '#15211f')};
  --paper: {palette.get('paper', '#f7f2e8')};
  --accent: {palette.get('accent', '#0d6b5f')};
  --accent-2: {palette.get('accent_2', '#9b3f00')};
  --muted: {palette.get('muted', '#5d6b66')};
  --w: {width}px;
  --h: {height}px;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background:
    radial-gradient(circle at 10% 10%, rgba(255, 225, 184, 0.9) 0, transparent 28%),
    radial-gradient(circle at 94% 5%, rgba(13, 107, 95, 0.12) 0, transparent 24%),
    linear-gradient(135deg, #f7f2e8, #e4f0ed);
  color: var(--ink);
  font-family: Aptos, Calibri, sans-serif;
  font-size: {min_font}px;
}}
.deck {{ width: var(--w); min-height: var(--h); margin: 0 auto; }}
.poster {{ width: var(--w); height: var(--h); margin: 0 auto; overflow: hidden; }}
.slide {{
  width: var(--w);
  height: var(--h);
  padding: 92px 110px;
  display: grid;
  grid-template-rows: auto 1fr auto;
  page-break-after: always;
  overflow: hidden;
}}
.poster {{
  padding: 34px;
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 14px;
  align-content: start;
  font-size: 20px;
}}
.block {{
  min-height: 0;
  padding: 16px 18px;
  border: 1.5px solid rgba(13, 107, 95, 0.18);
  background: rgba(255, 255, 255, 0.72);
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 5px 16px rgba(21, 33, 31, 0.07);
  display: flex;
  flex-direction: column;
  gap: 8px;
}}
h1, h2 {{
  margin: 0;
  font-family: Georgia, Aptos Display, serif;
  letter-spacing: -0.035em;
}}
h1 {{ font-size: 42px; line-height: 0.98; }}
h2 {{ font-size: 25px; line-height: 1.02; color: var(--accent); }}
p {{ line-height: 1.2; margin: 0; }}
.poster p, .poster li {{ font-size: 18px; line-height: 1.18; }}
ul {{ margin: 0; padding-left: 1.1em; line-height: 1.18; }}
li + li {{ margin-top: 5px; }}
.kicker {{ color: var(--accent-2); text-transform: uppercase; letter-spacing: 0.12em; font-size: 12px; font-weight: 700; }}
.claim {{ border-left: 8px solid var(--accent); padding-left: 28px; }}
.notes {{ color: var(--muted); font-size: 15px; }}
.brandline {{ display: flex; flex-wrap: wrap; gap: 16px; color: var(--muted); font-size: 18px; align-items: center; }}
.qr {{ font-family: Cascadia Mono, Consolas, monospace; color: var(--accent); font-size: 16px; overflow-wrap: anywhere; word-break: break-word; }}
.span-12 {{ grid-column: span 12; }}
.span-9 {{ grid-column: span 9; }}
.span-8 {{ grid-column: span 8; }}
.span-6 {{ grid-column: span 6; }}
.span-5 {{ grid-column: span 5; }}
.span-4 {{ grid-column: span 4; }}
.span-3 {{ grid-column: span 3; }}
.span-2 {{ grid-column: span 2; }}
.block.header {{
  min-height: 144px;
  padding: 22px 34px;
  background-color: #0D6B5F;
  background-image: linear-gradient(130deg, rgba(13, 107, 95, 0.96), rgba(7, 76, 68, 0.94));
  color: #f6f3eb;
}}
.block.header h1 {{
  font-size: 42px;
  line-height: 0.98;
  max-width: 1620px;
}}
.block.header p {{
  font-size: 18px;
}}
.block.header h1, .block.header h2, .block.header .kicker, .block.header p, .block.header .notes {{
  color: inherit;
}}
.block.header .kicker {{
  color: #ffd6a2;
}}
.poster-meta {{
  display: flex;
  flex-wrap: wrap;
  gap: 14px 18px;
  color: rgba(246, 243, 235, 0.92);
  font-size: 15px;
}}
.figure-frame {{
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 0;
  flex: 1 1 auto;
  justify-content: center;
}}
.figure-frame img {{
  width: 100%;
  height: 100%;
  min-height: 0;
  max-height: 120px;
  object-fit: contain;
  background: rgba(255, 255, 255, 0.86);
  border-radius: 16px;
  border: 1px solid rgba(21, 33, 31, 0.08);
}}
.figure-caption {{
  display: none;
  font-size: 11px;
  color: var(--muted);
}}
.block.forest .figure-frame img {{ max-height: 150px; }}
.block.prisma .figure-frame img {{ max-height: 110px; }}
.block.network .figure-frame img, .block.ranking .figure-frame img {{ max-height: 118px; }}
.metric-row {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}}
.metric {{
  padding: 9px 12px;
  border-radius: 12px;
  background: rgba(13, 107, 95, 0.08);
  border: 1px solid rgba(13, 107, 95, 0.14);
}}
.metric-label {{
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: var(--accent-2);
}}
.metric-value {{
  font-size: 19px;
  font-weight: 700;
  color: var(--accent);
}}
.support-line {{
  display: none;
}}
.qr-panel {{
  display: grid;
  grid-template-columns: 92px 1fr;
  gap: 12px;
  align-items: center;
}}
.qr-panel img {{
  width: 92px;
  height: 92px;
  border-radius: 12px;
  border: 1px solid rgba(21, 33, 31, 0.08);
  background: white;
}}
.footer-strip {{
  grid-column: span 12;
  display: flex;
  justify-content: space-between;
  gap: 18px;
  color: var(--muted);
  font-size: 12px;
  padding: 0 8px;
}}
@keyframes rise {{ from {{ opacity: 0; transform: translateY(18px); }} to {{ opacity: 1; transform: translateY(0); }} }}
.deck .slide > * {{ animation: rise 520ms ease both; }}
.poster .block {{
  animation: none;
  opacity: 1;
  transform: none;
}}
@media print {{
  *, *::before, *::after {{
    animation: none !important;
    transition: none !important;
    opacity: 1 !important;
    transform: none !important;
  }}
}}
@page {{ size: var(--w) var(--h); margin: 0; }}
"""


def _render_deck_html(conference: dict, storyboard: dict, theme: dict) -> str:
    slides = []
    authors = ", ".join(conference.get("authors", []))
    affiliations = "; ".join(conference.get("affiliations", []))
    qr_url = conference.get("qr", {}).get("url", "")
    for scene in storyboard.get("scenes", []):
        claims = " ".join(scene.get("source_claim_ids", []))
        slides.append(
            f"""
<section class="slide" data-scene="{html.escape(scene.get('scene_id', ''))}" data-claims="{html.escape(claims)}">
  <div class="kicker">{html.escape(scene.get('role', 'slide'))}</div>
  <main>
    <h1>{html.escape(scene.get('title', ''))}</h1>
    <p class="claim">{html.escape(scene.get('body', ''))}</p>
  </main>
  <aside class="notes">{html.escape(scene.get('speaker_notes', ''))}</aside>
  <footer class="brandline"><span>{html.escape(authors)}</span><span>{html.escape(affiliations)}</span><span class="qr">{html.escape(qr_url)}</span></footer>
</section>"""
        )
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(conference.get('event_name', 'Deck'))}</title><style>{_css(theme, conference)}</style></head>
<body><div class="deck">{''.join(slides)}</div></body>
</html>"""


def _render_poster_html(deliverable_dir: Path, conference: dict, storyboard: dict, theme: dict) -> str:
    blocks = []
    for scene in storyboard.get("scenes", []):
        claims = " ".join(scene.get("source_claim_ids", []))
        title_tag = "h1" if scene.get("role") in {"title", "header"} else "h2"
        block_classes = ["block", html.escape(str(scene.get("role") or "block")), f"span-{_poster_span(scene)}"]
        kicker = html.escape(str(scene.get("kicker") or scene.get("role") or "block"))
        paragraphs = []
        if scene.get("lead"):
            paragraphs.append(f'<p class="claim">{html.escape(str(scene.get("lead")))}</p>')
        if scene.get("body"):
            paragraphs.append(f"<p>{html.escape(str(scene.get('body')))}</p>")
        bullets = scene.get("bullets") or []
        bullet_markup = ""
        if isinstance(bullets, list) and bullets:
            bullet_markup = "<ul>" + "".join(f"<li>{html.escape(str(item))}</li>" for item in bullets) + "</ul>"
        meta_lines = scene.get("meta_lines") or []
        meta_markup = ""
        if isinstance(meta_lines, list) and meta_lines:
            meta_markup = '<div class="poster-meta">' + "".join(
                f"<span>{html.escape(str(item))}</span>" for item in meta_lines
            ) + "</div>"
        metrics = scene.get("metrics") or []
        metric_markup = ""
        if isinstance(metrics, list) and metrics:
            metric_markup = '<div class="metric-row">' + "".join(
                (
                    '<div class="metric">'
                    f'<div class="metric-label">{html.escape(str(metric.get("label", "")))}</div>'
                    f'<div class="metric-value">{html.escape(str(metric.get("value", "")))}</div>'
                    "</div>"
                )
                for metric in metrics
            ) + "</div>"
        image_markup = ""
        image_uri = _asset_data_uri(_resolve_storyboard_path(deliverable_dir, scene.get("image_path")))
        if image_uri:
            image_alt = html.escape(str(scene.get("image_alt") or scene.get("title") or "Poster figure"))
            image_caption = html.escape(str(scene.get("image_caption") or ""))
            image_markup = (
                '<figure class="figure-frame">'
                f'<img src="{image_uri}" alt="{image_alt}"/>'
                f'<figcaption class="figure-caption">{image_caption}</figcaption>'
                "</figure>"
            )
        qr_markup = ""
        qr_uri = _asset_data_uri(_resolve_storyboard_path(deliverable_dir, scene.get("qr_path")))
        if qr_uri:
            qr_markup = (
                '<div class="qr-panel">'
                f'<img src="{qr_uri}" alt="{html.escape(str(scene.get("qr_label") or "QR code"))}"/>'
                "<div>"
                f"<p>{html.escape(str(scene.get('body') or 'Full references and supporting material'))}</p>"
                f"<p class=\"notes\">{html.escape(str(scene.get('qr_label') or 'Scan for the full reference pack and supporting material.'))}</p>"
                f"<p class=\"qr\">{html.escape(str(scene.get('qr_display') or conference.get('qr', {}).get('label') or 'Reference pack'))}</p>"
                "</div>"
                "</div>"
            )
        support_markup = ""
        if claims:
            support_markup = f'<div class="support-line">Claim IDs: {html.escape(claims)}</div>'
        blocks.append(
            f"""
<section class="{' '.join(block_classes)}" data-scene="{html.escape(scene.get('scene_id', ''))}" data-claims="{html.escape(claims)}">
  <div class="kicker">{kicker}</div>
  <{title_tag}>{html.escape(scene.get('title', ''))}</{title_tag}>
  {meta_markup}
  {''.join(paragraphs)}
  {bullet_markup}
  {metric_markup}
  {image_markup}
  {qr_markup}
  {support_markup}
</section>"""
        )
    footer = (
        '<section class="footer-strip">'
        f"<span>{html.escape(conference.get('event_name', 'Conference poster'))}</span>"
        f"<span>{html.escape(conference.get('profile', 'digital 16:9 landscape'))}</span>"
        "</section>"
    )
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(conference.get('event_name', 'Poster'))}</title><style>{_css(theme, conference)}</style></head>
<body><main class="poster">{''.join(blocks)}{footer}</main></body>
</html>"""


def build_deliverable(deliverable_dir: Path) -> dict:
    deliverable_dir = Path(deliverable_dir)
    conference = load_structured_file(deliverable_dir / "conference.yaml")
    storyboard = load_structured_file(deliverable_dir / "storyboard.yaml")
    theme = load_structured_file(deliverable_dir / "theme.yaml")
    slug = deliverable_dir.name
    if not storyboard.get("scenes"):
        return {"status": "blocked", "issues": ["storyboard.yaml has no scenes. Run plan first."]}

    html_text = (
        _render_poster_html(deliverable_dir, conference, storyboard, theme)
        if conference.get("kind") == "poster"
        else _render_deck_html(conference, storyboard, theme)
    )
    html_path = deliverable_dir / "layouts" / f"{slug}.html"
    html_path.write_text(html_text, encoding="utf-8")
    _save_json(deliverable_dir / "assets" / "asset_manifest.json", _storyboard_asset_manifest(deliverable_dir, storyboard))
    _advance_stage(deliverable_dir, "asset-build")
    _advance_stage(deliverable_dir, "layout-build")
    _record_artifact(deliverable_dir, html_path, "canonical-html-layout")
    return {"status": "built", "layout": str(html_path), "html_first": True}


def _unsupported_claim_issues(project_dir: Path, storyboard: dict) -> list[str]:
    approved = {claim.get("claim_id") for claim in _load_supported_claims(project_dir)}
    issues: list[str] = []
    for scene in storyboard.get("scenes", []):
        for claim_id in scene.get("source_claim_ids", []):
            if claim_id not in approved:
                issues.append(f"Storyboard references unsupported claim '{claim_id}'.")
    for asset in storyboard.get("assets", []):
        for claim_id in asset.get("source_claim_ids", []):
            if claim_id not in approved:
                issues.append(f"Asset '{asset.get('asset_id')}' references unsupported claim '{claim_id}'.")
        for field in ["source_claim_ids", "backend", "purpose"]:
            if field not in asset:
                issues.append(f"Asset '{asset.get('asset_id', 'unknown')}' is missing '{field}'.")
    return issues


def _qr_image_paths(deliverable_dir: Path, storyboard: dict) -> list[Path]:
    paths: list[Path] = []
    for scene in storyboard.get("scenes", []):
        resolved = _resolve_storyboard_path(deliverable_dir, scene.get("qr_path"))
        if resolved:
            paths.append(resolved)
    return paths


def _decode_qr_value(path: Path) -> str:
    try:
        import cv2  # type: ignore
    except Exception:
        return ""
    image = cv2.imread(str(path))
    if image is None:
        return ""
    detector = cv2.QRCodeDetector()
    value, _, _ = detector.detectAndDecode(image)
    return str(value or "").strip()


def _pdf_page_count(path: Path) -> int:
    data = Path(path).read_bytes()
    matches = re.findall(rb"/Type\s*/Page\b", data)
    return len(matches)


def qa_deliverable(deliverable_dir: Path) -> dict:
    deliverable_dir = Path(deliverable_dir)
    project_dir = _project_dir_from_deliverable(deliverable_dir)
    conference = load_structured_file(deliverable_dir / "conference.yaml")
    storyboard = load_structured_file(deliverable_dir / "storyboard.yaml")
    theme = load_structured_file(deliverable_dir / "theme.yaml")
    slug = deliverable_dir.name
    layout_path = deliverable_dir / "layouts" / f"{slug}.html"
    contract = validate_deliverable_contract(deliverable_dir, strict=False)
    issues = _unsupported_claim_issues(project_dir, storyboard)
    issues.extend(contract.get("issues", []))

    if not layout_path.exists():
        issues.append("Canonical HTML layout is missing. Run build first.")
    if conference.get("kind") == "deck":
        max_slides = int(conference.get("limits", {}).get("max_slides") or 999)
        if len(storyboard.get("scenes", [])) > max_slides:
            issues.append(f"Slide count exceeds conference limit: {len(storyboard.get('scenes', []))}/{max_slides}.")
        duration = conference.get("presentation", {}).get("duration_minutes")
        total_seconds = sum(int(scene.get("duration_seconds") or 0) for scene in storyboard.get("scenes", []))
        if duration and total_seconds > int(duration) * 60 + 5:
            issues.append(f"Speaker timing exceeds conference duration: {total_seconds}s/{int(duration) * 60}s.")
    else:
        profile = conference.get("profile", "")
        orientation = conference.get("dimensions", {}).get("orientation")
        if orientation and orientation not in profile.lower():
            issues.append(f"Poster orientation mismatch: profile '{profile}' vs dimensions '{orientation}'.")
        qr_paths = _qr_image_paths(deliverable_dir, storyboard)
        if conference.get("qr", {}).get("url"):
            if not qr_paths:
                issues.append("Poster QR is configured in conference.yaml, but no qr_path is present in storyboard scenes.")
            else:
                decoded = _decode_qr_value(qr_paths[0])
                if decoded and decoded != conference.get("qr", {}).get("url"):
                    issues.append("Poster QR code payload does not match conference.yaml qr.url.")
        author_count = len(conference.get("authors", []))
        affiliation_count = len(conference.get("affiliations", []))
        if author_count != 4:
            issues.append(f"GastroSP poster expects 4 authors; found {author_count}.")
        if affiliation_count != 2:
            issues.append(f"GastroSP poster expects 2 affiliations; found {affiliation_count}.")

    min_font = int(theme.get("accessibility", {}).get("min_font_px") or 0)
    required_font = int(conference.get("limits", {}).get("min_font_px") or 22)
    if min_font < required_font:
        issues.append(f"Minimum font is below conference requirement: {min_font}px/{required_font}px.")
    if conference.get("logos", {}).get("required") and not conference.get("logos", {}).get("files"):
        issues.append("Conference requirements mention a logo, but no logo file is configured.")

    playwright_report = {"status": "skipped"}
    if layout_path.exists():
        available = playwright_ops.playwright_available()
        if available.get("status") != "pass":
            issues.append(available.get("message", "Playwright is not available."))
            playwright_report = available
        else:
            playwright_report = playwright_ops.qa_html(layout_path, deliverable_dir / "qa", conference.get("profile", "default"))
            if playwright_report.get("status") != "pass":
                issues.append("Playwright layout QA failed.")
            for overflow in playwright_report.get("overflow_elements", []):
                issues.append(f"Overflow detected in <{overflow.get('tag')}>: {overflow.get('text')}")

    report = {
        "status": "pass" if not issues else "block",
        "issues": issues,
        "checks": {
            "claim_safe_visuals": "pass" if not _unsupported_claim_issues(project_dir, storyboard) else "block",
            "layout": "pass" if layout_path.exists() else "block",
            "playwright": playwright_report,
            "contract": contract,
            "export": "pending",
        },
        "updated_at": _now_iso(),
    }
    _save_json(deliverable_dir / "qa_report.json", report)
    _advance_stage(deliverable_dir, "qa")
    return report


def _next_export_version(deliverable_dir: Path) -> str:
    manifest = load_structured_file(Path(deliverable_dir) / "manifest.json")
    exports = manifest.get("exports", [])
    return f"export-v{len(exports) + 1:03d}"


def _copy_latest_alias(source_path: Path, alias_path: Path) -> None:
    alias_path.parent.mkdir(parents=True, exist_ok=True)
    alias_path.write_bytes(source_path.read_bytes())


def _register_export_version(deliverable_dir: Path, export_version: str, artifacts: list[dict]) -> dict:
    manifest_path = Path(deliverable_dir) / "manifest.json"
    manifest = load_structured_file(manifest_path)
    exports = manifest.setdefault("exports", [])
    exports[:] = [export for export in exports if export.get("version") != export_version]
    exports.append({"version": export_version, "artifacts": artifacts, "created_at": _now_iso()})
    manifest["updated_at"] = _now_iso()
    _save_json(manifest_path, manifest)
    return manifest


def export_deliverable(deliverable_dir: Path, strict: bool = False) -> dict:
    deliverable_dir = Path(deliverable_dir)
    conference = load_structured_file(deliverable_dir / "conference.yaml")
    qa_report = load_structured_file(deliverable_dir / "qa_report.json")
    slug = deliverable_dir.name
    layout_path = deliverable_dir / "layouts" / f"{slug}.html"
    if qa_report.get("status") != "pass":
        return {"status": "blocked", "issues": ["qa_report.json must be pass before export."]}
    contract = validate_deliverable_contract(deliverable_dir, strict=strict)
    if contract["status"] != "pass":
        return {"status": "blocked", "issues": contract["issues"], "contract": contract}
    if not layout_path.exists():
        return {"status": "blocked", "issues": ["Canonical HTML layout is missing."]}

    exports_dir = deliverable_dir / "exports"
    export_version = _next_export_version(deliverable_dir)
    version_dir = exports_dir / export_version
    version_dir.mkdir(parents=True, exist_ok=True)
    html_export = version_dir / f"{slug}.html"
    html_export.write_text(layout_path.read_text(encoding="utf-8"), encoding="utf-8")
    artifacts = [{"path": str(html_export), "role": "html"}]
    manifest = _record_artifact(deliverable_dir, html_export, "canonical-html-export", export_version)
    _copy_latest_alias(html_export, exports_dir / f"{slug}.html")

    pdf_export = version_dir / f"{slug}.pdf"
    pdf_report = playwright_ops.export_html_pdf(html_export, pdf_export, conference.get("profile", "default"))
    if pdf_report.get("status") == "pass" and pdf_export.exists():
        if conference.get("kind") == "poster":
            page_count = _pdf_page_count(pdf_export)
            if page_count != 1:
                return {
                    "status": "blocked",
                    "issues": [f"Poster PDF must be single-page; detected {page_count} pages."],
                    "pdf": pdf_report,
                }
            if pdf_export.stat().st_size > 10 * 1024 * 1024:
                return {
                    "status": "blocked",
                    "issues": [f"Poster PDF exceeds 10 MB limit: {pdf_export.stat().st_size} bytes."],
                    "pdf": pdf_report,
                }
        artifacts.append({"path": str(pdf_export), "role": "pdf"})
        manifest = _record_artifact(deliverable_dir, pdf_export, "pdf-export", export_version)
        _copy_latest_alias(pdf_export, exports_dir / f"{slug}.pdf")
    else:
        return {"status": "blocked", "issues": [pdf_report.get("message", "PDF export failed.")], "pdf": pdf_report}

    thumbnail = version_dir / f"{slug}.png"
    thumb_report = playwright_ops.capture_thumbnail(html_export, thumbnail, conference.get("profile", "default"))
    if thumb_report.get("status") == "pass" and thumbnail.exists():
        artifacts.append({"path": str(thumbnail), "role": "thumbnail"})
        manifest = _record_artifact(deliverable_dir, thumbnail, "thumbnail", export_version)
        _copy_latest_alias(thumbnail, exports_dir / f"{slug}.png")
    else:
        return {"status": "blocked", "issues": [thumb_report.get("message", "Thumbnail export failed.")], "thumbnail": thumb_report}

    pptx_export = version_dir / f"{slug}.pptx"
    pptx_report = pptx_bridge.export_editable_pptx(
        deliverable_dir / "storyboard.yaml",
        pptx_export,
        conference.get("kind", "deck"),
        conference_path=deliverable_dir / "conference.yaml",
    )
    if pptx_report.get("status") == "pass" and pptx_export.exists():
        if conference.get("kind") == "poster" and int(pptx_report.get("slide_count") or 0) != 1:
            return {
                "status": "blocked",
                "issues": [f"Poster PPTX must export as one slide; got {pptx_report.get('slide_count')}."],
                "pptx": pptx_report,
            }
        artifacts.append({"path": str(pptx_export), "role": "pptx"})
        manifest = _record_artifact(deliverable_dir, pptx_export, "editable-pptx-export", export_version)
        _copy_latest_alias(pptx_export, exports_dir / f"{slug}.pptx")
    else:
        return {"status": "blocked", "issues": [pptx_report.get("message", "PPTX export failed.")], "pptx": pptx_report}

    qa_report["checks"]["export"] = "pass"
    _save_json(deliverable_dir / "qa_report.json", qa_report)
    manifest = _register_export_version(deliverable_dir, export_version, artifacts)
    manifest = _advance_stage(deliverable_dir, "export")
    return {
        "status": "exported",
        "export_version": export_version,
        "artifacts": artifacts,
        "manifest": manifest,
        "policy": "HTML is canonical; PDF is output; PPTX is editable fallback with simplified motion.",
    }


def submit_deliverable(deliverable_dir: Path, action: str = "dry-run", confirm: bool = False) -> dict:
    deliverable_dir = Path(deliverable_dir)
    conference = load_structured_file(deliverable_dir / "conference.yaml")
    qa_report = load_structured_file(deliverable_dir / "qa_report.json")
    if qa_report.get("status") != "pass":
        return {"status": "blocked", "message": "QA must pass before submission operations."}
    available = playwright_ops.playwright_available()
    if available.get("status") != "pass":
        return {"status": "blocked", "message": available.get("message", "Playwright is not available.")}

    action = (action or "dry-run").strip().lower()
    portal_url = conference.get("submission", {}).get("portal_url") or ""
    if action == "dry-run":
        payload = {
            "status": "pass",
            "action": "dry-run",
            "portal_url": portal_url,
            "message": "Submission dry-run passed local gates. No final submission was performed.",
        }
        _save_json(deliverable_dir / "submission" / "dry_run.json", payload)
        _advance_stage(deliverable_dir, "submission-dry-run")
        return payload

    if action == "run" and not confirm:
        return {
            "status": "blocked",
            "message": "Final submission automation requires explicit confirmation.",
        }

    payload = {
        "status": "ready",
        "action": "run",
        "portal_url": portal_url,
        "message": "Human confirmation recorded. Portal-specific click automation must use a fresh Playwright snapshot before submit.",
    }
    _save_json(deliverable_dir / "submission" / "run_request.json", payload)
    _advance_stage(deliverable_dir, "submission-run")
    return payload


def reset_deliverable_exports(deliverable_dir: Path) -> dict:
    exports_dir = Path(deliverable_dir) / "exports"
    if exports_dir.exists():
        shutil.rmtree(exports_dir)
    exports_dir.mkdir(parents=True, exist_ok=True)
    return {"status": "reset", "exports_dir": str(exports_dir)}
