from pathlib import Path

from article_machine.projects import init_project
from article_machine.serialization import load_structured_file


def test_init_project_creates_scientific_os_layout(tmp_path: Path) -> None:
    project_dir = init_project(
        workspace_root=tmp_path,
        name="Gut Twin Discovery",
        project_type="intestinal-digital-twin",
    )

    expected_directories = [
        "sources",
        "context",
        "evidence",
        "analysis",
        "drafts",
        "deliverables",
        "reviews",
        "figures",
        ".machine",
        ".machine/runs",
        "context/task_packets",
    ]
    for rel in expected_directories:
        assert (project_dir / rel).is_dir(), rel

    expected_files = [
        "project.yaml",
        "protocol.yaml",
        "standards.yaml",
        "compute.yaml",
        "drafts/manuscript.md",
        "drafts/references.bib",
        "evidence/claim_map.jsonl",
        "reviews/review_report.json",
    ]
    for rel in expected_files:
        assert (project_dir / rel).exists(), rel

    project = load_structured_file(project_dir / "project.yaml")
    assert project["project_type"] == "intestinal-digital-twin"
    assert project["lane"] == "computational-discovery"
    assert project["state"]["current_mode"] == "bootstrap"
    assert project["state"]["allowed_next_modes"] == ["protocol-freeze"]
