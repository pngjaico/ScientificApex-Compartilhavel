import json
from pathlib import Path

import pytest

from article_machine.cli import main
from article_machine.projects import init_project, load_project, save_project


@pytest.mark.parametrize(
    ("command", "required_mode", "protected_path"),
    [
        ("draft", "drafting", Path("reviews") / "evidence_lock_report.json"),
        ("review", "review-trinity", Path("reviews") / "review_report.json"),
        ("export", "submission", Path("exports") / "project_summary.json"),
    ],
)
def test_artifact_commands_block_before_writing_outside_required_mode(
    tmp_path: Path,
    capsys,
    command: str,
    required_mode: str,
    protected_path: Path,
) -> None:
    project_dir = init_project(tmp_path, f"Guard {command}", "systematic-review")
    target = project_dir / protected_path
    before = target.read_bytes() if target.exists() else None

    exit_code = main([command, str(project_dir)])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["contract"] == "CommandModeGate"
    assert payload["status"] == "block"
    assert payload["current_mode"] == "bootstrap"
    assert payload["required_mode"] == required_mode
    assert (target.read_bytes() if target.exists() else None) == before


def test_export_cli_still_blocks_when_submission_mode_has_no_valid_gates(tmp_path: Path, capsys) -> None:
    project_dir = init_project(tmp_path, "Guarded export", "systematic-review")
    project = load_project(project_dir)
    project["state"]["current_mode"] = "submission"
    project["state"]["mode_history"].append("submission")
    project["state"]["allowed_next_modes"] = []
    save_project(project_dir, project)

    exit_code = main(["export", str(project_dir)])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "block"
    assert not (project_dir / "exports" / "project_summary.json").exists()
