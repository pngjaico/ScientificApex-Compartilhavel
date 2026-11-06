"""Project-scoped bilingual workflow planning and translation regression checks."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..serialization import load_structured_file, save_structured_file

LANGUAGES = ("en", "pt-BR")
PROJECT_TYPES = {
    "systematic-review",
    "network-meta-analysis",
    "diagnostic-study",
    "observational-study",
    "clinical-trial",
    "animal-study",
    "prediction-model",
    "health-economics",
    "drug-discovery",
    "intestinal-digital-twin",
    "thesis-chapter",
    "machine-governance",
}
PHASES = (
    ("question", "Sol", "context/question_and_alternatives.md", "Protocol question, competing hypotheses, feasibility"),
    ("protocol", "Sol", "protocol.yaml", "Design, endpoints, estimand, registration, deviations"),
    ("retrieval", "Luna", "context/retrieval/", "Dated queries, source identifiers, deduplication, provider caveats"),
    ("screening", "Luna", "evidence/screening/", "Traceable decisions; ambiguous eligibility returns to Sol"),
    ("extraction", "Luna", "evidence/extraction_manifest.json", "Schema validation, locators, units, missing data"),
    ("methods", "Sol", "reviews/methods_review.json", "Bias, confounding, transitivity, sensitivity assumptions"),
    ("analysis", "Luna", "analysis/manifest.json", "Execute approved plan with locked runtime and hashes"),
    ("interpretation", "Sol", "evidence/claim_map.jsonl", "Support assessment, counterevidence, claim calibration"),
    ("writing", "Sol", "drafts/manuscript.md", "Native target-language prose and preserved claim/reference keys"),
    ("review", "Sol", "reviews/review_report.json", "Methodological, quantitative, editorial, independent red-team"),
)


def _confined_file(project: Path, value: str) -> Path:
    candidate = (project / value).resolve()
    if project not in candidate.parents:
        raise ValueError("artifact path must stay inside the active project")
    return candidate


def plan_scientific_workflow(project_dir: Path, query: str, language: str) -> dict[str, Any]:
    if language not in LANGUAGES:
        raise ValueError("language must be en or pt-BR")
    project = Path(project_dir).resolve()
    contracts = {
        name: load_structured_file(project / f"{name}.yaml") for name in ("project", "protocol", "standards", "compute")
    }
    issues = [
        f"{name}.yaml is missing, empty or not V2"
        for name, value in contracts.items()
        if not value or value.get("contract_version") != 2
    ]
    project_type = contracts["project"].get("project_type")
    if project_type not in PROJECT_TYPES:
        issues.append(f"unsupported project type: {project_type}")
    if not query.strip():
        issues.append("a concrete scientific task is required")
    if issues:
        return {"contract": "ScientificWorkflowPlanV1", "status": "block", "gate_eligible": False, "issues": issues}
    from ..agent_skills import route_workspace_skills
    from .workspace_hygiene import write_active_mode_guide

    route = route_workspace_skills(query, limit=12)
    current_mode_str = str(contracts["project"].get("state", {}).get("current_mode") or "bootstrap")
    flow_bindings = write_active_mode_guide(project, current_mode_str)
    plan: dict[str, Any] = {
        "contract": "ScientificWorkflowPlanV1",
        "status": "planned",
        "gate_eligible": False,
        "created_at": datetime.now(UTC).isoformat(),
        "project_id": contracts["project"].get("id"),
        "project_type": project_type,
        "query": query,
        "language": language,
        "current_mode": contracts["project"].get("state", {}).get("current_mode"),
        "allowed_next_modes": contracts["project"].get("state", {}).get("allowed_next_modes", []),
        "guidelines": contracts["standards"].get("guidelines", []),
        "selected_skills": route["selected_skills"],
        "mandatory_mode_skills": flow_bindings["mandatory_skills"],
        "canonical_mode_commands": flow_bindings["canonical_commands"],
        "allowed_write_paths": flow_bindings["allowed_write_paths"],
        "coordination": {
            "model": "gpt-6.1-sol",
            "effort": "medium",
            "service": "standard",
            "verify_actual_runtime": True,
        },
        "delegation": {
            "exploration": {"model": "gpt-6-luna", "effort": "low"},
            "implementation": {"model": "gpt-6-luna", "effort": "medium"},
            "focused_analysis": {"model": "gpt-6-luna", "effort": "high"},
            "scientific_review": {"model": "gpt-6.1-sol", "effort": "high"},
            "start_with_workers": 1,
            "max_subagents": 3,
            "packet_required_fields": [
                "objective",
                "inputs",
                "allowed_tools",
                "owned_files",
                "expected_artifacts",
                "verification",
                "stop_conditions",
            ],
        },
        "phases": [
            {"id": phase, "owner": owner, "artifact": artifact, "acceptance": acceptance}
            for phase, owner, artifact, acceptance in PHASES
        ],
        "language_contract": {
            "target": language,
            "glossary": "context/terminology_glossary.json",
            "preserve": ["claim_ids", "reference_keys", "study_ids", "numeric_values", "uncertainty", "disclosure"],
        },
        "gates": [
            "protocol registration when required",
            "locked runtime preflight",
            "Evidence Lock V2",
            "Review Trinity V2",
            "independent red-team",
        ],
        "limits": [
            "planning does not advance lifecycle",
            "scientific judgment remains with coordinator",
            "plugins are optional retrieval aids",
        ],
    }
    save_structured_file(project / "context" / "scientific_workflow_plan.json", plan)
    lines = [
        "# Scientific workflow packet",
        "",
        f"Language: {language}",
        f"Task: {query}",
        "",
        "## Execution assignments",
    ]
    lines.extend(
        f"- {item['id']}: {item['owner']} -> `{item['artifact']}`; {item['acceptance']}" for item in plan["phases"]
    )
    lines.extend(
        [
            "",
            "Read the selected skills and project contracts. Check the next allowed mode before execution.",
            "Each worker returns artifact paths, hashes, exact tests and unresolved issues.",
            "Planning is not an approval of claims or analysis.",
        ]
    )
    packet = project / "context" / "scientific_workflow_packet.md"
    packet.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return plan


def _text_signatures(text: str) -> dict[str, list[str]]:
    return {
        "claim_ids": sorted(re.findall(r"\{\{claim:([\w.-]+)\}\}", text)),
        "citation_keys": sorted(re.findall(r"(?<![\w])@([A-Za-z][A-Za-z0-9_.:-]*)", text)),
        "numeric_values": sorted(
            value.replace(",", ".") for value in re.findall(r"(?<![\w])[-+]?\d+(?:[.,]\d+)?(?:%|\b)", text)
        ),
        "inequalities": sorted(re.findall(r"[<>]=?|≤|≥", text)),
    }


def audit_language(
    project_dir: Path, language: str, draft: str = "drafts/manuscript.md", reference: str | None = None
) -> dict[str, Any]:
    if language not in LANGUAGES:
        raise ValueError("language must be en or pt-BR")
    project = Path(project_dir).resolve()
    target = _confined_file(project, draft)
    issues: list[str] = []
    if not target.is_file():
        issues.append(f"draft is absent: {draft}")
        text = ""
    else:
        text = target.read_text(encoding="utf-8-sig")
    if not text.strip():
        issues.append("draft is empty")
    signatures = _text_signatures(text)
    if reference:
        original = _confined_file(project, reference)
        if not original.is_file():
            issues.append(f"reference draft is absent: {reference}")
        else:
            baseline = _text_signatures(original.read_text(encoding="utf-8-sig"))
            for field, values in signatures.items():
                if values != baseline[field]:
                    issues.append(f"translation changed {field}")
    report: dict[str, Any] = {
        "contract": "BilingualScientificAuditV1",
        "status": "block" if issues else "pass",
        "language": language,
        "draft": draft,
        "reference": reference,
        "signatures": signatures,
        "issues": issues,
        "gate_eligible": False,
        "semantic_review_required": True,
        "limits": ["lexical preservation does not prove semantic equivalence or claim support"],
    }
    if language == "pt-BR" and text:
        from ..ptbr_style import audit_text

        report["native_style"] = audit_text(text, path=target)
    save_structured_file(project / "reviews" / f"language_audit_{language}.json", report)
    return report
