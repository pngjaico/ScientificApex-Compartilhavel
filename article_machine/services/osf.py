"""OSF (Open Science Framework) API v2 client and protocol registration bridge.

Provides secure token discovery, connectivity checks, registration metadata retrieval,
and automated evidence snapshotting for Article Machine's fail-closed registration gates.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..projects import register_review_protocol
from .protocol_registration import protocol_fingerprint

OSF_API_BASE = "https://api.osf.io/v2"
OSF_USER_AGENT = "ArticleMachine/0.3.0"


def get_osf_token(workspace_root: Path | None = None) -> str | None:
    """Discover OSF personal access token from environment or local .env file.

    Never logs, prints or stages the discovered token.
    """
    token = os.environ.get("OSF_TOKEN") or os.environ.get("OSF_API_KEY")
    if token and token.strip():
        return token.strip()

    root = Path(workspace_root) if workspace_root else Path.cwd()
    env_file = root / ".env"
    if env_file.is_file():
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key in {"OSF_TOKEN", "OSF_API_KEY"} and val:
                        return val
        except (OSError, UnicodeDecodeError):
            pass
    return None


def verify_osf_connection(token: str | None = None, workspace_root: Path | None = None) -> dict[str, Any]:
    """Verify live connectivity and authentication against OSF API v2 /users/me/.

    Returns sanitized account status without exposing credentials.
    """
    effective_token = token or get_osf_token(workspace_root)
    url = f"{OSF_API_BASE}/users/me/"
    headers = {"User-Agent": OSF_USER_AGENT, "Accept": "application/vnd.api+json"}
    if effective_token:
        headers["Authorization"] = f"Bearer {effective_token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
            data = payload.get("data", {})
            user_id = data.get("id")
            attrs = data.get("attributes", {})
            full_name = attrs.get("full_name", "")
            return {
                "status": "pass",
                "authenticated": bool(effective_token),
                "user_id": user_id,
                "full_name": full_name,
                "date_registered": attrs.get("date_registered"),
                "token_configured": bool(effective_token),
            }
    except urllib.error.HTTPError as exc:
        msg = f"HTTP {exc.code}: {exc.reason}"
        if exc.code == 401:
            msg = "OSF API rejected authentication token (401 Unauthorized)."
        elif exc.code == 403:
            msg = "OSF API access forbidden (403 Forbidden)."
        return {"status": "blocked", "issues": [msg], "token_configured": bool(effective_token)}
    except urllib.error.URLError as exc:
        return {
            "status": "blocked",
            "issues": [f"Network error contacting OSF API ({exc.reason})."],
            "token_configured": bool(effective_token),
        }
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "status": "blocked",
            "issues": [f"Unexpected error parsing OSF response: {exc}"],
            "token_configured": bool(effective_token),
        }


def fetch_osf_registration(
    registration_id: str,
    token: str | None = None,
    workspace_root: Path | None = None,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """Retrieve and validate official registration metadata from OSF API v2.

    Enforces that the record is a finalized registration (not a project or pending draft).
    """
    clean_id = registration_id.strip().lower()
    if not re.fullmatch(r"[a-z0-9]{5,}", clean_id):
        return {
            "status": "blocked",
            "issues": [
                f"Invalid OSF registration identifier '{registration_id}'. Expected alphanumeric slug (>=5 chars)."
            ],
        }

    effective_token = token or get_osf_token(workspace_root)
    url = f"{OSF_API_BASE}/registrations/{clean_id}/"
    headers = {"User-Agent": OSF_USER_AGENT, "Accept": "application/vnd.api+json"}
    if effective_token:
        headers["Authorization"] = f"Bearer {effective_token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {
                "status": "blocked",
                "issues": [
                    f"OSF registration '{clean_id}' not found (404). "
                    "Ensure this is a registration ID, not a project/node ID, and that you have access."
                ],
            }
        if exc.code == 401:
            return {"status": "blocked", "issues": ["OSF API unauthorized (401). Check OSF_TOKEN."]}
        return {"status": "blocked", "issues": [f"OSF API HTTP error: {exc.code} {exc.reason}"]}
    except urllib.error.URLError as exc:
        return {"status": "blocked", "issues": [f"Network failure reaching OSF API: {exc.reason}"]}

    data = payload.get("data", {})
    record_type = data.get("type")
    if record_type != "registrations":
        return {
            "status": "blocked",
            "issues": [
                f"Record '{clean_id}' returned type '{record_type}'. "
                "Article Machine policy requires a finalized OSF registration, not an OSF project or node."
            ],
        }

    attrs = data.get("attributes", {})
    withdrawn = bool(attrs.get("withdrawn", False))
    pending_reg = bool(attrs.get("pending_registration_approval", False))
    pending_embargo = bool(attrs.get("pending_embargo_approval", False))

    issues = []
    if withdrawn:
        issues.append(f"OSF registration '{clean_id}' is marked as withdrawn.")
    if pending_reg:
        issues.append(f"OSF registration '{clean_id}' is still pending registration approval (not final).")
    if pending_embargo:
        issues.append(f"OSF registration '{clean_id}' is still pending embargo approval (not final).")

    is_final = not issues
    date_registered = attrs.get("date_registered")
    if not date_registered:
        issues.append(f"OSF registration '{clean_id}' does not have a date_registered timestamp.")

    return {
        "status": "pass" if not issues else "blocked",
        "issues": issues,
        "registration_id": clean_id,
        "registration_url": f"https://osf.io/{clean_id}/",
        "title": attrs.get("title", ""),
        "description": attrs.get("description", ""),
        "date_registered": date_registered,
        "date_created": attrs.get("date_created"),
        "date_modified": attrs.get("date_modified"),
        "is_final": is_final,
        "is_public": bool(attrs.get("public", False)),
        "is_embargoed": bool(attrs.get("embargo_end_date")),
        "embargo_end_date": attrs.get("embargo_end_date"),
        "article_doi": attrs.get("article_doi"),
        "raw_payload": payload,
    }


def fetch_and_save_osf_evidence(
    project_dir: Path,
    registration_id: str,
    reviewer: str = "",
    token: str | None = None,
) -> dict[str, Any]:
    """Fetch live OSF registration, save exact JSON snapshot, and scaffold verification.

    1. Fetches metadata from OSF API v2.
    2. Writes evidence/protocol_registration/osf_snapshot_{id}.json with canonical indentation.
    3. Calculates SHA-256 of the snapshot.
    4. Registers OSF metadata in protocol.yaml (declared-unverified).
    5. Writes evidence/protocol_registration/osf_reviewed_record_{id}.json ready for human signing and verify.
    """
    root = Path(project_dir).resolve()
    fetch_result = fetch_osf_registration(registration_id, token=token, workspace_root=root)
    if fetch_result.get("status") != "pass":
        return fetch_result

    reg_id = fetch_result["registration_id"]
    reg_url = fetch_result["registration_url"]
    registered_at = fetch_result["date_registered"]
    raw_payload = fetch_result["raw_payload"]

    evidence_dir = root / "evidence" / "protocol_registration"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    # 1. Canonical snapshot of live OSF record
    snapshot_filename = f"osf_snapshot_{reg_id}.json"
    snapshot_path = evidence_dir / snapshot_filename
    canonical_json = json.dumps(raw_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    snapshot_path.write_text(canonical_json, encoding="utf-8")
    snapshot_sha256 = hashlib.sha256(snapshot_path.read_bytes()).hexdigest()

    # 2. Update protocol.yaml to declared-unverified
    register_review_protocol(
        root, registry="OSF", registry_id=reg_id, registry_url=reg_url, registered_at=registered_at
    )

    # 3. Create reviewable verification record scaffold
    fingerprint = protocol_fingerprint(root)
    review_record = {
        "registry": "OSF",
        "registry_id": reg_id,
        "registry_url": reg_url,
        "registered_at": registered_at,
        "record_kind": "registration",
        "registration_final": fetch_result["is_final"],
        "protocol_matches_record": True,
        "protocol_sha256": fingerprint,
        "reviewer": reviewer.strip(),
        "verified_at": datetime.now(UTC).isoformat() if reviewer.strip() else "",
        "scientific_work_not_started_before_registration": True if reviewer.strip() else False,
        "verification_method": "reviewed-hashed-registry-record",
        "source_record_path": snapshot_path.relative_to(root).as_posix(),
        "source_record_sha256": snapshot_sha256,
        "osf_api_verification": {
            "title": fetch_result["title"],
            "is_public": fetch_result["is_public"],
            "is_embargoed": fetch_result["is_embargoed"],
            "embargo_end_date": fetch_result["embargo_end_date"],
            "fetched_at": datetime.now(UTC).isoformat(),
        },
    }

    scaffold_filename = f"osf_reviewed_record_{reg_id}.json"
    scaffold_path = evidence_dir / scaffold_filename
    scaffold_path.write_text(
        json.dumps(review_record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    return {
        "contract": "OSFRegistrationEvidenceV1",
        "status": "pass",
        "registration_id": reg_id,
        "registration_url": reg_url,
        "title": fetch_result["title"],
        "date_registered": registered_at,
        "snapshot_path": snapshot_path.relative_to(root).as_posix(),
        "snapshot_sha256": snapshot_sha256,
        "scaffold_path": scaffold_path.relative_to(root).as_posix(),
        "next_step": (
            f"Review {scaffold_path.relative_to(root).as_posix()}, fill reviewer if empty, and run: "
            f"article-machine registry verify {project_dir} --record {scaffold_path.relative_to(root).as_posix()}"
        ),
    }
