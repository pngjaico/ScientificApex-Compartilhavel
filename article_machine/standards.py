from __future__ import annotations

from copy import deepcopy


_STANDARD_MATRIX: dict[str, dict] = {
    "machine-governance": {
        "lane": "machine-governance",
        "guidelines": [],
        "risk_of_bias_tools": [],
        "policy_labels": ["machine-governance", "reproducibility", "fail-closed"],
        "deliverables": ["inventory", "upgrade record", "verification report", "benchmark", "release audit"],
    },
    "systematic-review": {
        "lane": "evidence-writing",
        "guidelines": ["PRISMA", "GRADE", "ROBIS", "AMSTAR 2"],
        "risk_of_bias_tools": ["RoB 2", "ROBINS-I"],
        "policy_labels": ["evidence-synthesis", "high-rigor"],
        "deliverables": ["protocol", "screening log", "claim map", "manuscript", "review report"],
        "registration_policy": {
            "required": True,
            "timing": "before-data-extraction",
            "accepted_registries": ["PROSPERO", "OSF"],
            "rationale": "Systematic reviews must be registered prospectively before extraction to strengthen rigor and editorial credibility.",
        },
    },
    "network-meta-analysis": {
        "lane": "evidence-writing",
        "guidelines": ["PRISMA-NMA", "GRADE"],
        "risk_of_bias_tools": ["RoB 2", "ROBINS-I"],
        "policy_labels": ["evidence-synthesis", "comparative-effectiveness"],
        "deliverables": ["protocol", "network tables", "claim map", "manuscript", "review report"],
        "registration_policy": {
            "required": True,
            "timing": "before-data-extraction",
            "accepted_registries": ["PROSPERO", "OSF"],
            "rationale": "Evidence syntheses and meta-analyses must be registered prospectively before extraction to strengthen rigor and editorial credibility.",
        },
    },
    "diagnostic-study": {
        "lane": "evidence-writing",
        "guidelines": ["STARD 2015", "QUADAS-3"],
        "risk_of_bias_tools": ["QUADAS-3"],
        "policy_labels": ["diagnostic-accuracy"],
        "deliverables": ["protocol", "analysis", "claim map", "manuscript", "review report"],
    },
    "observational-study": {
        "lane": "evidence-writing",
        "guidelines": ["STROBE"],
        "risk_of_bias_tools": ["ROBINS-I"],
        "policy_labels": ["observational"],
        "deliverables": ["protocol", "analysis", "claim map", "manuscript", "review report"],
    },
    "clinical-trial": {
        "lane": "evidence-writing",
        "guidelines": ["CONSORT 2025", "SPIRIT 2025"],
        "risk_of_bias_tools": ["RoB 2"],
        "policy_labels": ["interventional"],
        "deliverables": ["protocol", "analysis", "claim map", "manuscript", "review report"],
    },
    "animal-study": {
        "lane": "evidence-writing",
        "guidelines": ["ARRIVE"],
        "risk_of_bias_tools": ["SYRCLE"],
        "policy_labels": ["preclinical"],
        "deliverables": ["protocol", "analysis", "claim map", "manuscript", "review report"],
    },
    "prediction-model": {
        "lane": "evidence-writing",
        "guidelines": ["TRIPOD+AI"],
        "risk_of_bias_tools": ["PROBAST+AI"],
        "policy_labels": ["prediction"],
        "deliverables": ["protocol", "analysis", "claim map", "manuscript", "review report"],
    },
    "health-economics": {
        "lane": "evidence-writing",
        "guidelines": ["CHEERS"],
        "risk_of_bias_tools": [],
        "policy_labels": ["economic-evaluation"],
        "deliverables": ["protocol", "analysis", "claim map", "manuscript", "review report"],
    },
    "drug-discovery": {
        "lane": "computational-discovery",
        "guidelines": [],
        "risk_of_bias_tools": [],
        "policy_labels": ["hypothesis-generating", "non-clinical", "computational-discovery"],
        "deliverables": ["discovery plan", "benchmark", "analysis", "report", "manuscript"],
    },
    "intestinal-digital-twin": {
        "lane": "computational-discovery",
        "guidelines": [],
        "risk_of_bias_tools": [],
        "policy_labels": ["hypothesis-generating", "non-clinical", "digital-twin"],
        "deliverables": ["model spec", "sensitivity analysis", "analysis", "report", "manuscript"],
    },
    "thesis-chapter": {
        "lane": "evidence-writing",
        "guidelines": [],
        "risk_of_bias_tools": [],
        "policy_labels": ["thesis"],
        "deliverables": ["chapter brief", "claim map", "chapter draft", "review report"],
    },
    "scoping-review": {
        "lane": "evidence-writing",
        "guidelines": ["PRISMA-ScR"],
        "risk_of_bias_tools": [],
        "policy_labels": ["evidence-synthesis", "scoping"],
        "deliverables": ["protocol", "charting log", "claim map", "manuscript", "review report"],
    },
    "diagnostic-meta-analysis": {
        "lane": "evidence-writing",
        "guidelines": ["PRISMA-DTA", "GRADE-DTA"],
        "risk_of_bias_tools": ["QUADAS-2", "QUADAS-C"],
        "policy_labels": ["evidence-synthesis", "diagnostic-accuracy"],
        "deliverables": ["protocol", "2x2 extraction table", "mada analysis", "claim map", "manuscript", "review report"],
    },
    "dose-response-meta-analysis": {
        "lane": "evidence-writing",
        "guidelines": ["PRISMA 2020", "MOOSE"],
        "risk_of_bias_tools": ["ROBINS-I", "RoB 2"],
        "policy_labels": ["evidence-synthesis", "dose-response"],
        "deliverables": ["protocol", "dosres table", "spline analysis", "claim map", "manuscript", "review report"],
    },
    "case-series": {
        "lane": "evidence-writing",
        "guidelines": ["PROCESS 2023"],
        "risk_of_bias_tools": [],
        "policy_labels": ["surgical-case-series", "observational"],
        "deliverables": ["case protocol", "cohort analysis", "claim map", "manuscript", "review report"],
    },
    "case-report": {
        "lane": "evidence-writing",
        "guidelines": ["CARE 2017"],
        "risk_of_bias_tools": [],
        "policy_labels": ["case-report", "clinical"],
        "deliverables": ["case report brief", "timeline", "claim map", "manuscript", "review report"],
    },
    "delphi-consensus": {
        "lane": "evidence-writing",
        "guidelines": ["CREDES", "AGREE II"],
        "risk_of_bias_tools": [],
        "policy_labels": ["consensus", "expert-panel"],
        "deliverables": ["protocol", "round questionnaires", "consensus report", "manuscript", "review report"],
    },
    "grant-proposal": {
        "lane": "evidence-writing",
        "guidelines": ["FAPESP", "CNPq"],
        "risk_of_bias_tools": [],
        "policy_labels": ["funding-proposal", "academic"],
        "deliverables": ["research project", "budget sheet", "feasibility analysis", "ethics approval pack"],
    },
    "omics-discovery": {
        "lane": "computational-discovery",
        "guidelines": [],
        "risk_of_bias_tools": [],
        "policy_labels": ["hypothesis-generating", "non-clinical", "computational-discovery", "omics"],
        "deliverables": ["discovery plan", "variant-target map", "pathway enrichment", "analysis", "report", "manuscript"],
    },
    "wet-lab-experiment": {
        "lane": "evidence-writing",
        "guidelines": ["ARRIVE 2.0", "MIQE", "STARD"],
        "risk_of_bias_tools": ["SYRCLE"],
        "policy_labels": ["bench-protocol", "preclinical", "translational", "high-rigor"],
        "deliverables": [
            "laboratory protocol",
            "sample manifest",
            "reagent catalog",
            "standard curves",
            "analysis",
            "claim map",
            "manuscript",
            "review report",
        ],
    },
}

_DEFAULT_STANDARD = {
    "lane": "evidence-writing",
    "guidelines": [],
    "risk_of_bias_tools": [],
    "policy_labels": [],
    "deliverables": ["analysis", "manuscript", "review report"],
    "registration_policy": {
        "required": False,
        "timing": "",
        "accepted_registries": [],
        "rationale": "",
    },
}


def route_standards(project_type: str) -> dict:
    key = (project_type or "").strip().lower()
    routed = deepcopy(_STANDARD_MATRIX.get(key, _DEFAULT_STANDARD))
    routed["contract_version"] = 2
    routed["project_type"] = key
    if key != "machine-governance":
        routed["registration_policy"] = {
            "required": True,
            "timing": "before-scientific-work",
            "accepted_registries": ["PROSPERO", "OSF"],
            "verification_required": True,
            "rationale": "User policy: verified protocol registration before scientific execution; preparing the protocol is permitted.",
        }
    checklist = {}
    for guideline in routed["guidelines"]:
        checklist[guideline] = {"status": "pending", "items": []}
    for tool in routed["risk_of_bias_tools"]:
        checklist[tool] = {"status": "pending", "items": []}
    routed["checklist_status"] = checklist
    return routed
