from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

from .projects import load_project
from .serialization import load_structured_file


MODE_DELIVERABLES = {
    "bootstrap": ["project.yaml", "protocol.yaml", "standards.yaml", "compute.yaml"],
    "protocol-freeze": ["protocol.yaml"],
    "corpus-build": ["sources/raw", "sources/converted"],
    "screening": ["screening decisions", "eligibility notes"],
    "extraction": ["evidence/claim_map.jsonl", "analysis"],
    "analysis": ["analysis outputs", "figures"],
    "discovery": ["benchmark report", "analysis outputs", "figures"],
    "drafting": ["drafts/manuscript.md", "drafts/references.bib"],
    "review-trinity": ["reviews/review_report.json"],
    "submission": ["exports"],
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_task_packet(project_dir: Path, mode: str, active_hypothesis: str | None = None) -> dict:
    project_dir = Path(project_dir)
    project = load_project(project_dir)
    protocol = load_structured_file(project_dir / "protocol.yaml")
    standards = load_structured_file(project_dir / "standards.yaml")
    from .zero_trust import audit_stage
    from .commands.governance import record_blocked_attempt
    from .services.workspace_hygiene import write_active_mode_guide

    gate = audit_stage(project_dir, target_mode=mode)
    current_mode = project.get("state", {}).get("current_mode")
    if mode != current_mode or gate.get("gate_eligible") is not True:
        report = {"contract": "TaskPacketGateV2", "status": "blocked", "gate_eligible": False,
                  "issues": ["Task Packet requires the active current mode and a passing canonical stage gate."], "gate": gate}
        record_blocked_attempt(project_dir, "context-build", report)
        return report
    hypothesis = active_hypothesis or protocol.get("hypothesis") or ""

    packet = {
        "contract": "TaskPacketV2",
        "status": "passed",
        "stage_gate": gate,
        "created_at": _now_iso(),
        "mode": mode,
        "active_hypothesis": hypothesis,
        "project": {
            "id": project.get("id"),
            "name": project.get("name"),
            "project_type": project.get("project_type"),
            "lane": project.get("lane"),
            "current_mode": project.get("state", {}).get("current_mode"),
        },
        "research_question": protocol.get("research_question", ""),
        "standards": {
            "guidelines": standards.get("guidelines", []),
            "risk_of_bias_tools": standards.get("risk_of_bias_tools", []),
            "policy_labels": standards.get("policy_labels", []),
            "registration_policy": standards.get("registration_policy", {}),
        },
        "deliverables": MODE_DELIVERABLES.get(mode, ["analysis"]),
        "real_flow_bindings": write_active_mode_guide(project_dir, mode),
        "criteria": {
            "block_if": [
                "Evidence is unsupported or missing.",
                "Required standards are incomplete.",
                "Reproducibility artifacts are absent.",
                "A required review registry was not completed before extraction.",
            ]
        },
    }

    packet_name = f"{_now_iso().replace(':', '-').replace('.', '-')}_{mode}.json"
    packet_path = project_dir / "context" / "task_packets" / packet_name
    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")
    packet["packet_path"] = packet_path.relative_to(project_dir).as_posix()
    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")
    return packet
