from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import os
import re
import unicodedata

from .serialization import load_structured_file, save_structured_file
from .standards import route_standards


MODE_ORDER = [
    "bootstrap",
    "protocol-freeze",
    "corpus-build",
    "screening",
    "extraction",
    "analysis",
    "discovery",
    "drafting",
    "review-trinity",
    "submission",
]

MACHINE_GOVERNANCE_MODE_ORDER = [
    "bootstrap", "inventory", "upgrade", "verification", "acceptance-benchmark", "release",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify_project_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return slug or "project"


def next_modes(current_mode: str, lane: str) -> list[str]:
    if lane == "machine-governance":
        try:
            index = MACHINE_GOVERNANCE_MODE_ORDER.index(current_mode)
        except ValueError:
            return []
        return [] if index + 1 >= len(MACHINE_GOVERNANCE_MODE_ORDER) else [MACHINE_GOVERNANCE_MODE_ORDER[index + 1]]
    if current_mode == "analysis" and lane == "computational-discovery":
        return ["discovery"]
    if current_mode == "extraction" and lane == "computational-discovery":
        return ["discovery"]
    try:
        idx = MODE_ORDER.index(current_mode)
    except ValueError:
        return []
    if idx + 1 >= len(MODE_ORDER):
        return []
    upcoming = MODE_ORDER[idx + 1]
    if current_mode == "drafting":
        return ["review-trinity"]
    if current_mode == "review-trinity":
        return ["submission"]
    if lane == "computational-discovery" and upcoming == "analysis":
        return ["discovery"]
    return [upcoming]


def _project_template(name: str, slug: str, project_type: str, standards: dict) -> dict:
    lane = standards["lane"]
    return {
        "contract_version": 2,
        "id": slug,
        "name": name,
        "project_type": project_type,
        "lane": lane,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "state": {
            "current_mode": "bootstrap",
            "mode_history": ["bootstrap"],
            "allowed_next_modes": next_modes("bootstrap", lane),
        },
    }


def _protocol_template(project_type: str) -> dict:
    return {
        "contract_version": 2,
        "project_type": project_type,
        "status": "draft",
        "research_question": "",
        "hypothesis": "",
        "objectives": [],
        "inclusion_criteria": [],
        "exclusion_criteria": [],
        "registration": {
            "required": False,
            "status": "not-applicable",
            "registry": "",
            "registry_id": "",
            "registry_url": "",
            "registered_at": "",
            "registered_before_extraction": False,
            "notes": "",
        },
        "notes": "",
    }


def _compute_template(project_type: str, lane: str) -> dict:
    discovery_skills = [
        "rdkit",
        "datamol",
        "deepchem",
        "diffdock",
        "medchem",
        "molecular-dynamics",
        "statistical-analysis",
        "scientific-visualization",
    ]
    r_required = project_type in {"network-meta-analysis", "health-economics", "machine-governance"}
    browser_required = project_type == "machine-governance"
    return {
        "contract_version": 2,
        "project_type": project_type,
        "lane": lane,
        "required_plugins": [],
        "r": {
            "required": r_required,
            "version": "4.6.1" if r_required else "4.6",
            "runner": "Rscript",
            "package_manager": "renv",
            "package_manager_version": "1.3.1",
            "lockfile": "renv.lock" if r_required else None,
            "timeout_seconds": 900,
            "allowed_directories": ["analysis", "scripts"],
            "packages": ["metafor", "meta", "netmeta", "clubSandwich", "robvis", "PRISMA2020", "ggplot2", "patchwork", "gtsummary"],
        },
        "python": {
            "required": True,
            "version": "3.13",
            "runner": ".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python",
            "package_manager": "uv",
            "package_manager_version": "0.11.31",
            "lockfile": "uv.lock",
            "timeout_seconds": 600,
            "allowed_directories": ["analysis", "scripts"],
            "skills": discovery_skills if lane == "computational-discovery" else ["statistical-analysis"],
        },
        "browser": {
            "required": browser_required,
            "version": "1.61.1",
            "runner": "tools/playwright/node_modules/.bin/playwright.cmd" if os.name == "nt" else "tools/playwright/node_modules/.bin/playwright",
            "package_manager": "npm",
            "package_manager_version": "11.17.0",
            "lockfile": "tools/playwright/package-lock.json" if browser_required else None,
            "timeout_seconds": 180,
            "allowed_directories": ["analysis", "scripts"],
        },
    }


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def init_project(workspace_root: Path, name: str, project_type: str) -> Path:
    workspace_root = Path(workspace_root)
    standards = route_standards(project_type)
    slug = slugify_project_name(name)
    project_dir = workspace_root / "projects" / slug
    project_dir.mkdir(parents=True, exist_ok=True)

    directories = [
        "sources/raw",
        "sources/converted",
        "context/task_packets",
        "context/life_science",
        "evidence",
        "evidence/prisma",
        "evidence/life_science",
        "screening",
        "analysis",
        "drafts/thesis",
        "deliverables",
        "reviews",
        "figures",
        "exports",
        ".machine/runs",
    ]
    for rel in directories:
        (project_dir / rel).mkdir(parents=True, exist_ok=True)

    project_data = _project_template(name, slug, project_type, standards)
    save_structured_file(project_dir / "project.yaml", project_data)
    protocol_data = _protocol_template(project_type)
    registration_policy = standards.get("registration_policy", {})
    protocol_data["registration"] = {
        "required": bool(registration_policy.get("required", False)),
        "status": "pending" if registration_policy.get("required", False) else "not-applicable",
        "registry": "",
        "registry_id": "",
        "registry_url": "",
        "registered_at": "",
        "registered_before_extraction": False,
        "notes": "",
    }
    save_structured_file(project_dir / "protocol.yaml", protocol_data)
    save_structured_file(project_dir / "standards.yaml", standards)
    save_structured_file(project_dir / "compute.yaml", _compute_template(project_type, standards["lane"]))
    save_structured_file(
        project_dir / "reviews" / "review_report.json",
        {
            "aggregate_status": "pending",
            "reviewers": {
                "methodological": {"status": "pending", "issues": []},
                "quantitative": {"status": "pending", "issues": []},
                "editorial": {"status": "pending", "issues": []},
            },
        },
    )

    _write_text(
        project_dir / "drafts" / "manuscript.md",
        "# Manuscript\n\nUse {{claim:claim-id}} markers for every factual assertion.\n",
    )
    _write_text(project_dir / "drafts" / "references.bib", "")
    _write_text(project_dir / "evidence" / "claim_map.jsonl", "")
    _write_text(
        project_dir / "context" / "project_brief.md",
        f"# {name}\n\nType: {project_type}\nLane: {standards['lane']}\n",
    )
    _write_text(
        project_dir / "analysis" / "README.md",
        "Place analysis scripts (.py, .R, .qmd) and generated reports in this directory.\n",
    )
    if project_type in ("systematic-review", "network-meta-analysis", "scoping-review", "diagnostic-meta-analysis", "dose-response-meta-analysis"):
        criteria_template = {
            "contract_version": 2,
            "project_id": slug,
            "name": f"Criterios de Triagem Triplo-Cego ({name})",
            "framework": f"PRISMA 2020 / Cochrane Handbook v6.4 ({project_type})",
            "screening_architecture": {
                "reviewer_1": {"role": "Revisor Clinico Independente", "focus": "PICO e elegibilidade clinica"},
                "reviewer_2": {"role": "Revisor Metodologico Independente", "focus": "Desenho de estudo e filtros de vies"},
                "reviewer_3": {"role": "Arbitro Senior de Consenso", "focus": "Adjudicacao formal de discrepancias"}
            },
            "study_designs": {
                "tier_1": {"code": "TIER_1_RCT", "name": "Ensaio Clinico Randomizado (RCT)"},
                "tier_2": {"code": "TIER_2_MATCHED_COHORT", "name": "Coorte Pareada por Escore de Propensao (PSM)"},
                "tier_3": {"code": "TIER_3_COMPARATIVE_COHORT", "name": "Coorte Comparativa com Controle"}
            }
        }
        save_structured_file(project_dir / "screening" / "screening_criteria.yaml", criteria_template)

    if project_type == "diagnostic-meta-analysis":
        diag_template = {
            "contract_version": 2,
            "model": "mada_reitsma_bivariate",
            "required_fields": ["study", "year", "tp", "fp", "fn", "tn", "threshold", "index_test", "reference_standard"],
            "data_file": "evidence/diagnostic_2x2_data.csv",
        }
        save_structured_file(project_dir / "analysis" / "diagnostic_config.yaml", diag_template)
        _write_text(
            project_dir / "evidence" / "diagnostic_2x2_data.csv",
            "study,year,tp,fp,fn,tn,threshold,index_test,reference_standard\n"
        )

    elif project_type == "dose-response-meta-analysis":
        dosres_template = {
            "contract_version": 2,
            "model": "dosresmeta_splines",
            "required_fields": ["study", "dose", "cases", "total", "logrr", "se"],
            "data_file": "evidence/dose_response_data.csv",
        }
        save_structured_file(project_dir / "analysis" / "dose_response_config.yaml", dosres_template)
        _write_text(
            project_dir / "evidence" / "dose_response_data.csv",
            "study,dose,cases,total,logrr,se\n"
        )

    elif project_type == "case-report":
        _write_text(
            project_dir / "context" / "case_report_care_template.md",
            "# CARE 2017 Case Report Structure\n\n1. Patient Information (de-identified)\n2. Clinical Findings\n3. Timeline\n4. Diagnostic Assessment\n5. Therapeutic Interventions\n6. Follow-up and Outcomes\n7. Discussion\n8. Patient Perspective & Informed Consent\n",
        )

    elif project_type == "case-series":
        _write_text(
            project_dir / "context" / "case_series_process_template.md",
            "# PROCESS 2023 Surgical Case Series Checklist\n\n1. Protocol and Registration\n2. Study Design & Setting\n3. Patient Cohort & Eligibility\n4. Surgical Technique & Equipment\n5. Postoperative Care & Endpoints\n6. Complications (Clavien-Dindo)\n7. Follow-up Loss\n8. Statistical Analysis\n",
        )

    elif project_type == "delphi-consensus":
        delphi_template = {
            "contract_version": 2,
            "guideline": "CREDES / AGREE II",
            "planned_rounds": 3,
            "consensus_threshold_percent": 80,
            "expert_panel_target": 25,
            "panel_composition": ["cirurgioes", "hepatologistas", "intensivistas", "pesquisadores_metodologicos"],
        }
        save_structured_file(project_dir / "context" / "delphi_protocol.yaml", delphi_template)

    elif project_type == "grant-proposal":
        _write_text(
            project_dir / "context" / "grant_proposal_template.md",
            "# Proposta de Fomento (FAPESP / CNPq)\n\n1. Resumo do Projeto (PT e EN)\n2. Enunciado do Problema e Hipótese\n3. Estado da Arte e Racionalidade Científica\n4. Objetivos Primários e Secundários\n5. Metodologia e Delineamento Experimental\n6. Cronograma de Execução e Metas (Milestones)\n7. Orçamento Detalhado e Justificativas\n8. Comitê de Ética em Pesquisa (CEP/CEUA)\n",
        )

    elif project_type == "omics-discovery":
        omics_template = {
            "contract_version": 2,
            "discovery_lane": "computational-discovery",
            "target_organisms": ["Homo sapiens"],
            "data_sources": ["AlphaGenome", "OpenTargets", "ChEMBL", "STRING", "Reactome", "UniProt"],
            "hypotheses_file": "context/discovery_hypotheses.yaml",
        }
        save_structured_file(project_dir / "context" / "omics_discovery_plan.yaml", omics_template)

    elif project_type == "wet-lab-experiment":
        exp_dirs = [
            "experiments/protocols",
            "experiments/checklists",
            "experiments/data/raw",
            "experiments/data/processed",
            "experiments/samples",
        ]
        for ed in exp_dirs:
            (project_dir / ed).mkdir(parents=True, exist_ok=True)

        gate_template = {
            "contract_version": 2,
            "unit_of_experimentation": "animal_or_patient_donor",
            "technical_replicates_policy": "Technical sub-samples (wells, slides, crypts) must be nested or averaged; treating them as independent N is strictly prohibited.",
            "ceua_cep_approval_required": True,
            "sample_manifest_file": "experiments/samples/sample_manifest.csv",
            "preregistration_registry": "OSF",
        }
        save_structured_file(project_dir / "experiments" / "checklists" / "pre_execution_gate.yaml", gate_template)
        _write_text(
            project_dir / "experiments" / "samples" / "sample_manifest.csv",
            "sample_id,subject_id,group,tissue,warm_ischemia_min,cold_ischemia_min,collection_time,centrifugation_time,storage_temp,freeze_thaw_cycles,freezer_location\n",
        )
        _write_text(
            project_dir / "experiments" / "README.md",
            "# Wet-Lab & Translational Experiment Environment\n\n- The biological subject (animal or patient) is the unit of experimentation.\n- Technical replicates (wells, fields, sections) are nested sub-samples.\n- Biobank tracking is mandatory in `experiments/samples/sample_manifest.csv`.\n",
        )

    return project_dir


def load_project(project_dir: Path) -> dict:
    return load_structured_file(Path(project_dir) / "project.yaml")


def save_project(project_dir: Path, payload: dict) -> None:
    payload["updated_at"] = _now_iso()
    state = payload.setdefault("state", {})
    lane = payload.get("lane", "evidence-writing")
    current_mode = state.get("current_mode", "bootstrap")
    state["allowed_next_modes"] = next_modes(current_mode, lane)
    save_structured_file(Path(project_dir) / "project.yaml", payload)


def _has_nonempty_registry(project_dir: Path) -> bool:
    registry = Path(project_dir) / "sources" / "registry.jsonl"
    return registry.exists() and registry.read_text(encoding="utf-8").strip() != ""


def _registration_required(project_dir: Path, project: dict | None = None, protocol: dict | None = None) -> bool:
    from .services.protocol_registration import registration_required
    return registration_required(project_dir)


def _registration_gate(protocol: dict) -> list[str]:
    registration = protocol.get("registration", {})
    issues: list[str] = []
    if not registration.get("required", False):
        return issues
    if registration.get("status") != "registered":
        issues.append("protocol.yaml registration.status must be 'registered' and verified before scientific work.")
    if not registration.get("registry"):
        issues.append("protocol.yaml registration.registry is required before extraction.")
    if not registration.get("registry_url"):
        issues.append("protocol.yaml registration.registry_url is required before extraction.")
    if not registration.get("registered_at"):
        issues.append("protocol.yaml registration.registered_at is required before extraction.")
    if not registration.get("registered_before_extraction", False):
        issues.append("protocol.yaml registration.registered_before_extraction must be true before extraction.")
    return issues


def register_review_protocol(
    project_dir: Path,
    registry: str,
    registry_id: str,
    registry_url: str,
    registered_at: str,
    notes: str = "",
) -> dict:
    project_dir = Path(project_dir)
    protocol = load_structured_file(project_dir / "protocol.yaml")
    registration = protocol.setdefault("registration", {})
    registration.update(
        {
            "required": True,
            "status": "declared-unverified",
            "registry": registry,
            "registry_id": registry_id,
            "registry_url": registry_url,
            "registered_at": registered_at,
            "registered_before_extraction": False,
            "registered_before_scientific_work": False,
            "notes": notes,
        }
    )
    save_structured_file(project_dir / "protocol.yaml", protocol)
    return registration


def gate_mode(project_dir: Path, target_mode: str) -> dict:
    project_dir = Path(project_dir)
    project = load_project(project_dir)
    protocol = load_structured_file(project_dir / "protocol.yaml")
    review_report = load_structured_file(project_dir / "reviews" / "review_report.json")
    issues: list[str] = []

    current_mode = project.get("state", {}).get("current_mode", "bootstrap")
    allowed = project.get("state", {}).get("allowed_next_modes", [])
    if target_mode not in allowed:
        issues.append(f"Mode '{target_mode}' is not allowed from '{current_mode}'.")

    if project.get("lane") == "machine-governance" and project.get("project_type") == "machine-governance":
        governance_requirements = {
            "inventory": [(project_dir / "context" / "inventory_manifest.json", "context/inventory_manifest.json is required.")],
            "upgrade": [(project_dir / "context" / "inventory_manifest.json", "inventory must be completed before upgrade.")],
            "verification": [(project_dir / "analysis" / "verification_report.json", "analysis/verification_report.json is required.")],
            "acceptance-benchmark": [(project_dir / "analysis" / "benchmark_report.json", "analysis/benchmark_report.json is required.")],
            "release": [(project_dir / "analysis" / "release_audit.json", "analysis/release_audit.json is required.")],
        }
        for path, message in governance_requirements.get(target_mode, []):
            if not path.exists():
                issues.append(message)
        if target_mode == "acceptance-benchmark":
            from .benchmarks import benchmark_gate_passed
            if not benchmark_gate_passed(project_dir):
                issues.append("AgentBenchmarkReportV2 is missing or not gate eligible.")
        return {"status": "passed" if not issues else "blocked", "target_mode": target_mode, "issues": issues}

    from .services.protocol_registration import PLANNING_MODES, registration_gate
    if target_mode not in PLANNING_MODES:
        issues.extend(registration_gate(project_dir, target_mode)["issues"])

    if target_mode == "protocol-freeze":
        if not protocol.get("research_question"):
            issues.append("protocol.yaml is missing 'research_question'.")
        if not protocol.get("objectives"):
            issues.append("protocol.yaml must declare at least one objective.")
    elif target_mode == "corpus-build":
        if not (project_dir / "standards.yaml").exists():
            issues.append("standards.yaml is missing.")
    elif target_mode in {"screening", "extraction"}:
        if not _has_nonempty_registry(project_dir):
            issues.append("sources/registry.jsonl is empty.")
        if target_mode == "extraction" and _registration_required(project_dir, project, protocol):
            issues.extend(_registration_gate(protocol))
    elif target_mode == "analysis":
        if not (project_dir / "evidence" / "claim_map.jsonl").exists():
            issues.append("evidence/claim_map.jsonl is missing.")
        if _registration_required(project_dir, project, protocol):
            issues.extend(_registration_gate(protocol))
    elif target_mode == "discovery":
        if project.get("lane") != "computational-discovery":
            issues.append("Only computational-discovery projects can enter discovery mode.")
    elif target_mode == "review-trinity":
        manuscript = project_dir / "drafts" / "manuscript.md"
        if not manuscript.exists() or not manuscript.read_text(encoding="utf-8").strip():
            issues.append("drafts/manuscript.md is empty.")
    elif target_mode == "submission":
        if review_report.get("aggregate_status") != "pass":
            issues.append("reviews/review_report.json must be PASS before submission.")
        from .policy.gates import workspace_snapshot, file_sha256
        if review_report.get("contract") != "ReviewTrinityReportV2":
            issues.append("reviews/review_report.json must use ReviewTrinityReportV2.")
        elif review_report.get("review_snapshot") != workspace_snapshot(project_dir):
            issues.append("reviews/review_report.json is stale for current protected project inputs.")
        if review_report.get("red_team_sha256") != file_sha256(project_dir / "reviews" / "red_team_report.json"):
            issues.append("reviews/review_report.json does not match the current red-team artifact.")

    return {
        "status": "passed" if not issues else "blocked",
        "target_mode": target_mode,
        "issues": issues,
    }


def advance_mode(project_dir: Path, target_mode: str) -> dict:
    project_dir = Path(project_dir)
    gate = gate_mode(project_dir, target_mode)
    if gate["status"] != "passed":
        return gate

    # The transition-specific checks above preserve the V1 API, but are not the
    # authoritative gate: audit every prerequisite up to this stage and reject
    # a stage that is incomplete even when a legacy sentinel file exists.
    from .zero_trust import audit_stage
    protocol_before_stage_audit = None
    if target_mode == "protocol-freeze":
        protocol_before_stage_audit = load_structured_file(project_dir / "protocol.yaml")
        frozen_protocol = dict(protocol_before_stage_audit)
        frozen_protocol["status"] = "frozen"
        save_structured_file(project_dir / "protocol.yaml", frozen_protocol)
    stage = audit_stage(project_dir, target_mode=target_mode)
    if stage.get("gate_eligible") is not True:
        if protocol_before_stage_audit is not None:
            save_structured_file(project_dir / "protocol.yaml", protocol_before_stage_audit)
        return {
            "status": "blocked",
            "target_mode": target_mode,
            "issues": stage.get("issues", ["Canonical stage audit is not gate eligible."]),
            "stage_audit": stage,
        }

    # The V2 transition report binds the successful legacy and canonical checks
    # to current project and control-plane hashes.
    from .policy.gates import canonical_gate
    checks = [
        {"name": "legacy_transition", "status": "pass", "message": "Transition-specific requirements passed."},
        {"name": "project_contract", "status": "pass" if (project_dir / "compute.yaml").exists() else "block", "message": "compute.yaml is required."},
        {"name": "canonical_stage_audit", "status": "pass", "message": "Canonical stage audit passed."},
    ]
    v2 = canonical_gate(project_dir, target_mode, checks)
    if v2["status"] != "pass":
        return {"status": "blocked", "target_mode": target_mode, "issues": v2["issues"], "gate": v2}

    project = load_project(project_dir)
    state = project.setdefault("state", {})
    history = state.setdefault("mode_history", [])
    history.append(target_mode)
    state["current_mode"] = target_mode
    state["allowed_next_modes"] = next_modes(target_mode, project.get("lane", "evidence-writing"))

    if target_mode == "protocol-freeze":
        protocol = load_structured_file(project_dir / "protocol.yaml")
        protocol["status"] = "frozen"
        save_structured_file(project_dir / "protocol.yaml", protocol)

    if target_mode not in {"bootstrap", "protocol-freeze"}:
        from .services.protocol_registration import registration_gate
        registration_gate(project_dir, target_mode, mark_started=True)
    save_project(project_dir, project)
    return {
        "status": "passed",
        "target_mode": target_mode,
        "allowed_next_modes": state["allowed_next_modes"],
        "gate": v2,
    }
