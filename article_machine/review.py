from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import yaml

from .evidence import validate_evidence_lock
from .ptbr_style import audit_paths, render_markdown_report
from .serialization import load_structured_file, save_structured_file
from .policy.gates import workspace_snapshot, file_sha256


def _review_evidence(path: Path, contract: str, protected_snapshot: dict) -> dict:
    issues: list[str] = []
    try:
        evidence = load_structured_file(path)
    except (OSError, UnicodeError, yaml.YAMLError):
        evidence = {}
        issues.append(f"{path.name} is missing or unreadable.")
    if evidence.get("contract") != contract:
        issues.append(f"{path.name} must use {contract}.")
    if evidence.get("independent") is not True:
        issues.append(f"{path.name} must declare independent=true.")
    if evidence.get("status") != "pass":
        issues.append(f"{path.name} status is not pass.")
    reviewer_id = evidence.get("reviewer_id")
    if not isinstance(reviewer_id, str) or len(reviewer_id.strip()) < 3:
        issues.append(f"{path.name} must identify an independent reviewer.")
    if not isinstance(evidence.get("reviewed_at"), str) or not evidence["reviewed_at"].strip():
        issues.append(f"{path.name} must record reviewed_at.")
    assessment = evidence.get("assessment")
    if not isinstance(assessment, str) or len(assessment.strip()) < 40:
        issues.append(f"{path.name} must contain a substantive reviewer assessment.")
    if evidence.get("input_snapshot") != protected_snapshot:
        issues.append(f"{path.name} is missing or stale for protected scientific inputs.")
    return {"status": "pass" if not issues else "block", "issues": issues, "reviewer_id": reviewer_id}


def _checklist_issues(standards: dict) -> list[str]:
    guidelines = standards.get("guidelines", [])
    bias_tools = standards.get("risk_of_bias_tools", [])
    requirements = [
        *(guidelines if isinstance(guidelines, list) else []),
        *(bias_tools if isinstance(bias_tools, list) else []),
    ]
    if any(not isinstance(requirement, str) or not requirement.strip() for requirement in requirements):
        return ["Standards guidelines/checklist requirements are malformed."]
    checklist = standards.get("checklist_status")
    if not requirements:
        return ["Standards guidelines/checklist requirements are missing."]
    if not isinstance(checklist, dict) or not checklist:
        return ["Standards checklist_status is missing or malformed."]
    issues: list[str] = []
    for requirement in requirements:
        item = checklist.get(requirement)
        status = item.get("status") if isinstance(item, dict) else item
        if status != "pass":
            issues.append(f"Standards checklist item '{requirement}' is not pass.")
    for item_name, item in checklist.items():
        if item_name in requirements:
            continue
        status = item.get("status") if isinstance(item, dict) else item
        if status != "pass":
            issues.append(f"Standards checklist item '{item_name}' is not pass.")
    return issues


def _aggregate_status(statuses: list[str]) -> str:
    if "block" in statuses:
        return "block"
    if "revise" in statuses:
        return "revise"
    if all(status == "pass" for status in statuses):
        return "pass"
    return "pending"


def _run_configured_ptbr_style_audit(project_dir: Path, standards: dict) -> dict:
    policy = standards.get("ptbr_style_policy") or {}
    if not policy.get("enabled"):
        return {"status": "pass", "issues": []}

    configured_paths = policy.get("audit_paths") or []
    paths: list[Path] = []
    missing_paths: list[str] = []
    for item in configured_paths:
        path = project_dir / item
        if path.exists():
            paths.append(path)
        else:
            missing_paths.append(str(item))

    issues = [f"PT-BR style audit path is missing: {item}" for item in missing_paths]
    if paths:
        payload = audit_paths(paths)
        save_structured_file(project_dir / "reviews" / "ptbr_style_audit.json", payload)
        (project_dir / "reviews" / "ptbr_style_audit.md").write_text(
            render_markdown_report(payload["reports"]),
            encoding="utf-8",
        )
        if payload["status"] == "block":
            issues.append(f"PT-BR style audit blocked {payload['issue_count']} issue(s).")
    elif not missing_paths:
        issues.append("PT-BR style audit is enabled, but no audit_paths were configured.")

    return {"status": "block" if issues else "pass", "issues": issues}


