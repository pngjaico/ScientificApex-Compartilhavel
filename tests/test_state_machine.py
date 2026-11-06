from pathlib import Path

from article_machine.projects import advance_mode, init_project
from article_machine.serialization import load_structured_file, save_structured_file


def test_protocol_freeze_requires_question_and_objectives(tmp_path: Path) -> None:
    project_dir = init_project(tmp_path, "Frozen Protocol", "systematic-review")

    blocked = advance_mode(project_dir, "protocol-freeze")
    assert blocked["status"] == "blocked"
    assert any("research_question" in issue for issue in blocked["issues"])

    protocol = load_structured_file(project_dir / "protocol.yaml")
    protocol["research_question"] = "Does intervention X improve outcome Y?"
    protocol["objectives"] = ["Estimate the effect size."]
    save_structured_file(project_dir / "protocol.yaml", protocol)

    passed = advance_mode(project_dir, "protocol-freeze")
    project = load_structured_file(project_dir / "project.yaml")

    assert passed["status"] == "passed"
    assert project["state"]["current_mode"] == "protocol-freeze"
