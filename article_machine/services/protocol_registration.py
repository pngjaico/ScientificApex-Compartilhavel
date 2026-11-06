"""Fail-closed local policy: register and verify a protocol before scientific work.

Verification records attest a review of a hashed registry record. They do not
provide cryptographic proof of registry authenticity or substitute for reviewers.
This stricter workspace rule is user policy, not a universal registry requirement.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from ..serialization import load_structured_file, save_structured_file

PLANNING_MODES = {"bootstrap", "protocol-freeze"}
VERIFICATION_PATH = "evidence/protocol_registration/verification.json"
START_PATH = ".machine/scientific_start.json"


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def protocol_fingerprint(project_dir: Path) -> str:
    protocol = load_structured_file(Path(project_dir) / "protocol.yaml")
    substantive = {key: value for key, value in protocol.items() if key not in {"registration", "status"}}
    content = json.dumps(substantive, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def registration_required(project_dir: Path) -> bool:
    project = load_structured_file(Path(project_dir) / "project.yaml")
    # Governance builds/test fixtures are not studies. A missing/unknown project
    # is not an exemption. Per-project required:false cannot disable this policy.
    return not (project.get("project_type") == "machine-governance" and project.get("lane") == "machine-governance")


def _registry_identity(registry: str, identifier: str, url: str) -> list[str]:
    issues = []
    parsed = urlsplit(str(url))
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.query or parsed.fragment:
        issues.append("Registry URL must be canonical HTTPS without credentials, query or fragment.")
    if registry == "PROSPERO":
        if not re.fullmatch(r"CRD\d{8,}", identifier) or host != "www.crd.york.ac.uk":
            issues.append("PROSPERO requires its official host and a CRD registration identifier.")
        if identifier not in parsed.path or not parsed.path.lower().startswith("/prospero/"):
            issues.append("PROSPERO URL must identify the exact registered record.")
    elif registry == "OSF":
        if host not in {"osf.io", "www.osf.io"} or not re.fullmatch(r"[a-z0-9]{5,}", identifier):
            issues.append("OSF requires its official host and an OSF registration identifier.")
        if parsed.path.strip("/") not in {identifier, f"registrations/{identifier}"}:
            issues.append("OSF URL must identify the exact registration, not a project or draft.")
    else:
        issues.append(
            "Workspace policy accepts PROSPERO or OSF; other mandatory trial registries remain additional obligations."
        )
    return issues


def _local_path(root: Path, relative: str) -> Path:
    value = Path(relative)
    candidate = (root / value).resolve()
    if value.is_absolute() or ".." in value.parts or not candidate.is_relative_to(root.resolve()):
        raise ValueError("Registration evidence must remain inside the active project.")
    return candidate


def _observed_scientific_starts(project_dir: Path) -> list[datetime]:
    """Reconcile known legacy ledgers too; a missing new marker proves nothing."""
    starts = []
    marker = project_dir / START_PATH
    if marker.is_file():
        starts.append(_time(json.loads(marker.read_text(encoding="utf-8"))["started_at"]))
    registry = project_dir / "sources/registry.jsonl"
    if registry.is_file():
        for line in registry.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entry = json.loads(line)
                dates = [entry[key] for key in ("observed_at", "registered_at") if entry.get(key)]
                if not dates:
                    raise ValueError("Undated legacy source record")
                starts.extend(_time(value) for value in dates)
    for path in (project_dir / ".machine/runs").glob("*/manifest.json"):
        run = load_structured_file(path)
        if run.get("mode") not in PLANNING_MODES:
            starts.append(_time(run["started_at"]))
    return starts


def _verification_issues(project_dir: Path, registration: dict[str, Any], record: dict[str, Any]) -> list[str]:
    if not isinstance(registration, dict) or not isinstance(record, dict):
        return ["Registration declaration and verification must be JSON objects."]
    issues = _registry_identity(
        str(registration.get("registry", "")),
        str(registration.get("registry_id", "")),
        str(registration.get("registry_url", "")),
    )
    for key in ("registry", "registry_id", "registry_url", "registered_at"):
        if record.get(key) != registration.get(key):
            issues.append(f"Registration verification does not match {key}.")
    if record.get("record_kind") != "registration" or record.get("registration_final") is not True:
        issues.append(
            "A final registry registration is required; projects, drafts and pending submissions do not qualify."
        )
    if record.get("protocol_matches_record") is not True:
        issues.append("A reviewer must confirm that the frozen protocol matches the registry record.")
    if record.get("protocol_sha256") != protocol_fingerprint(project_dir):
        issues.append("Protocol changed after verification; review and document an amendment before continuing.")
    if not isinstance(record.get("reviewer"), str) or not record["reviewer"].strip():
        issues.append("A named reviewer of the registry evidence is required.")
    if record.get("scientific_work_not_started_before_registration") is not True:
        issues.append(
            "The reviewer must explicitly reconcile prior work, including legacy and outside-pipeline activity."
        )
    if record.get("verification_method") != "reviewed-hashed-registry-record":
        issues.append("Registration verification method must identify review of a hashed registry record.")
    try:
        registered = _time(registration.get("registered_at", ""))
        verified = _time(record.get("verified_at", ""))
        if registered > verified or verified > datetime.now(UTC):
            issues.append("Registration/verification dates are inconsistent or in the future.")
        starts = _observed_scientific_starts(project_dir)
        if any(registered > observed for observed in starts):
            issues.append(
                "Registration postdates recorded scientific work; retrospective registration cannot satisfy this gate."
            )
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        issues.append("Valid registration, verification and legacy scientific-start records are required.")
    try:
        source = _local_path(project_dir, str(record.get("source_record_path", "")))
        if not source.is_file() or source.stat().st_size == 0:
            issues.append("The reviewed registry record is missing or empty.")
        elif hashlib.sha256(source.read_bytes()).hexdigest() != record.get("source_record_sha256"):
            issues.append("The registry evidence hash does not match its reviewed content.")
    except (OSError, ValueError):
        issues.append("The registry record path is invalid or unavailable.")
    return issues


def verify_protocol_registration(project_dir: Path, reviewed_record: Path) -> dict[str, Any]:
    """Import an explicit source-review record; never create an external registration."""
    root = Path(project_dir).resolve()
    source = Path(reviewed_record).resolve()
    if not source.is_relative_to(root):
        raise ValueError("Reviewed registration metadata must be inside the active project.")
    record = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValueError("Registration review metadata must be a JSON object.")
    protocol = load_structured_file(root / "protocol.yaml")
    registration = protocol.get("registration", {})
    if not isinstance(registration, dict):
        return {
            "contract": "ProtocolRegistrationVerificationV1",
            "status": "blocked",
            "issues": ["Registration declaration must be an object."],
        }
    issues = _verification_issues(root, registration, record)
    if issues:
        return {"contract": "ProtocolRegistrationVerificationV1", "status": "blocked", "issues": issues}
    destination = root / VERIFICATION_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    canonical = json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    destination.write_text(canonical, encoding="utf-8")
    registration.update(
        required=True,
        status="registered",
        verification_path=VERIFICATION_PATH,
        verification_sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
        registered_before_extraction=True,
        registered_before_scientific_work=True,
    )
    protocol["registration"] = registration
    save_structured_file(root / "protocol.yaml", protocol)
    return {
        "contract": "ProtocolRegistrationVerificationV1",
        "status": "pass",
        "issues": [],
        "verification_scope": "local review of hashed registry evidence; not independent live authenticity proof",
    }


def registration_gate(project_dir: Path, action: str, *, mark_started: bool = False) -> dict[str, Any]:
    root = Path(project_dir).resolve()
    if not registration_required(root):
        return {"contract": "ProtocolRegistrationGateV1", "status": "pass", "required": False, "issues": []}
    protocol = load_structured_file(root / "protocol.yaml")
    registration = protocol.get("registration", {})
    if not isinstance(registration, dict):
        return {
            "contract": "ProtocolRegistrationGateV1",
            "status": "blocked",
            "required": True,
            "issues": ["Registration declaration must be an object."],
        }
    issues = []
    if protocol.get("status") not in {"frozen", "approved", "locked"}:
        issues.append("The scientific protocol must be explicitly frozen before execution.")
    if registration.get("status") != "registered":
        issues.append("protocol.yaml registration.status must be registered AND verified before scientific work.")
    try:
        path = _local_path(root, str(registration.get("verification_path", "")))
        if not path.is_file():
            raise ValueError("missing verification")
        if hashlib.sha256(path.read_bytes()).hexdigest() != registration.get("verification_sha256"):
            issues.append("Registration verification artifact changed after approval.")
        record = json.loads(path.read_text(encoding="utf-8"))
        issues.extend(_verification_issues(root, registration, record))
    except (OSError, ValueError, TypeError):
        issues.append(
            "Verified PROSPERO/OSF evidence is required before corpus, screening, extraction, "
            "analysis or manuscript execution."
        )
    if not issues and mark_started:
        start = root / START_PATH
        start.parent.mkdir(parents=True, exist_ok=True)
        try:
            with start.open("x", encoding="utf-8") as handle:
                json.dump(
                    {
                        "started_at": datetime.now(UTC).isoformat(),
                        "action": action,
                        "registry_id": registration["registry_id"],
                    },
                    handle,
                    indent=2,
                )
        except FileExistsError:
            pass
    return {
        "contract": "ProtocolRegistrationGateV1",
        "status": "blocked" if issues else "pass",
        "required": True,
        "action": action,
        "issues": issues,
        "policy": "user-required-registration-before-scientific-work",
    }
