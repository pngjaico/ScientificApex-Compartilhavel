from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from .benchmarks import benchmark_gate_passed
from .serialization import save_structured_file


CLAIM_PATTERN = re.compile(r"\{\{claim:([a-zA-Z0-9_.-]+)\}\}")
BIB_PATTERN = re.compile(r"@\w+\{([^,]+),")
DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$", re.IGNORECASE)
PMID_PATTERN = re.compile(r"^\d{1,12}$")
PROHIBITED_CONFIDENCE_PATTERN = re.compile(
    r"\b(perfect|world-best|world best|production-grade|production grade|perfeito|melhor do mundo)\b",
    re.IGNORECASE,
)
FACTUAL_CUE_PATTERN = re.compile(
    r"(\b(is|are|was|were|has|have|had|contains|showed|reported|increased|decreased|"
    r"improved|reduced|associated|demonstrated|found|identified|compared|selected|expects|"
    r"validates|implements|seeds|requires|reported|foi|foram|demonstrou|aumentou|reduziu|associado|associada|mostrou)\b|"
    r"\b(PubMed|Crossref|OpenAlex|PRISMA|CONSORT|EQUATOR|DOI|PMID)\b|"
    r"\d{4}|%|\bp\s*[<=>]|\bCI\b|\bOR\b|\bRR\b|\bHR\b)",
    re.IGNORECASE,
)
TEMPORAL_CUE_PATTERN = re.compile(
    r"\b(current|currently|latest|today|now|as of|atual|atualmente|mais recente|hoje)\b",
    re.IGNORECASE,
)
TEXT_SOURCE_EXTENSIONS = {".txt", ".md", ".json", ".jsonl", ".csv", ".tsv", ".xml", ".html"}