def run_review_trinity(project_dir: Path) -> dict:
    project_dir = Path(project_dir)
    protocol = load_structured_file(project_dir / "protocol.yaml")
    standards = load_structured_file(project_dir / "standards.yaml")
    protected_snapshot = workspace_snapshot(project_dir)
    evidence_report = validate_evidence_lock(project_dir)

    methodological_issues = []
    if protocol.get("status") not in {"frozen", "approved", "locked"}:
        methodological_issues.append("Protocol is not frozen.")
    methodological_issues.extend(_checklist_issues(standards))
    methodological_evidence = _review_evidence(
        project_dir / "reviews" / "methodological_review.json",
        "MethodologicalReviewEvidenceV1",
        protected_snapshot,
    )
    methodological_issues.extend(methodological_evidence["issues"])
    methodological_status = "pass" if not methodological_issues else "block"

    quantitative_issues = []
    quantitative_config = standards.get("quantitative_review") or {}
    if quantitative_config.get("enabled") is not True:
        quantitative_issues.append("quantitative_review configuration is missing or disabled.")
    manifest_path = project_dir / "analysis" / "manifest.json"
    try:
        manifest_present = manifest_path.is_file() and bool(manifest_path.read_bytes().strip())
    except OSError:
        manifest_present = False
    if not manifest_present:
        quantitative_issues.append("analysis/manifest.json is required and must be non-empty for quantitative review.")
    quantitative_evidence = _review_evidence(
        project_dir / "reviews" / "quantitative_review.json",
        "QuantitativeReviewEvidenceV1",
        protected_snapshot,
    )
    quantitative_issues.extend(quantitative_evidence["issues"])
    if standards.get("lane") == "computational-discovery":
        quantitative_issues.append("Discovery outputs require benchmark review before submission.")
    quantitative_status = "pass" if not quantitative_issues else "block"

    ptbr_style_report = _run_configured_ptbr_style_audit(project_dir, standards)
    editorial_issues = list(evidence_report["issues"]) + ptbr_style_report["issues"]
    editorial_status = "pass" if evidence_report["status"] == "pass" and ptbr_style_report["status"] == "pass" else "block"

    red_team_path = project_dir / "reviews" / "red_team_report.json"
    red_team = load_structured_file(red_team_path)
    red_team_issues: list[str] = []
    if red_team.get("contract") != "ScientificRedTeamReportV2":
        red_team_issues.append("Independent ScientificRedTeamReportV2 is missing.")
    if red_team.get("independent") is not True:
        red_team_issues.append("Red-team report must declare independent=true.")
    if red_team.get("status") != "pass":
        red_team_issues.append("Red-team report status is not pass.")
    if red_team.get("input_snapshot") != protected_snapshot:
        red_team_issues.append("Red-team report is missing or stale for protected scientific inputs; rerun the independent review.")
    red_team_status = "pass" if not red_team_issues else "block"

    reviewers = {
        "methodological": {"status": methodological_status, "issues": methodological_issues},
        "quantitative": {"status": quantitative_status, "issues": quantitative_issues},
        "editorial": {"status": editorial_status, "issues": editorial_issues},
        "red_team": {"status": red_team_status, "issues": red_team_issues},
    }
    report = {
        "contract": "ReviewTrinityReportV2",
        "contract_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "aggregate_status": _aggregate_status([item["status"] for item in reviewers.values()]),
        "gate_eligible": all(item["status"] == "pass" for item in reviewers.values()),
        # Bind reviewer output to the exact project inputs and red-team artifact
        # that were inspected. gate_mode checks this snapshot before submission.
        "review_snapshot": protected_snapshot,
        "red_team_sha256": file_sha256(red_team_path),
        "reviewers": reviewers,
    }
    save_structured_file(project_dir / "reviews" / "review_report.json", report)
    return report
