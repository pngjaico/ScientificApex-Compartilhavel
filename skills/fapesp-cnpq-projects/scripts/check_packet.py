"""Structural checks only; no scientific or submission-readiness certification."""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
from urllib.parse import urlparse

import yaml


def check_packet(packet: object, today: date | None = None) -> dict:
    today = today or date.today()
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(packet, dict):
        return {"status": "block", "errors": ["packet must be a mapping"], "warnings": []}

    def nonempty(value: object) -> bool:
        return isinstance(value, str) and bool(value.strip()) and value.strip().upper() not in {"PENDENTE", "TODO"}

    def checked_date(value: object, label: str) -> date | None:
        try:
            parsed = date.fromisoformat(str(value))
        except ValueError:
            errors.append(f"{label}: missing or invalid ISO date")
            return None
        if parsed > today:
            errors.append(f"{label}: future date")
        elif (today - parsed).days > 30:
            warnings.append(f"{label}: older than 30 days; recheck live rules (local freshness heuristic)")
        return parsed

    if packet.get("agency") not in ("FAPESP", "CNPq"):
        errors.append("agency must be FAPESP or CNPq")
    for key in ("modality", "call_id", "status"):
        if not nonempty(packet.get(key)):
            errors.append(f"{key}: missing")
    checked_date(packet.get("verified_on"), "verified_on")
    sources = packet.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("sources: nonempty list required")
        sources = []
    indexed: dict[str, dict] = {}
    for source in sources:
        if not isinstance(source, dict) or not nonempty(source.get("id")):
            errors.append("source: mapping with id required")
            continue
        sid = source["id"]
        if sid in indexed:
            errors.append(f"source {sid}: duplicate id")
        indexed[sid] = source
        url = urlparse(str(source.get("url", "")))
        host = url.hostname or ""
        allowed = host == "fapesp.br" or host.endswith(".fapesp.br") or host == "gov.br" or host.endswith(".gov.br") or host == "cnpq.br" or host.endswith(".cnpq.br")
        if url.scheme != "https" or not allowed:
            errors.append(f"source {sid}: official HTTPS URL required; content still needs manual verification")
        if not nonempty(source.get("version")):
            errors.append(f"source {sid}: version missing")
        checked_date(source.get("accessed_on"), f"source {sid} accessed_on")
        if source.get("role") not in ("current-rule", "historical-example"):
            errors.append(f"source {sid}: invalid role")

    def current_source(sid: object, label: str) -> None:
        source = indexed.get(str(sid))
        if source is None:
            errors.append(f"{label}: unknown source_id")
        elif source.get("role") != "current-rule":
            errors.append(f"{label}: historical example cannot establish a current requirement")

    requirements = packet.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        errors.append("requirements: nonempty list required")
        requirements = []
    for req in requirements:
        if not isinstance(req, dict):
            errors.append("requirement must be a mapping")
            continue
        label = f"requirement {req.get('id')}"
        for key in ("id", "locator", "rule"):
            if not nonempty(req.get(key)):
                errors.append(f"{label}: {key} missing")
        if req.get("kind") not in ("mandatory", "recommended"):
            errors.append(f"{label}: invalid kind")
        if req.get("verified") is not True:
            errors.append(f"{label}: unverified")
        current_source(req.get("source_id"), label)
    fields = packet.get("fields", [])
    if not isinstance(fields, list):
        errors.append("fields must be a list")
        fields = []
    for field in fields:
        if not isinstance(field, dict):
            errors.append("field must be a mapping")
            continue
        label = f"field {field.get('name')}"
        limit, value = field.get("limit"), field.get("text")
        if not nonempty(field.get("name")) or not nonempty(value):
            errors.append(f"{label}: name and text required")
        if type(limit) is not int or limit <= 0:
            errors.append(f"{label}: positive integer character limit required")
        elif isinstance(value, str) and len(value) > limit:
            errors.append(f"{label}: {len(value)} characters exceeds {limit}")
        current_source(field.get("source_id"), label)
    pending = packet.get("pending", [])
    if not isinstance(pending, list):
        errors.append("pending must be a list")
    elif pending:
        errors.append(f"pending: {len(pending)} unresolved items")
    return {"status": "block" if errors else "pass-structural-only", "errors": errors, "warnings": warnings,
            "limits": "Does not verify source truth, eligibility, complete requirements, scientific merit, pages, layout, budget, references or portal."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    args = parser.parse_args()
    try:
        report = check_packet(yaml.safe_load(args.packet.read_text(encoding="utf-8")))
    except (OSError, yaml.YAMLError) as exc:
        report = {"status": "block", "errors": [str(exc)], "warnings": []}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["status"] == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