def _load_claim_entries(project_dir: Path) -> tuple[list[dict], list[str]]:
    claim_path = Path(project_dir) / "evidence" / "claim_map.jsonl"
    claims: list[dict] = []
    issues: list[str] = []
    if not claim_path.exists():
        return claims, issues
    for line_number, line in enumerate(claim_path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        content = line.strip()
        if not content:
            continue
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            issues.append(f"evidence/claim_map.jsonl line {line_number} is not valid JSON: {exc.msg}.")
            continue
        claim_id = payload.get("claim_id")
        if claim_id:
            payload["_line_number"] = line_number
            claims.append(payload)
        else:
            issues.append(f"evidence/claim_map.jsonl line {line_number} is missing claim_id.")
    return claims, issues


def _claim_map_from_entries(entries: list[dict], issues: list[str]) -> dict[str, dict]:
    claims: dict[str, dict] = {}
    seen: dict[str, int] = {}
    for entry in entries:
        claim_id = str(entry.get("claim_id"))
        if claim_id in seen:
            issues.append(
                f"Duplicate claim_id '{claim_id}' in evidence/claim_map.jsonl lines {seen[claim_id]} and {entry.get('_line_number')}."
            )
            continue
        seen[claim_id] = int(entry.get("_line_number") or 0)
        claims[claim_id] = entry
    return claims


def _load_bib_keys(project_dir: Path) -> set[str]:
    bib_path = Path(project_dir) / "drafts" / "references.bib"
    if not bib_path.exists():
        return set()
    text = bib_path.read_text(encoding="utf-8")
    return {match.group(1).strip() for match in BIB_PATTERN.finditer(text)}


def _normalize_excerpt(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _resolve_source_path(project_dir: Path, source_path: str) -> Path:
    candidate = Path(source_path)
    if candidate.is_absolute():
        return candidate
    project_candidate = project_dir / candidate
    if project_candidate.exists():
        return project_candidate
    workspace_candidate = project_dir.parents[1] / candidate if len(project_dir.parents) > 1 else project_candidate
    if workspace_candidate.exists():
        return workspace_candidate
    return project_candidate


def _source_contains_excerpt(source_path: Path, source_excerpt: str) -> bool:
    if source_path.suffix.lower() not in TEXT_SOURCE_EXTENSIONS:
        return False
    source_text = source_path.read_text(encoding="utf-8", errors="replace")
    if source_excerpt in source_text:
        return True
    return _normalize_excerpt(source_excerpt) in _normalize_excerpt(source_text)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalized_hash(value: object) -> str:
    return str(value or "").removeprefix("sha256:").strip().lower()


def _parse_observed_at(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(UTC)


def _max_age_days(policy: object) -> int | None:
    if isinstance(policy, dict):
        value = policy.get("max_age_days")
        return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None
    if not isinstance(policy, str):
        return None
    normalized = policy.strip().lower()
    if normalized == "current":
        return 30
    match = re.fullmatch(r"max-age-days:(\d+)", normalized)
    return int(match.group(1)) if match else None


def _source_registry(project_dir: Path) -> tuple[dict[str, dict], list[str]]:
    """Load an explicit source registry; it is mandatory for V2 eligibility."""
    path = Path(project_dir) / "sources" / "registry.jsonl"
    sources: dict[str, dict] = {}
    issues: list[str] = []
    if not path.exists() or not path.read_text(encoding="utf-8", errors="replace").strip():
        return sources, ["sources/registry.jsonl is required for EvidenceLockReportV2."]
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            issues.append(f"sources/registry.jsonl line {number} is invalid JSON.")
            continue
        source_id = entry.get("source_id") or entry.get("id")
        if not source_id:
            issues.append(f"sources/registry.jsonl line {number} is missing source_id.")
        else:
            sources[str(source_id)] = entry
    return sources, issues


def _unmarked_factual_lines(manuscript: str) -> list[int]:
    lines: list[int] = []
    in_code_block = False
    for line_number, line in enumerate(manuscript.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block or not stripped:
            continue
        if stripped.startswith("#") or stripped in {"---", "***"}:
            continue
        if CLAIM_PATTERN.search(stripped):
            continue
        if FACTUAL_CUE_PATTERN.search(stripped):
            lines.append(line_number)
    return lines


def validate_evidence_lock(project_dir: Path) -> dict:
    project_dir = Path(project_dir)
    manuscript_path = project_dir / "drafts" / "manuscript.md"
    manuscript = manuscript_path.read_text(encoding="utf-8") if manuscript_path.exists() else ""
    claim_ids = CLAIM_PATTERN.findall(manuscript)
    claim_entries, issues = _load_claim_entries(project_dir)
    claim_map = _claim_map_from_entries(claim_entries, issues)
    bib_keys = _load_bib_keys(project_dir)

    if not claim_ids:
        issues.append("No claim markers were found in drafts/manuscript.md.")

    for line_number in _unmarked_factual_lines(manuscript):
        issues.append(f"Factual-looking sentence on drafts/manuscript.md line {line_number} has no {{{{claim:...}}}} marker.")

    if PROHIBITED_CONFIDENCE_PATTERN.search(manuscript) and not benchmark_gate_passed(project_dir):
        issues.append(
            "Prohibited confidence language ('perfect', 'world-best', 'production-grade', 'perfeito', or equivalent) "
            "requires a gate-eligible acceptance-level AgentBenchmarkReport."
        )

    required_fields = ["statement", "source_path", "source_excerpt", "reference_key", "status"]
    for claim_id in claim_ids:
        claim = claim_map.get(claim_id)
        if claim is None:
            issues.append(f"Claim marker '{claim_id}' is missing from evidence/claim_map.jsonl.")
            continue
        for field in required_fields:
            if not claim.get(field):
                issues.append(f"Claim '{claim_id}' is missing required field '{field}'.")
        if claim.get("status") != "supported":
            issues.append(f"Claim '{claim_id}' is not marked as supported.")
        reference_key = claim.get("reference_key")
        if reference_key and reference_key not in bib_keys:
            issues.append(f"Reference key '{reference_key}' for claim '{claim_id}' is missing from drafts/references.bib.")
        source_path_value = claim.get("source_path")
        source_excerpt = claim.get("source_excerpt")
        if source_path_value and source_excerpt:
            source_path = _resolve_source_path(project_dir, str(source_path_value))
            if not source_path.exists():
                issues.append(f"Source path '{source_path_value}' for claim '{claim_id}' does not exist.")
            elif source_path.suffix.lower() not in TEXT_SOURCE_EXTENSIONS:
                issues.append(
                    f"Claim '{claim_id}' source_path must reference a registered text extraction for excerpt verification; "
                    f"binary source '{source_path_value}' is not directly verifiable."
                )
            elif not _source_contains_excerpt(source_path, str(source_excerpt)):
                issues.append(f"Source excerpt for claim '{claim_id}' does not appear in '{source_path_value}'.")
        doi = claim.get("doi")
        if doi and not DOI_PATTERN.match(str(doi).strip()):
            issues.append(f"Claim '{claim_id}' declares invalid DOI '{doi}'.")
        pmid = claim.get("pmid")
        if pmid and not PMID_PATTERN.match(str(pmid).strip()):
            issues.append(f"Claim '{claim_id}' declares invalid PMID '{pmid}'.")

    # V2 provenance is deliberately stricter than legacy readability. Existing
    # claim maps can still be inspected, but cannot unlock a V2 gate.
    registry, v2_issues = _source_registry(project_dir)
    for claim_id in claim_ids:
        claim = claim_map.get(claim_id)
        if claim is None:
            continue
        for field in ("source_id", "source_hash", "observed_at", "locator", "freshness_policy", "support"):
            if not claim.get(field):
                v2_issues.append(f"Claim '{claim_id}' is missing V2 field '{field}'.")
        source_id = str(claim.get("source_id") or "")
        source = registry.get(source_id)
        if source_id and source is None:
            v2_issues.append(f"Claim '{claim_id}' source_id '{source_id}' is absent from sources/registry.jsonl.")
        if source and not re.fullmatch(r"[0-9a-f]{64}", _normalized_hash(source.get("sha256"))):
            v2_issues.append(f"Registry source '{source_id}' must have a concrete SHA-256 hash.")
        if (
            source
            and claim.get("source_hash")
            and source.get("sha256")
            and _normalized_hash(claim.get("source_hash")) != _normalized_hash(source.get("sha256"))
        ):
            v2_issues.append(f"Claim '{claim_id}' source_hash disagrees with registry source '{source_id}'.")
        source_path_value = claim.get("source_path")
        if source_path_value and claim.get("source_hash"):
            source_path = _resolve_source_path(project_dir, str(source_path_value))
            if source_path.exists() and _sha256(source_path) != _normalized_hash(claim.get("source_hash")):
                v2_issues.append(f"Claim '{claim_id}' source_hash does not match current source bytes.")
        if claim.get("support") != "supported":
            v2_issues.append(f"Claim '{claim_id}' support must be 'supported' for gate eligibility.")
        observed_at = _parse_observed_at(claim.get("observed_at"))
        if observed_at is None:
            v2_issues.append(f"Claim '{claim_id}' observed_at must be a timezone-aware ISO-8601 timestamp.")
        elif observed_at > datetime.now(UTC):
            v2_issues.append(f"Claim '{claim_id}' observed_at cannot be in the future.")
        source_observed_at = _parse_observed_at(source.get("observed_at")) if source else None
        if source and source_observed_at is None:
            v2_issues.append(f"Registry source '{source_id}' observed_at is missing or invalid.")
        if observed_at and source_observed_at and observed_at != source_observed_at:
            v2_issues.append(f"Claim '{claim_id}' observed_at disagrees with registry source '{source_id}'.")
        policy = claim.get("freshness_policy")
        policy_name = str(policy).strip().lower() if isinstance(policy, str) else ""
        max_age = _max_age_days(policy)
        temporal = bool(claim.get("temporal")) or bool(TEMPORAL_CUE_PATTERN.search(str(claim.get("statement") or "")))
        if policy_name not in {"immutable", "historical"} and max_age is None:
            v2_issues.append(
                f"Claim '{claim_id}' freshness_policy must be immutable, historical, current, or max-age-days:N."
            )
        if temporal and max_age is None:
            v2_issues.append(f"Temporal claim '{claim_id}' requires a bounded freshness policy.")
        if observed_at and max_age is not None:
            age_days = (datetime.now(UTC) - observed_at).total_seconds() / 86400
            if age_days > max_age:
                v2_issues.append(
                    f"Claim '{claim_id}' is stale: observed {age_days:.1f} days ago with max age {max_age}."
                )

    all_issues = [*issues, *v2_issues]
    status = "pass" if not all_issues else "block"
    from .policy.gates import workspace_snapshot

    report = {
        "contract": "EvidenceLockReportV2",
        "contract_version": 2,
        "generated_at": datetime.now(UTC).isoformat(),
        "status": status,
        "gate_eligible": status == "pass",
        "claims_checked": claim_ids,
        "issues": issues,
        "v2_issues": v2_issues,
        "source_registry_count": len(registry),
        "snapshot": workspace_snapshot(project_dir),
    }
    save_structured_file(project_dir / "reviews" / "evidence_lock_report.json", report)
    return report
