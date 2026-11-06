from __future__ import annotations

from pathlib import Path

from .projects import load_project
from .serialization import load_structured_file, save_structured_file


DISCOVERY_PROFILES = {
    "drug-discovery": {
        "skills": ["rdkit", "datamol", "deepchem", "diffdock", "medchem", "molecular-dynamics"],
        "benchmarks": ["target triage", "ligand ranking", "pose inspection", "uncertainty notes"],
        "outputs": ["analysis/discovery_profile.json", "analysis/benchmark_report.md", "figures/"],
    },
    "intestinal-digital-twin": {
        "skills": ["statistical-analysis", "scientific-visualization", "matplotlib", "networkx"],
        "benchmarks": ["parameter sweep", "sensitivity analysis", "failure modes", "uncertainty notes"],
        "outputs": ["analysis/discovery_profile.json", "analysis/sensitivity_report.md", "figures/"],
    },
}


def build_discovery_plan(project_dir: Path) -> dict:
    project_dir = Path(project_dir)
    project = load_project(project_dir)
    standards = load_structured_file(project_dir / "standards.yaml")
    compute = load_structured_file(project_dir / "compute.yaml")
    project_type = project.get("project_type", "")
    profile = DISCOVERY_PROFILES.get(project_type, {"skills": [], "benchmarks": [], "outputs": []})

    report = {
        "project_type": project_type,
        "lane": project.get("lane"),
        "policy_labels": standards.get("policy_labels", []),
        "skills": profile["skills"] or compute.get("python", {}).get("skills", []),
        "benchmarks": profile["benchmarks"],
        "outputs": profile["outputs"],
    }
    output_path = project_dir / "analysis" / "discovery_profile.json"
    save_structured_file(output_path, report)
    report["output_path"] = output_path.relative_to(project_dir).as_posix()
    save_structured_file(output_path, report)
    return report
