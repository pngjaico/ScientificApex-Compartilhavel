"""Tests for the PROSPERO 40-Field Compiler & Playwright Browser Assistant."""

from __future__ import annotations

from pathlib import Path

from article_machine.projects import init_project
from article_machine.serialization import load_structured_file, save_structured_file
from article_machine.services.prospero_assistant import (
    PROSPERO_ELIGIBILITY_WIZARD,
    compile_prospero_40_fields,
    launch_prospero_browser_assistant,
)


def _create_sr_project(tmp_path: Path) -> Path:
    project = init_project(tmp_path, "Sepsis Biomarkers Systematic Review", "systematic-review")
    protocol = load_structured_file(project / "protocol.yaml")
    protocol["research_question"] = (
        "Does procalcitonin-guided antibiotic therapy reduce 28-day mortality in ICU sepsis?"
    )
    protocol["population"] = "Adult ICU patients with sepsis or septic shock (Sepsis-3)"
    protocol["intervention"] = "Procalcitonin-guided antibiotic discontinuation algorithm"
    protocol["comparator"] = "Standard clinical care / empirical duration"
    protocol["outcomes"] = [
        "28-day all-cause mortality (Primary Outcome)",
        "Antibiotic exposure duration in days (Secondary Outcome)",
    ]
    protocol["inclusion_criteria"] = ["Randomized controlled trials in adult ICU sepsis"]
    protocol["exclusion_criteria"] = ["Pediatric populations, case reports, narrative reviews"]
    protocol["databases"] = ["PubMed/MEDLINE", "Scopus", "Embase", "Cochrane CENTRAL"]
    protocol["statistical_plan"] = (
        "Random-effects meta-analysis with REML tau^2 and Hartung-Knapp-Sidik-Jonkman (HKSJ) CI."
    )
    save_structured_file(project / "protocol.yaml", protocol)
    return project


def test_compile_prospero_40_fields_generates_all_stages_and_artifacts(tmp_path: Path) -> None:
    project = _create_sr_project(tmp_path)
    result = compile_prospero_40_fields(project)

    assert result["status"] == "pass"
    assert result["eligibility_wizard_count"] == 5
    assert result["field_count"] == 40
    assert result["extraction_not_completed_verified"] is True

    # Verify eligibility screening wizard Q4 is locked to starting with "NO" (extraction not completed)
    q4 = next(q for q in PROSPERO_ELIGIBILITY_WIZARD if q["step"] == "Q4")
    assert q4["required_answer"].upper().startswith("NO")

    # Verify all 40 numbered fields exist
    fields = result["fields"]
    numbers = [f["number"] for f in fields]
    assert numbers == list(range(1, 41))

    # Verify Field 5 Stage of Review matrix locks Data extraction to not started / not completed
    stage_matrix = {row["milestone"]: row for row in result["stage_of_review_matrix"]}
    assert stage_matrix["Data extraction"]["started"] is False
    assert stage_matrix["Data extraction"]["completed"] is False
    assert stage_matrix["Risk of bias (quality) assessment"]["started"] is False
    assert stage_matrix["Data analysis"]["started"] is False

    # Verify output files
    assert (project / result["json_payload_path"]).exists()
    assert (project / result["paired_guides"]["portugues"]).exists()
    assert (project / result["paired_guides"]["ingles"]).exists()
    assert (project / result["paired_guides"]["interactive_html"]).exists()

    html_text = (project / result["paired_guides"]["interactive_html"]).read_text(encoding="utf-8")
    assert "PROSPERO" in html_text
    assert "40 Campos" in html_text


def test_launch_prospero_browser_assistant_dry_run_creates_playwright_script(tmp_path: Path) -> None:
    project = _create_sr_project(tmp_path)
    result = launch_prospero_browser_assistant(project, dry_run=True)

    assert result["status"] == "pass"
    assert result["mode"] in {"dry-run", "dry-run-ready"}
    assert result["field_count"] == 40

    script_path = project / result["playwright_script_path"]
    assert script_path.exists()
    script_text = script_path.read_text(encoding="utf-8")
    assert "am-prospero-dock" in script_text
    assert "https://www.crd.york.ac.uk/prospero/" in script_text
