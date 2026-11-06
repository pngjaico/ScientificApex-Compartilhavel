"""Methodology Perfection Engine: Protocol validation, PROSPERO/OSF packet compilation, and EQUATOR compliance.

Enforces design-specific methodological completeness (PICO/PICOTS, Estimands, SAP, Bias Domains),
generates paired PT-BR/EN registration packets for PROSPERO and OSF, and audits machine-readable
EQUATOR checklists (PRISMA 2020, PRISMA-NMA, TRIPOD+AI, PROBAST+AI, STARD 2015, QUADAS-2, STROBE, CONSORT 2025).
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..serialization import load_structured_file, save_structured_file
from .protocol_registration import protocol_fingerprint

EQUATOR_SCHEMAS: dict[str, dict[str, Any]] = {
    "PRISMA 2020": {
        "guideline": "PRISMA 2020",
        "project_types": ["systematic-review"],
        "required_protocol_fields": [
            "research_question",
            "pico.population",
            "pico.intervention",
            "pico.comparator",
            "pico.outcomes",
            "eligibility.inclusion",
            "eligibility.exclusion",
            "information_sources",
            "risk_of_bias_tool",
            "synthesis_plan.effect_measure",
            "synthesis_plan.model",
            "synthesis_plan.heterogeneity",
            "certainty_assessment",
        ],
        "required_manuscript_Markers": [
            "PRISMA",
            "eligibility",
            "risk of bias",
            "heterogeneity",
            "GRADE",
            "limitations",
        ],
        "items": [
            {
                "id": "PRISMA-01",
                "section": "Title",
                "requirement": "Identify report as a systematic review / meta-analysis.",
            },
            {
                "id": "PRISMA-05",
                "section": "Methods",
                "requirement": "Specify inclusion and exclusion criteria and PICO.",
            },
            {
                "id": "PRISMA-06",
                "section": "Methods",
                "requirement": "Specify all databases, registers, dates of coverage.",
            },
            {
                "id": "PRISMA-07",
                "section": "Methods",
                "requirement": "Present full search strategies for all databases.",
            },
            {
                "id": "PRISMA-11",
                "section": "Methods",
                "requirement": "Specify methods used to assess risk of bias in included studies.",
            },
            {
                "id": "PRISMA-13",
                "section": "Methods",
                "requirement": "Describe synthesis methods, model (REML/HKSJ), and heterogeneity.",
            },
            {
                "id": "PRISMA-15",
                "section": "Methods",
                "requirement": "Describe methods to assess certainty (GRADE) in body of evidence.",
            },
            {
                "id": "PRISMA-24",
                "section": "Other",
                "requirement": "Provide registration information (PROSPERO/OSF) and protocol deviations.",
            },
        ],
    },
    "PRISMA-NMA": {
        "guideline": "PRISMA-NMA",
        "project_types": ["network-meta-analysis"],
        "required_protocol_fields": [
            "research_question",
            "pico.population",
            "pico.interventions",
            "pico.outcomes",
            "network_plan.geometry",
            "network_plan.transitivity_assumption",
            "network_plan.inconsistency_assessment",
            "network_plan.ranking_metric",
            "risk_of_bias_tool",
            "certainty_assessment",
        ],
        "required_manuscript_Markers": [
            "PRISMA-NMA",
            "network",
            "transitivity",
            "inconsistency",
            "ranking",
        ],
        "items": [
            {
                "id": "NMA-S1",
                "section": "Methods",
                "requirement": "Describe treatment nodes, network geometry, and transitivity modifiers.",
            },
            {
                "id": "NMA-S2",
                "section": "Methods",
                "requirement": "Specify global and local inconsistency models (node-splitting / design-by-treatment).",
            },
            {
                "id": "NMA-S3",
                "section": "Results",
                "requirement": (
                    "Present network plot, league table with 95% CIs, and treatment ranking "
                    "(SUCRA/P-score) with caveats."
                ),
            },
        ],
    },
    "TRIPOD+AI": {
        "guideline": "TRIPOD+AI",
        "project_types": ["prediction-model"],
        "required_protocol_fields": [
            "research_question",
            "prediction_spec.target_population",
            "prediction_spec.time_zero",
            "prediction_spec.prediction_horizon",
            "prediction_spec.outcome_definition",
            "prediction_spec.candidate_predictors",
            "validation_plan.partition_unit",
            "validation_plan.strategy",
            "validation_plan.baseline_comparator",
            "validation_plan.calibration_metrics",
            "validation_plan.clinical_utility_dca",
            "missing_data_plan",
        ],
        "required_manuscript_Markers": [
            "TRIPOD+AI",
            "calibration",
            "discrimination",
            "validation",
            "limitations",
        ],
        "items": [
            {
                "id": "TRIPOD-01",
                "section": "Title",
                "requirement": "Identify study as developing and/or validating a multivariable prediction model.",
            },
            {
                "id": "TRIPOD-06",
                "section": "Methods",
                "requirement": (
                    "Define time zero (T0), prediction horizon, and outcome assessment blinded to predictors."
                ),
            },
            {
                "id": "TRIPOD-09",
                "section": "Methods",
                "requirement": (
                    "Specify handling of missing data inside training partitions only (no train-test leakage)."
                ),
            },
            {
                "id": "TRIPOD-10",
                "section": "Methods",
                "requirement": "Specify patient-level grouped nested CV / temporal / external validation strategy.",
            },
            {
                "id": "TRIPOD-16",
                "section": "Results",
                "requirement": (
                    "Report discrimination (AUROC/AUPRC with 95% CI), calibration intercept, slope, "
                    "ICI, and DCA Net Benefit."
                ),
            },
        ],
    },
    "PROBAST+AI": {
        "guideline": "PROBAST+AI",
        "project_types": ["prediction-model"],
        "required_protocol_fields": [
            "prediction_spec.target_population",
            "prediction_spec.outcome_definition",
            "validation_plan.partition_unit",
            "missing_data_plan",
        ],
        "required_manuscript_Markers": ["PROBAST+AI", "bias", "applicability"],
        "items": [
            {
                "id": "PROBAST-D1",
                "section": "Participants",
                "requirement": "Appropriate data sources and inclusion criteria without inappropriate exclusions.",
            },
            {
                "id": "PROBAST-D2",
                "section": "Predictors",
                "requirement": "Predictors defined and measured before T0 without knowledge of outcome.",
            },
            {
                "id": "PROBAST-D3",
                "section": "Outcome",
                "requirement": "Outcome determined appropriately without predictor incorporation bias.",
            },
            {
                "id": "PROBAST-D4",
                "section": "Analysis",
                "requirement": (
                    "Adequate events per variable, zero patient leakage, proper calibration and "
                    "internal/external validation."
                ),
            },
        ],
    },
    "STARD 2015": {
        "guideline": "STARD 2015",
        "project_types": ["diagnostic-study"],
        "required_protocol_fields": [
            "research_question",
            "diagnostic_spec.target_condition",
            "diagnostic_spec.index_test",
            "diagnostic_spec.prespecified_cutoff",
            "diagnostic_spec.reference_standard",
            "diagnostic_spec.blinding",
            "analysis_plan.metrics",
        ],
        "required_manuscript_Markers": [
            "STARD",
            "sensitivity",
            "specificity",
            "reference standard",
        ],
        "items": [
            {
                "id": "STARD-07",
                "section": "Methods",
                "requirement": "Define index test positivity cut-offs prespecified vs exploratory.",
            },
            {
                "id": "STARD-08",
                "section": "Methods",
                "requirement": "Define reference standard and blinding between index test and reference standard.",
            },
            {
                "id": "STARD-19",
                "section": "Results",
                "requirement": "Provide 2x2 cross-tabulation (TP, FP, FN, TN) and Sens/Spec/LR+/LR- with 95% CIs.",
            },
        ],
    },
    "STROBE": {
        "guideline": "STROBE",
        "project_types": ["observational-study"],
        "required_protocol_fields": [
            "research_question",
            "study_design",
            "estimand.exposure",
            "estimand.comparator",
            "estimand.outcome",
            "estimand.time_zero_alignment",
            "confounding_plan.dag_variables",
            "missing_data_plan",
        ],
        "required_manuscript_Markers": ["STROBE", "confounding", "bias", "limitations"],
        "items": [
            {
                "id": "STROBE-04",
                "section": "Methods",
                "requirement": (
                    "Present key elements of study design and time-zero alignment (avoid immortal time bias)."
                ),
            },
            {
                "id": "STROBE-07",
                "section": "Methods",
                "requirement": (
                    "Clearly define all outcomes, exposures, predictors, potential confounders, and effect modifiers."
                ),
            },
            {
                "id": "STROBE-12",
                "section": "Methods",
                "requirement": (
                    "Describe statistical methods, confounding adjustment (DAG/IPTW/multivariable), and missing data."
                ),
            },
        ],
    },
    "CONSORT 2025": {
        "guideline": "CONSORT 2025",
        "project_types": ["clinical-trial"],
        "required_protocol_fields": [
            "research_question",
            "pico.population",
            "pico.intervention",
            "pico.comparator",
            "pico.outcomes",
            "randomization_and_blinding",
            "sample_size_justification",
            "estimand.population_analysis_set",
        ],
        "required_manuscript_Markers": ["CONSORT", "random", "allocation", "harms"],
        "items": [
            {
                "id": "CONSORT-06",
                "section": "Methods",
                "requirement": (
                    "Completely define pre-specified primary and secondary outcomes, including how and when assessed."
                ),
            },
            {
                "id": "CONSORT-07",
                "section": "Methods",
                "requirement": (
                    "How sample size was determined and explanation of any interim analyses and stopping guidelines."
                ),
            },
            {
                "id": "CONSORT-08",
                "section": "Methods",
                "requirement": "Method used to generate random allocation sequence, concealment, and blinding.",
            },
        ],
    },
}


def _get_nested(data: dict[str, Any], dotted_path: str) -> Any:
    current: Any = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _is_populated(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        stripped = value.strip()
        return bool(stripped) and stripped.lower() not in {"tbd", "todo", "pending", "a definir", "rascunho"}
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def _schemas_for_project_type(project_type: str) -> list[dict[str, Any]]:
    ptype = (project_type or "").strip().lower()
    matched = [schema for schema in EQUATOR_SCHEMAS.values() if ptype in schema["project_types"]]
    return matched


def validate_protocol_methodology(project_dir: Path) -> dict[str, Any]:
    """Validate that protocol.yaml satisfies design-specific methodological requirements."""
    root = Path(project_dir).resolve()
    project = load_structured_file(root / "project.yaml")
    protocol = load_structured_file(root / "protocol.yaml")
    project_type = str(project.get("project_type") or protocol.get("project_type") or "").strip().lower()

    if project_type == "machine-governance":
        return {
            "contract": "ProtocolMethodologyAuditV1",
            "status": "pass",
            "project_type": project_type,
            "required_fields": [],
            "missing_fields": [],
            "issues": [],
        }

    schemas = _schemas_for_project_type(project_type)
    required_fields: list[str] = ["research_question"]
    for schema in schemas:
        for field in schema["required_protocol_fields"]:
            if field not in required_fields:
                required_fields.append(field)

    missing_fields: list[str] = []
    for field in required_fields:
        val = _get_nested(protocol, field)
        if not _is_populated(val):
            missing_fields.append(field)

    issues: list[str] = []
    if missing_fields:
        issues.append(
            f"Protocol for '{project_type}' is missing mandatory methodological specifications: {missing_fields}"
        )

    # Extra domain-specific checks
    if project_type == "prediction-model":
        part_unit = str(_get_nested(protocol, "validation_plan.partition_unit") or "").lower()
        if part_unit and part_unit not in {"patient", "paciente", "subject", "center", "centro", "cluster"}:
            issues.append(
                "Prediction model partition_unit must prevent patient-level leakage (got "
                f"'{part_unit}'; expected 'patient' or 'center')."
            )

    return {
        "contract": "ProtocolMethodologyAuditV1",
        "status": "pass" if not issues else "blocked",
        "project_type": project_type,
        "guidelines": [s["guideline"] for s in schemas],
        "required_fields": required_fields,
        "missing_fields": missing_fields,
        "protocol_sha256": protocol_fingerprint(root),
        "gate_eligible": False,
        "human_review_required": True,
        "scope": "Required-field presence and limited structural checks; not scientific design approval.",
        "issues": issues,
    }


def _recommended_registry(project_type: str, protocol: dict[str, Any]) -> dict[str, str]:
    ptype = (project_type or "").strip().lower()
    human_health = bool(protocol.get("human_health_outcomes", True))
    if ptype in {"systematic-review", "network-meta-analysis"} and human_health:
        return {
            "primary_registry": "PROSPERO",
            "fallback_registry": "OSF",
            "rationale_pt": (
                "Revisão sistemática/meta-análise com desfechos em saúde humana: elegível "
                "primariamente ao PROSPERO (CRD); caso fora do escopo ou sem desfecho clínico "
                "direto, registrar versão final no OSF."
            ),
            "rationale_en": (
                "Systematic review/meta-analysis with human health outcomes: primarily eligible for "
                "PROSPERO (CRD); if outside scope, register a final OSF Preregistration."
            ),
        }
    return {
        "primary_registry": "OSF",
        "fallback_registry": "PROSPERO",
        "rationale_pt": (
            f"Desenho '{ptype}': o registro prospectivo final deve ser realizado no OSF "
            "Preregistration (e registro adicional de ensaio clínico/ética quando aplicável)."
        ),
        "rationale_en": (
            f"Design '{ptype}': prospective final registration should use OSF Preregistration "
            "(plus applicable clinical trial registry and ethics approval)."
        ),
    }


def compile_registration_packet(project_dir: Path) -> dict[str, Any]:
    """Compile paired PT-BR/EN protocol registration packets and OSF/PROSPERO JSON submission payload.

    Requires that validate_protocol_methodology passes first.
    """
    root = Path(project_dir).resolve()
    audit = validate_protocol_methodology(root)
    if audit["status"] != "pass":
        return {
            "contract": "ProtocolRegistrationPacketV1",
            "status": "blocked",
            "issues": audit["issues"],
            "missing_fields": audit["missing_fields"],
        }

    project = load_structured_file(root / "project.yaml")
    protocol = load_structured_file(root / "protocol.yaml")
    project_type = audit["project_type"]
    fp = audit["protocol_sha256"]
    route = _recommended_registry(project_type, protocol)
    title = str(protocol.get("title") or project.get("name") or root.name)
    question = str(protocol.get("research_question", ""))
    generated_at = datetime.now(UTC).isoformat()

    # Build structured submission payload compatible with OSF Preregistration & PROSPERO fields
    substantive_protocol = {k: v for k, v in protocol.items() if k not in {"registration", "status"}}
    submission_payload = {
        "contract": "RegistrySubmissionPayloadV1",
        "project_id": project.get("project_id") or root.name,
        "title": title,
        "project_type": project_type,
        "recommended_registry": route["primary_registry"],
        "fallback_registry": route["fallback_registry"],
        "guidelines": audit["guidelines"],
        "protocol_sha256": fp,
        "generated_at": generated_at,
        "research_question": question,
        "osf_preregistration_schema": {
            "title": title,
            "description": question,
            "category": "project",
            "registration_supplement": "OSF Preregistration",
            "specification": substantive_protocol,
        },
        "prospero_crd_mapping": {
            "1_review_title": title,
            "15_review_question": question,
            "16_searches": protocol.get("information_sources", []),
            "18_condition_or_domain": _get_nested(protocol, "pico.population")
            or _get_nested(protocol, "prediction_spec.target_population"),
            "19_participants_population": _get_nested(protocol, "pico.population")
            or _get_nested(protocol, "prediction_spec.target_population"),
            "20_interventions_exposures": _get_nested(protocol, "pico.intervention")
            or _get_nested(protocol, "pico.interventions"),
            "21_comparators_control": _get_nested(protocol, "pico.comparator"),
            "24_main_outcomes": _get_nested(protocol, "pico.outcomes")
            or _get_nested(protocol, "prediction_spec.outcome_definition"),
            "27_risk_of_bias_quality": protocol.get("risk_of_bias_tool"),
            "28_strategy_for_data_synthesis": protocol.get("synthesis_plan")
            or protocol.get("validation_plan")
            or protocol.get("analysis_plan"),
        },
    }

    evidence_dir = root / "evidence" / "protocol_registration"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    json_packet_path = evidence_dir / "registration_submission_packet.json"
    json_packet_path.write_text(
        json.dumps(submission_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    packet_sha256 = hashlib.sha256(json_packet_path.read_bytes()).hexdigest()

    # Paired PT-BR and EN Markdown protocol packets
    pt_dir = root / "context" / "protocolo_registravel" / "portugues"
    en_dir = root / "context" / "protocolo_registravel" / "ingles"
    pt_dir.mkdir(parents=True, exist_ok=True)
    en_dir.mkdir(parents=True, exist_ok=True)

    spec_json_str = json.dumps(substantive_protocol, ensure_ascii=False, indent=2, sort_keys=True)

    pt_md = (
        f"# Pacote de Protocolo Congelado para Registro ({route['primary_registry']} / "
        f"{route['fallback_registry']})\n\n"
        f"- **Título:** {title}\n"
        f"- **Tipo de Estudo:** `{project_type}`\n"
        f"- **Diretrizes EQUATOR:** {', '.join(audit['guidelines'])}\n"
        f"- **Registro Primário Recomendado:** `{route['primary_registry']}` ({route['rationale_pt']})\n"
        f"- **Fingerprint SHA-256 do Protocolo (`protocol_sha256`):** `{fp}`\n"
        f"- **SHA-256 do Payload de Submissão:** `{packet_sha256}`\n\n"
        f"## 1. Pergunta de Pesquisa\n\n{question}\n\n"
        f"## 2. Especificação Metodológica Completa\n\n```json\n{spec_json_str}\n```\n\n"
        f"## 3. Próximos Passos para Registro Oficial\n\n"
        f"1. Submeta este protocolo congelado no **{route['primary_registry']}** (ou "
        f"**{route['fallback_registry']}**).\n"
        f"2. Caso registrado no OSF, execute:\n"
        f'   `python -m article_machine registry fetch-osf {root.as_posix()} --id <OSF_ID> --reviewer "<Nome>"`\n'
        f"3. Verifique o registro final com:\n"
        f"   `python -m article_machine registry verify {root.as_posix()} --record <CAMINHO_JSON_REVISADO>`\n"
    )

    en_md = (
        f"# Frozen Protocol Registration Packet ({route['primary_registry']} / {route['fallback_registry']})\n\n"
        f"- **Title:** {title}\n"
        f"- **Study Design:** `{project_type}`\n"
        f"- **EQUATOR Guidelines:** {', '.join(audit['guidelines'])}\n"
        f"- **Primary Recommended Registry:** `{route['primary_registry']}` ({route['rationale_en']})\n"
        f"- **Protocol Fingerprint SHA-256 (`protocol_sha256`):** `{fp}`\n"
        f"- **Submission Payload SHA-256:** `{packet_sha256}`\n\n"
        f"## 1. Research Question\n\n{question}\n\n"
        f"## 2. Complete Methodological Specification\n\n```json\n{spec_json_str}\n```\n\n"
        f"## 3. Next Steps for Official Registration\n\n"
        f"1. Submit this frozen protocol to **{route['primary_registry']}** (or **{route['fallback_registry']}**).\n"
        f"2. Once finalized on OSF, run:\n"
        f'   `python -m article_machine registry fetch-osf {root.as_posix()} --id <OSF_ID> --reviewer "<Name>"`\n'
        f"3. Verify the finalized registration with:\n"
        f"   `python -m article_machine registry verify {root.as_posix()} --record <REVIEWED_JSON_PATH>`\n"
    )

    pt_file = pt_dir / "pacote_registro_protocolo.md"
    en_file = en_dir / "pacote_registro_protocolo.md"
    pt_file.write_text(pt_md, encoding="utf-8")
    en_file.write_text(en_md, encoding="utf-8")

    return {
        "contract": "ProtocolRegistrationPacketV1",
        "status": "pass",
        "project_type": project_type,
        "recommended_registry": route["primary_registry"],
        "protocol_sha256": fp,
        "json_packet_path": json_packet_path.relative_to(root).as_posix(),
        "packet_sha256": packet_sha256,
        "paired_deliverables": {
            "portugues": pt_file.relative_to(root).as_posix(),
            "ingles": en_file.relative_to(root).as_posix(),
        },
        "issues": [],
    }


def audit_equator_compliance(project_dir: Path, update_standards: bool = False) -> dict[str, Any]:
    """Audit protocol and manuscript drafts against machine-readable EQUATOR checklists."""
    root = Path(project_dir).resolve()
    project = load_structured_file(root / "project.yaml")
    standards = load_structured_file(root / "standards.yaml")
    project_type = str(project.get("project_type") or standards.get("project_type") or "").strip().lower()

    proto_audit = validate_protocol_methodology(root)
    schemas = _schemas_for_project_type(project_type)

    # Collect manuscript text if present (ignoring default un-drafted '# Manuscript' stub)
    manuscript_candidates = [
        root / "drafts" / "manuscript.md",
        root / "drafts" / "portugues" / "manuscrito.md",
        root / "drafts" / "ingles" / "manuscrito.md",
    ]
    default_stubs = {
        "# manuscript",
        "# manuscrito",
        "# manuscript\n\nuse {{claim:claim-id}} markers for every factual assertion.",
    }
    non_stub_texts: list[str] = []
    for p in manuscript_candidates:
        if p.is_file():
            raw = p.read_text(encoding="utf-8", errors="replace").strip()
            if raw and raw.lower() not in default_stubs:
                non_stub_texts.append(raw.lower())
    combined_text = "\n".join(non_stub_texts)

    checklist_reports: dict[str, Any] = {}
    issues: list[str] = list(proto_audit["issues"])

    for schema in schemas:
        gname = schema["guideline"]
        missing_markers = [
            marker for marker in schema["required_manuscript_Markers"] if marker.lower() not in combined_text
        ]
        if not combined_text.strip():
            status = "protocol-ready" if proto_audit["status"] == "pass" else "blocked"
        elif not missing_markers and proto_audit["status"] == "pass":
            status = "markers-present-review-required"
        else:
            status = "incomplete"
            if missing_markers:
                issues.append(f"Guideline '{gname}' missing manuscript reporting markers: {missing_markers}")

        checklist_reports[gname] = {
            "status": status,
            "human_review_required": True,
            "methodological_approval": False,
            "items": schema["items"],
            "missing_manuscript_markers": missing_markers,
        }

    if update_standards and (root / "standards.yaml").is_file():
        checklist_status = standards.get("checklist_status", {})
        if not isinstance(checklist_status, dict):
            checklist_status = {}
        for gname, rep in checklist_reports.items():
            checklist_status[gname] = {
                "status": rep["status"],
                "items": [item["id"] for item in rep["items"]],
            }
        standards["checklist_status"] = checklist_status
        save_structured_file(root / "standards.yaml", standards)

    return {
        "contract": "EquatorComplianceAuditV1",
        "status": "pass" if not issues else "blocked",
        "scope": "structural protocol fields and textual markers only; not methodological certification",
        "gate_eligible": False,
        "human_review_required": True,
        "project_type": project_type,
        "protocol_status": proto_audit["status"],
        "checklists": checklist_reports,
        "issues": issues,
    }
