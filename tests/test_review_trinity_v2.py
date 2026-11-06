from pathlib import Path

from article_machine.projects import init_project
from article_machine.review import run_review_trinity


def test_review_v2_blocks_without_independent_red_team(tmp_path: Path) -> None:
    project = init_project(tmp_path, "Review", "systematic-review")
    report = run_review_trinity(project)
    assert report["contract"] == "ReviewTrinityReportV2"
    assert report["reviewers"]["red_team"]["status"] == "block"
