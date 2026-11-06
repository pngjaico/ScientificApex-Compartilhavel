from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .agent_skills import audit_workspace_skills, catalog_workspace_skills, route_workspace_skills
from .analysis import preflight, run_python_script, run_r_script
from .benchmarks import validate_benchmark_report
from .commands.governance import aggregate_benchmark_file, record_blocked_attempt
from .congress_profiles import save_congress_profile, use_congress_profile
from .context import build_task_packet
from .deliverables import (
    build_deliverable,
    export_deliverable,
    import_conference_requirements,
    plan_deliverable,
    qa_deliverable,
    submit_deliverable,
)
from .discovery import build_discovery_plan
from .evidence import validate_evidence_lock
from .ingest import register_source
from .journals import catalog_journals, route_journals, verify_journal_presets, write_journal_report
from .life_science import catalog_life_science_skills, plan_life_science_retrieval
from .projects import advance_mode, init_project, load_project, register_review_protocol
from .ptbr_style import (
    anti_ai_naturalize_text,
    audit_text,
    build_generation_brief,
    naturalize_text,
    read_text_for_audit,
    write_audit_reports,
)
from .review import run_review_trinity
from .services.environment import check_environment, prepare_environment
from .services.graph_query import query_operational_graph
from .services.machine import machine_doctor, release_audit
from .services.plugins import audit_scientific_plugins
from .services.scientific_workflows import audit_language, plan_scientific_workflow
from .services.skill_registry import build_skill_update_plan
from .zero_trust import (
    audit_retrieval,
    audit_stage,
    build_retrieval_plan,
    compile_query_plan,
    run_guard_check,
    run_idea_tournament,
    run_machine_audit,
    validate_query_plan,
)


def _print(payload: Any) -> None:
    try:
        getattr(sys.stdout, "reconfigure", lambda **_: None)(encoding="utf-8", errors="replace")
    except Exception:
        pass
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _require_command_mode(project_dir: Path, command: str, required_mode: str) -> dict[str, Any]:
    project = load_project(project_dir)
    current_mode = project.get("state", {}).get("current_mode", "bootstrap")
    from .services.protocol_registration import registration_gate

    issues = list(registration_gate(project_dir, command)["issues"])
    if current_mode != required_mode:
        issues.append(
            f"Command '{command}' requires current_mode '{required_mode}', found '{current_mode}'. "
            "Advance through the state machine before producing this artifact."
        )
    return {
        "contract": "CommandModeGate",
        "status": "pass" if not issues else "block",
        "command": command,
        "required_mode": required_mode,
        "current_mode": current_mode,
        "issues": issues,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="article-machine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("name")
    init_parser.add_argument("--type", required=True, dest="project_type")
    init_parser.add_argument("--workspace-root", default=".")

    preflight_parser = subparsers.add_parser("preflight")
    preflight_parser.add_argument("project_dir")

    workflow_parser = subparsers.add_parser("workflow")
    workflow_sub = workflow_parser.add_subparsers(dest="workflow_command", required=True)
    workflow_plan = workflow_sub.add_parser("plan")
    workflow_plan.add_argument("project_dir")
    workflow_plan.add_argument("--query", required=True)
    workflow_plan.add_argument("--language", required=True, choices=["en", "pt-BR"])
    workflow_language = workflow_sub.add_parser("audit-language")
    workflow_language.add_argument("project_dir")
    workflow_language.add_argument("--language", required=True, choices=["en", "pt-BR"])
    workflow_language.add_argument("--draft", default="drafts/manuscript.md")
    workflow_language.add_argument("--reference")

    env_parser = subparsers.add_parser("env")
    env_sub = env_parser.add_subparsers(dest="env_command", required=True)
    for env_action in ("check", "prepare"):
        env_action_parser = env_sub.add_parser(env_action)
        env_action_parser.add_argument("project_dir")
        env_action_parser.add_argument("--runtime", required=True, choices=["python", "r", "browser"])
        if env_action == "prepare":
            env_action_parser.add_argument("--dry-run", action="store_true")

    ingest_parser = subparsers.add_parser("ingest")
    ingest_parser.add_argument("project_dir")
    ingest_parser.add_argument("--source", required=True)
    ingest_parser.add_argument("--kind", default="note")

    registry_parser = subparsers.add_parser("registry")
    registry_sub = registry_parser.add_subparsers(dest="registry_command", required=True)
    registry_register = registry_sub.add_parser("register")
    registry_register.add_argument("project_dir")
    registry_register.add_argument("--registry", required=True)
    registry_register.add_argument("--id", required=True, dest="registry_id")
    registry_register.add_argument("--url", required=True, dest="registry_url")
    registry_register.add_argument("--registered-at", required=True, dest="registered_at")
    registry_register.add_argument("--notes", default="")
    registry_verify = registry_sub.add_parser("verify")
    registry_verify.add_argument("project_dir")
    registry_verify.add_argument(
        "--record",
        required=True,
        help="Reviewed registry-evidence JSON inside the project; never creates a registration",
    )
    registry_check_osf = registry_sub.add_parser("check-osf", help="Test OSF API v2 token and connectivity")
    registry_check_osf.add_argument(
        "--token", default=None, help="Explicit token to test; defaults to OSF_TOKEN env or .env"
    )
    registry_fetch_osf = registry_sub.add_parser(
        "fetch-osf", help="Fetch OSF registration snapshot, compute hash and scaffold verification"
    )
    registry_fetch_osf.add_argument("project_dir")
    registry_fetch_osf.add_argument(
        "--id", required=True, dest="registry_id", help="OSF registration identifier (e.g. 5+ chars)"
    )
    registry_fetch_osf.add_argument("--reviewer", default="", help="Name of reviewer confirming protocol match")
    registry_fetch_osf.add_argument("--token", default=None, help="Explicit token; defaults to OSF_TOKEN env or .env")

    methodology_parser = subparsers.add_parser(
        "methodology", help="Protocol validation, PROSPERO/OSF packet compilation, EQUATOR & extraction audits"
    )
    methodology_sub = methodology_parser.add_subparsers(dest="methodology_command", required=True)
    meth_val_proto = methodology_sub.add_parser(
        "validate-protocol", help="Validate design-specific methodological completeness in protocol.yaml"
    )
    meth_val_proto.add_argument("project_dir")
    meth_compile_reg = methodology_sub.add_parser(
        "compile-registration-packet", help="Compile paired PT-BR/EN registration packets for PROSPERO and OSF"
    )
    meth_compile_reg.add_argument("project_dir")
    meth_equator = methodology_sub.add_parser(
        "audit-equator", help="Audit protocol and manuscripts against machine-readable EQUATOR checklists"
    )
    meth_equator.add_argument("project_dir")
    meth_extract = methodology_sub.add_parser(
        "validate-extraction", help="Validate extracted study rows for denominator, SD/SE, 2x2, and NMA connectivity"
    )
    meth_extract.add_argument("file_path")
    meth_extract.add_argument("--mode", default="pairwise", choices=["pairwise", "nma", "diagnostic"])
    meth_numbers = methodology_sub.add_parser(
        "audit-numbers", help="Verify numerical consistency between analysis/results_ledger.json and PT/EN drafts"
    )
    meth_numbers.add_argument("project_dir")
    meth_prisma = methodology_sub.add_parser(
        "prisma-checklist", help="Generate comprehensive PRISMA 2020 & PRISMA-NMA checklist tables with exact anchors"
    )
    meth_prisma.add_argument("project_dir")

    corpus_parser = subparsers.add_parser(
        "corpus", help="Multi-database search compilation, drop-folders, PubMed API retrieval, and PRISMA deduplication"
    )
    corpus_sub = corpus_parser.add_subparsers(dest="corpus_command", required=True)
    corpus_prep = corpus_sub.add_parser(
        "prepare",
        help="Compile search strings (PubMed, Scopus, Embase, CENTRAL, LILACS) and create manual drop-folders",
    )
    corpus_prep.add_argument("project_dir")
    corpus_pubmed = corpus_sub.add_parser(
        "fetch-pubmed", help="Execute live PubMed E-utilities retrieval for compiled query"
    )
    corpus_pubmed.add_argument("project_dir")
    corpus_pubmed.add_argument("--max-records", type=int, default=200, dest="max_records")
    corpus_scopus = corpus_sub.add_parser("fetch-scopus", help="Execute live Scopus API retrieval using SCOPUS_API_KEY")
    corpus_scopus.add_argument("project_dir")
    corpus_scopus.add_argument("--max-records", type=int, default=200, dest="max_records")
    corpus_check_scopus = corpus_sub.add_parser("check-scopus", help="Test live Scopus API key connectivity")
    corpus_check_scopus.add_argument("--project-dir", default=".", dest="project_dir")
    corpus_dedup = corpus_sub.add_parser(
        "deduplicate",
        help="Ingest drop-folders (.ris, .nbib, .csv, .json), write manifests, and run 3-stage PRISMA deduplication",
    )
    corpus_dedup.add_argument("project_dir")
    corpus_screen = corpus_sub.add_parser(
        "screen",
        help="Run Cochrane gold-standard triple-reviewer screening (2 blind reviewers + 1 senior arbiter) and export native Rayyan CSV & PRISMA checklists",
    )
    corpus_screen.add_argument("project_dir")

    datasets_parser = subparsers.add_parser(
        "datasets", help="Clinical & Healthcare ML dataset catalog, staging, and SHA-256 verification"
    )
    datasets_sub = datasets_parser.add_subparsers(dest="datasets_command", required=True)
    ds_cat = datasets_sub.add_parser(
        "catalog", help="List curated clinical/ML datasets (open-direct and credentialed-dua)"
    )
    ds_cat.add_argument("--domain", default=None)
    ds_cat.add_argument("--access-tier", default=None, dest="access_tier")
    ds_cat.add_argument("--query", default=None)
    ds_cat.add_argument("--auto-only", action="store_true", dest="auto_only")
    ds_packs = datasets_sub.add_parser(
        "packs", help="List specialty dataset packs ready for automatic API/HTTP/R download"
    )
    ds_packs.add_argument("--pack", default=None)
    ds_stage = datasets_sub.add_parser(
        "stage", help="Create dataset drop-folders (sources/datasets/<id>/) and bilingual governance plan"
    )
    ds_stage.add_argument("project_dir")
    ds_stage.add_argument("--ids", default=None, help="Comma-separated dataset IDs to stage (defaults to all)")
    ds_fetch = datasets_sub.add_parser(
        "fetch", help="Automatically download & verify an open-direct dataset via REST API, HTTP/ZIP, or R 4.6.1"
    )
    ds_fetch.add_argument("project_dir")
    ds_fetch.add_argument("--id", required=True, dest="dataset_id")
    ds_fetch_pack = datasets_sub.add_parser(
        "fetch-pack", help="Stage and automatically download all open datasets in a specialty pack"
    )
    ds_fetch_pack.add_argument("project_dir")
    ds_fetch_pack.add_argument("--pack", default="essential-core", dest="pack_id")
    ds_verify = datasets_sub.add_parser(
        "verify", help="Verify local dataset files in sources/datasets/<id>/ and write SHA-256 manifest"
    )
    ds_verify.add_argument("project_dir")
    ds_verify.add_argument("--id", required=True, dest="dataset_id")

    hygiene_parser = subparsers.add_parser(
        "hygiene", help="Workspace anti-pollution shield, project organizer & real-flow skill bindings"
    )
    hygiene_sub = hygiene_parser.add_subparsers(dest="hygiene_command", required=True)
    hyg_check = hygiene_sub.add_parser("check", help="Audit workspace root, projects/, and optionally git staged files")
    hyg_check.add_argument("--workspace-root", default=".", dest="workspace_root")
    hyg_check.add_argument(
        "--staged", action="store_true", help="Also audit git staged files for secrets or loose files"
    )
    hyg_bind = hygiene_sub.add_parser(
        "bindings", help="Resolve mandatory skills, CLI commands & allowed paths for a project/mode"
    )
    hyg_bind.add_argument("project_dir")
    hyg_bind.add_argument("--mode", default=None)
    hyg_org = hygiene_sub.add_parser(
        "organize", help="Organize stray top-level files inside a project into canonical folders with SHA-256 manifest"
    )
    hyg_org.add_argument("project_dir")
    hyg_org.add_argument(
        "--apply", action="store_true", help="Move stray files into canonical folders (default is dry-run manifest)"
    )
    hyg_hook = hygiene_sub.add_parser(
        "install-hook", help="Install automatic .git/hooks/pre-commit anti-pollution guard"
    )
    hyg_hook.add_argument("--workspace-root", default=".", dest="workspace_root")

    study_parser = subparsers.add_parser(
        "study", help="Build bilingual study guide, didactic lessons & defense flashcards"
    )
    study_sub = study_parser.add_subparsers(dest="study_command", required=True)
    study_build = study_sub.add_parser(
        "build", help="Generate PT-BR/EN study & defense guides and interactive HTML dashboard"
    )
    study_build.add_argument("project_dir")

    synth_parser = subparsers.add_parser(
        "synthesis", help="Generate bilingual manuscripts, abstracts, slides & posters from R outputs"
    )
    synth_sub = synth_parser.add_subparsers(dest="synthesis_command", required=True)
    synth_sub.add_parser("templates", help="List expanded bilingual publication, slide, poster & abstract templates")
    synth_harvest = synth_sub.add_parser(
        "harvest", help="Harvest R/Python tables, metrics & figures into results_ledger.json"
    )
    synth_harvest.add_argument("project_dir")
    synth_build = synth_sub.add_parser(
        "build", help="Synthesize complete PT-BR/EN manuscripts, abstracts, slides & posters from R outputs"
    )
    synth_build.add_argument("project_dir")
    synth_build.add_argument(
        "--publication-template", default="jama-lancet-nejm-high-impact", dest="publication_template"
    )
    synth_build.add_argument("--slide-template", default="congresso-cirurgico-oral-10min", dest="slide_template")
    synth_build.add_argument("--poster-template", default="eposter-digital-16x9-congresso", dest="poster_template")
    synth_build.add_argument("--slug", default="pacote-completo-r")

    prospero_parser = subparsers.add_parser(
        "prospero",
        help="Compile all 40 official NIHR CRD PROSPERO fields and launch built-in Playwright browser assistant",
    )
    prospero_sub = prospero_parser.add_subparsers(dest="prospero_command", required=True)
    prospero_compile = prospero_sub.add_parser(
        "compile",
        help="Compile 40 PROSPERO fields + 5 screening wizard answers into PT-BR/EN guides and HTML5 1-Click Assistant",
    )
    prospero_compile.add_argument("project_dir")
    prospero_assist = prospero_sub.add_parser(
        "browser-assist",
        help="Launch Playwright Chromium on PROSPERO with floating 40-field Auto-Fill Dock for login & review",
    )
    prospero_assist.add_argument("project_dir")
    prospero_assist.add_argument("--dry-run", action="store_true", dest="dry_run")
    prospero_assist.add_argument("--headless", action="store_true")

    doc_parser = subparsers.add_parser(
        "document",
        help="Extract PDF/DOCX/images to text and tables with OCR fallback (Tesseract)",
    )
    doc_sub = doc_parser.add_subparsers(dest="document_command", required=True)
    doc_sub.add_parser(
        "test-tesseract",
        help="Check Tesseract binary, tessdata directory, and available language models",
    )
    doc_extract = doc_sub.add_parser(
        "extract",
        help="Extract a single document or directory of documents to markdown, jsonl, and tables",
    )
    doc_extract.add_argument("input_path")
    doc_extract.add_argument("--output", default=None, dest="output_root")
    doc_extract.add_argument(
        "--ocr",
        default="auto",
        choices=["auto", "force", "off"],
        help="auto (default, OCR on low-quality/scanned pages), force, or off",
    )
    doc_extract.add_argument(
        "--lang",
        default=None,
        help="Tesseract language string (e.g. por+eng)",
    )
    doc_extract.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Rendering resolution for OCR (default 300)",
    )
    doc_extract.add_argument(
        "--tables",
        default="lines",
        choices=["lines", "text", "both", "off"],
        dest="table_strategy",
    )
    doc_extract.add_argument(
        "--max-pages",
        type=int,
        default=None,
        dest="max_pages",
    )
    doc_extract.add_argument("--force", action="store_true")

    doc_proj = doc_sub.add_parser(
        "project-extract",
        help="Extract all project sources to sources/extracted/ with provenance index",
    )
    doc_proj.add_argument("project_dir")
    doc_proj.add_argument("--input", default=None, dest="input_path")
    doc_proj.add_argument(
        "--ocr",
        default="auto",
        choices=["auto", "force", "off"],
    )
    doc_proj.add_argument("--lang", default=None)
    doc_proj.add_argument(
        "--tables",
        default="lines",
        choices=["lines", "text", "both", "off"],
        dest="table_strategy",
    )
    doc_proj.add_argument("--force", action="store_true")

    context_parser = subparsers.add_parser("context")
    context_sub = context_parser.add_subparsers(dest="context_command", required=True)
    context_build = context_sub.add_parser("build")
    context_build.add_argument("project_dir")
    context_build.add_argument("--mode", required=True)
    context_build.add_argument("--hypothesis")

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("project_dir")
    analyze_parser.add_argument("--mode", required=True)
    analyze_parser.add_argument("--hypothesis")

    run_r_parser = subparsers.add_parser("run-r")
    run_r_parser.add_argument("project_dir")
    run_r_parser.add_argument("script_path")

    run_python_parser = subparsers.add_parser("run-python")
    run_python_parser.add_argument("project_dir")
    run_python_parser.add_argument("script_path")

    draft_parser = subparsers.add_parser("draft")
    draft_parser.add_argument("project_dir")

    review_parser = subparsers.add_parser("review")
    review_parser.add_argument("project_dir")

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("project_dir")

    congress_parser = subparsers.add_parser("congress")
    congress_sub = congress_parser.add_subparsers(dest="congress_command", required=True)
    congress_import = congress_sub.add_parser("import")
    congress_import.add_argument("project_dir")
    congress_import.add_argument("--source", required=True)
    congress_import.add_argument("--kind", choices=["deck", "poster", "abstract"], default="deck")
    congress_import.add_argument("--slug")
    congress_import.add_argument("--profile")
    congress_import.add_argument("--crawl", action="store_true")
    congress_import.add_argument("--author", action="append", dest="authors")
    congress_import.add_argument("--affiliation", action="append", dest="affiliations")
    congress_import.add_argument("--qr-url", default="")
    congress_import.add_argument("--logo", action="append", dest="logos")
    congress_save = congress_sub.add_parser("save-profile")
    congress_save.add_argument("deliverable_dir")
    congress_save.add_argument("--profile", required=True)
    congress_use = congress_sub.add_parser("use-profile")
    congress_use.add_argument("project_dir")
    congress_use.add_argument("--profile", required=True)
    congress_use.add_argument("--slug", required=True)

    deck_parser = subparsers.add_parser("deck")
    deck_sub = deck_parser.add_subparsers(dest="deck_command", required=True)
    for action in ["plan", "build", "qa", "export"]:
        action_parser = deck_sub.add_parser(action)
        action_parser.add_argument("deliverable_dir")
        if action == "export":
            action_parser.add_argument("--strict", action="store_true")

    poster_parser = subparsers.add_parser("poster")
    poster_sub = poster_parser.add_subparsers(dest="poster_command", required=True)
    for action in ["plan", "build", "qa", "export"]:
        action_parser = poster_sub.add_parser(action)
        action_parser.add_argument("deliverable_dir")
        if action == "export":
            action_parser.add_argument("--strict", action="store_true")

    submit_parser = subparsers.add_parser("submit")
    submit_sub = submit_parser.add_subparsers(dest="submit_command", required=True)
    submit_dry = submit_sub.add_parser("dry-run")
    submit_dry.add_argument("deliverable_dir")
    submit_run = submit_sub.add_parser("run")
    submit_run.add_argument("deliverable_dir")
    submit_run.add_argument("--confirm", action="store_true")

    life_science_parser = subparsers.add_parser("life-science")
    life_science_sub = life_science_parser.add_subparsers(dest="life_science_command", required=True)
    life_catalog = life_science_sub.add_parser("catalog")
    life_catalog.add_argument("--plugin-root")
    life_plan = life_science_sub.add_parser("plan")
    life_plan.add_argument("project_dir")
    life_plan.add_argument("--question", required=True)
    life_plan.add_argument("--plugin-root")

    skills_parser = subparsers.add_parser("skills")
    skills_sub = skills_parser.add_subparsers(dest="skills_command", required=True)
    skills_catalog = skills_sub.add_parser("catalog")
    skills_catalog.add_argument("--skills-dir")
    skills_audit = skills_sub.add_parser("audit")
    skills_audit.add_argument("--skills-dir")
    skills_audit.add_argument("--strict", action="store_true")
    skills_audit.add_argument("--provenance", action="store_true")
    skills_update = skills_sub.add_parser("update-plan")
    skills_update.add_argument("--workspace-root", default=".")
    skills_route = skills_sub.add_parser("route")
    skills_route.add_argument("--query", required=True)
    skills_route.add_argument("--skills-dir")
    skills_route.add_argument("--limit", type=int, default=8)

    journal_parser = subparsers.add_parser("journal")
    journal_sub = journal_parser.add_subparsers(dest="journal_command", required=True)
    journal_catalog = journal_sub.add_parser("catalog")
    journal_catalog.add_argument("--domain")
    journal_catalog.add_argument("--tier")
    journal_catalog.add_argument("--presets-dir")
    journal_verify = journal_sub.add_parser("verify")
    journal_verify.add_argument("--presets-dir")
    journal_route = journal_sub.add_parser("route")
    journal_route.add_argument("project_dir")
    journal_route.add_argument("--domain")
    journal_route.add_argument("--limit", type=int, default=10)
    journal_route.add_argument("--presets-dir")
    journal_report = journal_sub.add_parser("report")
    journal_report.add_argument("project_dir")
    journal_report.add_argument("--domain")
    journal_report.add_argument("--presets-dir")

    guard_parser = subparsers.add_parser("guard")
    guard_sub = guard_parser.add_subparsers(dest="guard_command", required=True)
    guard_check = guard_sub.add_parser("check")
    guard_check.add_argument("project_dir")

    query_parser = subparsers.add_parser("query")
    query_sub = query_parser.add_subparsers(dest="query_command", required=True)
    query_validate = query_sub.add_parser("validate")
    query_validate.add_argument("project_dir")
    query_compile = query_sub.add_parser("compile")
    query_compile.add_argument("project_dir")

    retrieval_parser = subparsers.add_parser("retrieval")
    retrieval_sub = retrieval_parser.add_subparsers(dest="retrieval_command", required=True)
    retrieval_plan = retrieval_sub.add_parser("plan")
    retrieval_plan.add_argument("project_dir")
    retrieval_audit = retrieval_sub.add_parser("audit")
    retrieval_audit.add_argument("project_dir")

    idea_parser = subparsers.add_parser("idea")
    idea_sub = idea_parser.add_subparsers(dest="idea_command", required=True)
    idea_tournament = idea_sub.add_parser("tournament")
    idea_tournament.add_argument("project_dir")

    stage_parser = subparsers.add_parser("stage")
    stage_sub = stage_parser.add_subparsers(dest="stage_command", required=True)
    stage_audit = stage_sub.add_parser("audit")
    stage_audit.add_argument("project_dir")
    stage_audit.add_argument("--target-mode")

    benchmark_parser = subparsers.add_parser("benchmark")
    benchmark_sub = benchmark_parser.add_subparsers(dest="benchmark_command", required=True)
    benchmark_validate = benchmark_sub.add_parser("validate")
    benchmark_validate.add_argument("project_dir")
    benchmark_aggregate = benchmark_sub.add_parser("aggregate")
    benchmark_aggregate.add_argument("project_dir")
    benchmark_aggregate.add_argument("--input")
    benchmark_aggregate.add_argument("--output")

    graph_parser = subparsers.add_parser("graph")
    graph_sub = graph_parser.add_subparsers(dest="graph_command", required=True)
    graph_query = graph_sub.add_parser("query")
    graph_query.add_argument("query")
    graph_query.add_argument("--scope", default="control-plane")
    graph_query.add_argument("--limit", type=int, default=10)
    graph_query.add_argument("--graph-path")

    machine_parser = subparsers.add_parser("machine")
    machine_sub = machine_parser.add_subparsers(dest="machine_command", required=True)
    machine_audit = machine_sub.add_parser("audit")
    machine_audit.add_argument("--workspace-root", default=".")
    machine_audit.add_argument("--strict", action="store_true")
    machine_doctor_parser = machine_sub.add_parser("doctor")
    machine_doctor_parser.add_argument("--workspace-root", default=".")
    machine_doctor_parser.add_argument("--project-dir")
    machine_release = machine_sub.add_parser("release-audit")
    machine_release.add_argument("project_dir")

    plugins_parser = subparsers.add_parser("plugins")
    plugins_sub = plugins_parser.add_subparsers(dest="plugins_command", required=True)
    plugins_audit = plugins_sub.add_parser("audit")
    plugins_audit.add_argument("--workspace-root", default=".")

    style_parser = subparsers.add_parser("style")
    style_sub = style_parser.add_subparsers(dest="style_command", required=True)
    ptbr_audit = style_sub.add_parser("ptbr-audit")
    ptbr_audit.add_argument("paths", nargs="+")
    ptbr_audit.add_argument("--output")
    ptbr_audit.add_argument("--json-output")
    ptbr_audit.add_argument("--allow-issues", action="store_true")
    ptbr_brief = style_sub.add_parser("ptbr-brief")
    ptbr_brief.add_argument("--deliverable", required=True)
    ptbr_brief.add_argument("--audience", default="pesquisador")
    ptbr_brief.add_argument("--output")
    ptbr_naturalize = style_sub.add_parser("ptbr-naturalize")
    ptbr_naturalize.add_argument("input_path")
    ptbr_naturalize.add_argument("--output", required=True)
    ptbr_naturalize.add_argument("--json-output")
    anti_ai_audit = style_sub.add_parser("anti-ai-audit")
    anti_ai_audit.add_argument("paths", nargs="+")
    anti_ai_audit.add_argument("--output")
    anti_ai_audit.add_argument("--json-output")
    anti_ai_audit.add_argument("--strict", action="store_true")
    anti_ai_audit.add_argument("--allow-issues", action="store_true")
    anti_ai_naturalize = style_sub.add_parser("anti-ai-naturalize")
    anti_ai_naturalize.add_argument("input_path")
    anti_ai_naturalize.add_argument("--output", required=True)
    anti_ai_naturalize.add_argument("--json-output")

    publish_parser = subparsers.add_parser("publish")
    publish_sub = publish_parser.add_subparsers(dest="publish_command", required=True)
    publish_prep = publish_sub.add_parser("prepare")
    publish_prep.add_argument("project_dir")
    publish_prep.add_argument("--journal", required=True, help="Target journal name or preset (e.g. Transplantation, Annals of Surgery)")
    publish_prep.add_argument("--slug", default="artigo_principal", help="Package slug/identifier")
    publish_prep.add_argument("--version", default="v01", help="Deliverable version (default v01)")
    publish_rebuttal = publish_sub.add_parser("rebuttal", help="Motor de Resposta a Pareceristas e Rebuttal Ponto-a-Ponto")
    publish_rebuttal.add_argument("project_dir")
    publish_rebuttal.add_argument("--peer-review", required=True, help="Arquivo contendo a carta de parecer dos revisores")
    publish_rebuttal.add_argument("--journal", default="", help="Revista de destino (ex: Transplantation, Annals of Surgery)")
    publish_rebuttal.add_argument("--slug", default="artigo_principal", help="Identificador do pacote de submissao")

    portal_parser = subparsers.add_parser("portal", help="Gerenciador de Portais Colaborativos de Recuperação de Artigos (Web / Firebase / Storage / Drive)")
    portal_sub = portal_parser.add_subparsers(dest="portal_command", required=True)
    
    portal_build = portal_sub.add_parser("build")
    portal_build.add_argument("project_dir")
    portal_build.add_argument("--firebase-project", default="pharosreader")
    portal_build.add_argument("--target-dir")
    
    portal_deploy = portal_sub.add_parser("deploy")
    portal_deploy.add_argument("project_dir")
    portal_deploy.add_argument("--firebase-project", default="pharosreader")
    
    portal_sync = portal_sub.add_parser("sync")
    portal_sync.add_argument("project_dir")
    portal_sync.add_argument("--bucket", default="pharosreader.firebasestorage.app")
    
    portal_status_cmd = portal_sub.add_parser("status")
    portal_status_cmd.add_argument("project_dir")

    bench_parser = subparsers.add_parser("bench", help="Protocolos de Bancada e Laboratório Pré-Clínico / Translacional")
    bench_sub = bench_parser.add_subparsers(dest="bench_command", required=True)
    bench_template = bench_sub.add_parser("template")
    bench_template.add_argument("project_dir")
    bench_template.add_argument("--assay", required=True, choices=["elisa", "western", "rt-qpcr", "chiu", "suzuki", "teer", "biobank"])
    bench_template.add_argument("--name", default="")
    bench_manifest = bench_sub.add_parser("sample-manifest")
    bench_manifest.add_argument("project_dir")
    bench_manifest.add_argument("--audit", action="store_true")

    landmark_parser = subparsers.add_parser("landmark", help="Motor de Aprendizado e Dissecação de Artigos Seminais de Elite")
    landmark_sub = landmark_parser.add_subparsers(dest="landmark_command", required=True)
    landmark_search = landmark_sub.add_parser("search")
    landmark_search.add_argument("--query", required=True)
    landmark_search.add_argument("--limit", type=int, default=5)
    landmark_dissect = landmark_sub.add_parser("dissect")
    landmark_dissect.add_argument("project_dir")
    landmark_dissect.add_argument("--title", required=True)
    landmark_dissect.add_argument("--journal", required=True)
    landmark_dissect.add_argument("--year", default="2024")
    landmark_dissect.add_argument("--doi", required=True)
    landmark_dissect.add_argument("--authors", default="Autores Principais")
    landmark_dissect.add_argument("--endpoint", default="")
    landmark_dissect.add_argument("--design", default="")
    landmark_dissect.add_argument("--slug", default="")

    landmark_corpus_plan = landmark_sub.add_parser("corpus-plan")
    landmark_corpus_plan.add_argument("project_dir")
    landmark_corpus_plan.add_argument("--count", type=int, default=1000)

    landmark_corpus_mine = landmark_sub.add_parser("corpus-mine")
    landmark_corpus_mine.add_argument("project_dir")

    landmark_corpus_atlas = landmark_sub.add_parser("corpus-atlas")
    landmark_corpus_atlas.add_argument("project_dir")

    audit_parser = subparsers.add_parser("audit", help="Auditor Hostil de Incongruencias Texto-Tabela-Figura e Evidencias")
    audit_sub = audit_parser.add_subparsers(dest="audit_command", required=True)
    audit_numbers = audit_sub.add_parser("numbers", help="Audita consistencia matematica de ICs, p-valores, n amostrais e overclaims")
    audit_numbers.add_argument("project_dir")
    audit_numbers.add_argument("--strict", action="store_true", help="Falha se encontrar violacoes ou inconsistencias")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "plugins":
        _print(audit_scientific_plugins(Path(args.workspace_root).resolve()))
        return 0

    if args.command == "publish":
        if args.publish_command == "prepare":
            from .services.publication_packager import prepare_publication_package
            payload = prepare_publication_package(
                project_dir=Path(args.project_dir),
                target_journal=args.journal,
                package_slug=args.slug,
                version=args.version,
            )
            _print(payload)
            return 0
        elif args.publish_command == "rebuttal":
            from .services.peer_rebuttal_engine import generate_peer_rebuttal_package
            payload = generate_peer_rebuttal_package(
                project_dir=Path(args.project_dir),
                peer_review_path=Path(args.peer_review),
                target_journal=args.journal,
                package_slug=args.slug,
            )
            _print(payload)
            return 0 if payload.get("status") in {"pass", "created"} else 1

    if args.command == "bench":
        from .services.bench_protocols import generate_bench_template, validate_sample_manifest
        project_dir = Path(args.project_dir)
        if args.bench_command == "template":
            res = generate_bench_template(project_dir, args.assay, args.name)
            _print(res)
            return 0
        elif args.bench_command == "sample-manifest":
            manifest_file = project_dir / "experiments" / "samples" / "sample_manifest.csv"
            if args.audit:
                res = validate_sample_manifest(manifest_file)
                _print(res)
                return 0 if res.get("status") in {"pass", "warning"} else 1
            else:
                res = generate_bench_template(project_dir, "biobank")
                _print(res)
                return 0

    if args.command == "landmark":
        from .services.landmark_learning import search_landmark_papers, dissect_landmark_paper
        if args.landmark_command == "search":
            res = search_landmark_papers(args.query, limit=args.limit)
            _print(res)
            return 0
        elif args.landmark_command == "dissect":
            res = dissect_landmark_paper(
                project_dir=Path(args.project_dir),
                title=args.title,
                journal=args.journal,
                year=args.year,
                doi=args.doi,
                authors=args.authors,
                primary_endpoint=args.endpoint,
                study_design=args.design,
                slug=args.slug,
            )
            _print(res)
            return 0
        elif args.landmark_command == "corpus-plan":
            from .services.landmark_corpus_engine import plan_landmark_corpus
            res = plan_landmark_corpus(args.project_dir, target_count=args.count)
            _print(res)
            return 0
        elif args.landmark_command == "corpus-mine":
            from .services.landmark_corpus_engine import mine_landmark_corpus
            res = mine_landmark_corpus(args.project_dir)
            _print(res)
            return 0
        elif args.landmark_command == "corpus-atlas":
            from .services.landmark_corpus_engine import generate_corpus_atlas
            json_p, md_p = generate_corpus_atlas(args.project_dir)
            _print({"status": "generated", "atlas_json": str(json_p), "atlas_markdown": str(md_p)})
            return 0

    if args.command == "audit":
        from .services.numerical_consistency_auditor import audit_numerical_consistency
        if args.audit_command == "numbers":
            res = audit_numerical_consistency(Path(args.project_dir))
            _print(res)
            if args.strict and res.get("status") in {"block", "warning"}:
                return 1
            return 0 if res.get("status") != "block" else 1

    if args.command == "portal":
        from .services.retrieval_portal import build_portal, portal_status, sync_portal
        import subprocess
        if args.portal_command == "build":
            payload = build_portal(
                project_dir=Path(args.project_dir),
                target_dir=Path(args.target_dir) if args.target_dir else None,
                firebase_project=args.firebase_project,
            )
            _print(payload)
            return 0 if payload.get("status") == "pass" else 1
        if args.portal_command == "sync":
            payload = sync_portal(
                project_dir=Path(args.project_dir),
                bucket=args.bucket,
            )
            _print(payload)
            return 0 if payload.get("status") == "pass" else 1
        if args.portal_command == "status":
            payload = portal_status(Path(args.project_dir))
            _print(payload)
            return 0
        if args.portal_command == "deploy":
            portal_dir = Path(args.project_dir) / "portal_recuperacao"
            if not portal_dir.is_dir():
                build_portal(Path(args.project_dir), firebase_project=args.firebase_project)
            cmd = f'firebase deploy --only "hosting,storage" --project {args.firebase_project}'
            res = subprocess.run(cmd, cwd=str(portal_dir), shell=True, capture_output=True, text=True)
            payload = {
                "contract": "DeployPortalResult",
                "status": "pass" if res.returncode == 0 else "error",
                "output": res.stdout,
                "error": res.stderr if res.returncode != 0 else ""
            }
            _print(payload)
            return 0 if res.returncode == 0 else 1

    if args.command == "workflow":
        try:
            if args.workflow_command == "plan":
                payload = plan_scientific_workflow(Path(args.project_dir), args.query, args.language)
            else:
                payload = audit_language(Path(args.project_dir), args.language, args.draft, args.reference)
        except (OSError, ValueError) as exc:
            payload = {"status": "block", "gate_eligible": False, "issues": [str(exc)]}
        _print(payload)
        return 0 if payload.get("status") in {"pass", "planned"} else 1

    if args.command == "init":
        project_dir = init_project(Path(args.workspace_root), args.name, args.project_type)
        _print({"status": "created", "project_dir": str(project_dir)})
        return 0
    if args.command == "preflight":
        payload = preflight(Path(args.project_dir))
        _print(payload)
        return 0 if payload.get("status") in {"pass", "passed"} else 1
    if args.command == "env":
        project_dir = Path(args.project_dir)
        if args.env_command == "check":
            payload = check_environment(project_dir, args.runtime)
        else:
            payload = prepare_environment(project_dir, args.runtime, execute=not bool(args.dry_run))
        _print(payload)
        return 0 if payload.get("status") in {"pass", "passed"} else 1
    if args.command == "ingest":
        payload = register_source(Path(args.project_dir), args.source, args.kind)
        _print(payload)
        return 1 if payload.get("status") == "blocked" else 0
    if args.command == "registry" and args.registry_command == "verify":
        from .services.protocol_registration import verify_protocol_registration

        try:
            payload = verify_protocol_registration(Path(args.project_dir), Path(args.record))
        except (OSError, ValueError, TypeError) as exc:
            payload = {"status": "blocked", "issues": [str(exc)]}
        _print(payload)
        return 0 if payload.get("status") == "pass" else 1
    if args.command == "registry" and args.registry_command == "register":
        _print(
            register_review_protocol(
                Path(args.project_dir),
                registry=args.registry,
                registry_id=args.registry_id,
                registry_url=args.registry_url,
                registered_at=args.registered_at,
                notes=args.notes,
            )
        )
        return 0
    if args.command == "registry" and args.registry_command == "check-osf":
        from .services.osf import verify_osf_connection

        payload = verify_osf_connection(token=args.token)
        _print(payload)
        return 0 if payload.get("status") == "pass" else 1
    if args.command == "registry" and args.registry_command == "fetch-osf":
        from .services.osf import fetch_and_save_osf_evidence

        payload = fetch_and_save_osf_evidence(
            Path(args.project_dir),
            registration_id=args.registry_id,
            reviewer=args.reviewer,
            token=args.token,
        )
        _print(payload)
        return 0 if payload.get("status") == "pass" else 1
    if args.command == "methodology":
        from .services.extraction_validator import load_extraction_records, validate_extraction_records
        from .services.methodology_engine import (
            audit_equator_compliance,
            compile_registration_packet,
            validate_protocol_methodology,
        )
        from .services.results_ledger import audit_numerical_consistency

        if args.methodology_command == "validate-protocol":
            payload = validate_protocol_methodology(Path(args.project_dir))
        elif args.methodology_command == "compile-registration-packet":
            payload = compile_registration_packet(Path(args.project_dir))
        elif args.methodology_command == "audit-equator":
            payload = audit_equator_compliance(Path(args.project_dir))
        elif args.methodology_command == "validate-extraction":
            records = load_extraction_records(Path(args.file_path))
            payload = validate_extraction_records(records, mode=args.mode)
        elif args.methodology_command == "prisma-checklist":
            from .services.screening_engine import TripleReviewerScreeningEngine
            engine = TripleReviewerScreeningEngine(Path(args.project_dir))
            engine.generate_prisma_checklists()
            payload = {"contract": "PRISMAChecklistReportV1", "status": "pass", "project_dir": str(args.project_dir)}
        else:
            payload = audit_numerical_consistency(Path(args.project_dir))
        _print(payload)
        return 0 if payload.get("status") == "pass" else 1
    if args.command == "corpus":
        from .services.corpus_pipeline import (
            execute_pubmed_api_search,
            execute_scopus_api_search,
            ingest_drop_folders_and_deduplicate,
            prepare_search_workspace,
            verify_scopus_connection,
        )

        if args.corpus_command == "prepare":
            payload = prepare_search_workspace(Path(args.project_dir))
        elif args.corpus_command == "fetch-pubmed":
            payload = execute_pubmed_api_search(Path(args.project_dir), max_records=args.max_records)
        elif args.corpus_command == "fetch-scopus":
            payload = execute_scopus_api_search(Path(args.project_dir), max_records=args.max_records)
        elif args.corpus_command == "check-scopus":
            payload = verify_scopus_connection(Path(args.project_dir))
        elif args.corpus_command == "screen":
            from .services.screening_engine import run_triple_screening_command
            payload = run_triple_screening_command(Path(args.project_dir))
        else:
            payload = ingest_drop_folders_and_deduplicate(Path(args.project_dir))
        _print(payload)
        return 0 if payload.get("status") == "pass" else 1
    if args.command == "datasets":
        from .services.clinical_datasets import (
            DATASET_SPECIALTY_PACKS,
            fetch_open_dataset,
            fetch_specialty_pack,
            ingest_and_verify_dataset,
            list_clinical_datasets,
            prepare_dataset_stage,
        )

        if args.datasets_command == "catalog":
            items = list_clinical_datasets(
                domain=args.domain,
                access_tier=args.access_tier,
                query=args.query,
                auto_fetchable_only=bool(getattr(args, "auto_only", False)),
            )
            payload = {
                "status": "pass",
                "count": len(items),
                "auto_fetchable_count": sum(1 for d in items if d.get("auto_fetchable")),
                "datasets": items,
            }
        elif args.datasets_command == "packs":
            payload = {"status": "pass", "packs": DATASET_SPECIALTY_PACKS}
        elif args.datasets_command == "stage":
            ids = [s.strip() for s in args.ids.split(",") if s.strip()] if args.ids else None
            payload = prepare_dataset_stage(Path(args.project_dir), dataset_ids=ids)
        elif args.datasets_command == "fetch":
            payload = fetch_open_dataset(Path(args.project_dir), dataset_id=args.dataset_id)
        elif args.datasets_command == "fetch-pack":
            payload = fetch_specialty_pack(Path(args.project_dir), pack_id=args.pack_id)
        else:
            payload = ingest_and_verify_dataset(Path(args.project_dir), dataset_id=args.dataset_id)
        _print(payload)
        return 0 if payload.get("status") == "pass" else 1
    if args.command == "hygiene":
        from .services.workspace_hygiene import (
            audit_workspace_hygiene,
            install_git_hygiene_hook,
            organize_project_strays,
            write_active_mode_guide,
        )

        if args.hygiene_command == "check":
            payload = audit_workspace_hygiene(Path(args.workspace_root), check_staged=args.staged)
        elif args.hygiene_command == "bindings":
            payload = write_active_mode_guide(Path(args.project_dir), mode=args.mode)
        elif args.hygiene_command == "organize":
            payload = organize_project_strays(Path(args.project_dir), apply=args.apply)
        else:
            payload = install_git_hygiene_hook(Path(args.workspace_root))
        _print(payload)
        return 0 if payload.get("status") == "pass" else 1
    if args.command == "study":
        from .services.study_and_synthesis import build_project_study_guide

        payload = build_project_study_guide(Path(args.project_dir))
        _print(payload)
        return 0 if payload.get("status") == "pass" else 1
    if args.command == "synthesis":
        from .services.study_and_synthesis import (
            harvest_analysis_outputs,
            list_synthesis_templates,
            synthesize_from_r_outputs,
        )

        if args.synthesis_command == "templates":
            payload = list_synthesis_templates()
        elif args.synthesis_command == "harvest":
            payload = harvest_analysis_outputs(Path(args.project_dir))
        else:
            payload = synthesize_from_r_outputs(
                Path(args.project_dir),
                publication_template_id=args.publication_template,
                slide_template_id=args.slide_template,
                poster_template_id=args.poster_template,
                slug=args.slug,
            )
        _print(payload)
        return 0 if payload.get("status") == "pass" else 1
    if args.command == "document":
        from .services.document_extraction import (
            extract_document,
            extract_documents,
            extract_project_documents,
            resolve_tesseract,
        )

        if args.document_command == "test-tesseract":
            payload = resolve_tesseract()
        elif args.document_command == "project-extract":
            payload = extract_project_documents(
                Path(args.project_dir),
                input_path=Path(args.input_path) if args.input_path else None,
                ocr=args.ocr,
                lang=args.lang,
                table_strategy=args.table_strategy,
                force=bool(args.force),
            )
        else:
            in_p = Path(args.input_path)
            out_p = Path(args.output_root) if args.output_root else in_p.parent
            if in_p.is_file():
                payload = extract_document(
                    in_p,
                    out_p,
                    ocr=args.ocr,
                    lang=args.lang,
                    dpi=args.dpi,
                    table_strategy=args.table_strategy,
                    max_pages=args.max_pages,
                    force=bool(args.force),
                )
            else:
                payload = extract_documents(
                    in_p,
                    out_p,
                    ocr=args.ocr,
                    lang=args.lang,
                    dpi=args.dpi,
                    table_strategy=args.table_strategy,
                    max_pages=args.max_pages,
                    force=bool(args.force),
                )
        _print(payload)
        return 0 if payload.get("status") in {"pass", True} or payload.get("available") is True else 1
    if args.command == "prospero":
        from .services.prospero_assistant import (
            compile_prospero_40_fields,
            launch_prospero_browser_assistant,
        )

        if args.prospero_command == "compile":
            payload = compile_prospero_40_fields(Path(args.project_dir))
        else:
            payload = launch_prospero_browser_assistant(
                Path(args.project_dir),
                dry_run=bool(args.dry_run),
                headless=bool(args.headless),
            )
        _print(payload)
        return 0 if payload.get("status") == "pass" else 1
    if args.command == "context" and args.context_command == "build":
        payload = build_task_packet(Path(args.project_dir), args.mode, args.hypothesis)
        _print(payload)
        return 0 if payload.get("status") == "passed" else 1
    if args.command == "analyze":
        project_dir = Path(args.project_dir)
        transition = advance_mode(project_dir, args.mode)
        if transition["status"] != "passed":
            attempt_path = record_blocked_attempt(project_dir, "analyze", {"mode": args.mode, "transition": transition})
            _print({"transition": transition, "task_packet": None, "attempt": str(attempt_path), "status": "blocked"})
            return 1
        packet = build_task_packet(project_dir, args.mode, args.hypothesis)
        payload = {"task_packet": packet, "transition": transition, "status": "passed"}
        if args.mode == "discovery" and transition["status"] == "passed":
            payload["discovery_plan"] = build_discovery_plan(project_dir)
        _print(payload)
        return 0
    if args.command == "run-r":
        payload = run_r_script(Path(args.project_dir), Path(args.script_path))
        _print(payload)
        return 0 if payload.get("status") in {"pass", "passed"} else 1
    if args.command == "run-python":
        payload = run_python_script(Path(args.project_dir), Path(args.script_path))
        _print(payload)
        return 0 if payload.get("status") in {"pass", "passed"} else 1
    if args.command == "draft":
        project_dir = Path(args.project_dir)
        gate = _require_command_mode(project_dir, "draft", "drafting")
        if gate["status"] != "pass":
            _print(gate)
            return 1
        report = validate_evidence_lock(project_dir)
        _print(report)
        return 0 if report.get("gate_eligible") is True else 1
    if args.command == "review":
        project_dir = Path(args.project_dir)
        gate = _require_command_mode(project_dir, "review", "review-trinity")
        if gate["status"] != "pass":
            _print(gate)
            return 1
        report = run_review_trinity(project_dir)
        _print(report)
        return 0 if report.get("gate_eligible") is True else 1
    if args.command == "export":
        project_dir = Path(args.project_dir)
        gate = _require_command_mode(project_dir, "export", "submission")
        if gate["status"] != "pass":
            _print(gate)
            return 1
        stage_gate = audit_stage(project_dir, target_mode="submission")
        if stage_gate.get("gate_eligible") is not True:
            _print(stage_gate)
            return 1
        export_path = project_dir / "exports" / "project_summary.json"
        payload = {
            "project_dir": str(project_dir),
            "manuscript": str(project_dir / "drafts" / "manuscript.md"),
            "review_report": str(project_dir / "reviews" / "review_report.json"),
        }
        export_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        _print({"status": "exported", "path": str(export_path)})
        return 0
    if args.command == "congress" and args.congress_command == "import":
        _print(
            import_conference_requirements(
                Path(args.project_dir),
                source=args.source,
                kind=args.kind,
                slug=args.slug,
                profile=args.profile,
                crawl=args.crawl,
                authors=args.authors,
                affiliations=args.affiliations,
                qr_url=args.qr_url,
                logos=args.logos,
            )
        )
        return 0
    if args.command == "congress" and args.congress_command == "save-profile":
        _print(save_congress_profile(Path(args.deliverable_dir), args.profile))
        return 0
    if args.command == "congress" and args.congress_command == "use-profile":
        _print(use_congress_profile(Path(args.project_dir), args.profile, args.slug))
        return 0
    if args.command in {"deck", "poster"}:
        action = args.deck_command if args.command == "deck" else args.poster_command
        deliverable_dir = Path(args.deliverable_dir)
        if action == "plan":
            _print(plan_deliverable(deliverable_dir))
            return 0
        if action == "build":
            _print(build_deliverable(deliverable_dir))
            return 0
        if action == "qa":
            payload = qa_deliverable(deliverable_dir)
            _print(payload)
            return 1 if payload.get("status") in {"block", "blocked", "failed", "fail"} else 0
        if action == "export":
            payload = export_deliverable(deliverable_dir, strict=bool(getattr(args, "strict", False)))
            _print(payload)
            return 1 if payload.get("status") in {"block", "blocked", "failed", "fail"} else 0
    if args.command == "submit":
        _print(
            submit_deliverable(
                Path(args.deliverable_dir),
                action="dry-run" if args.submit_command == "dry-run" else "run",
                confirm=bool(getattr(args, "confirm", False)),
            )
        )
        return 0
    if args.command == "life-science":
        plugin_root = Path(args.plugin_root) if getattr(args, "plugin_root", None) else None
        if args.life_science_command == "catalog":
            _print(catalog_life_science_skills(plugin_root))
            return 0
        if args.life_science_command == "plan":
            _print(plan_life_science_retrieval(Path(args.project_dir), args.question, plugin_root))
            return 0
    if args.command == "skills":
        skills_dir = Path(args.skills_dir) if getattr(args, "skills_dir", None) else None
        if args.skills_command == "catalog":
            _print(catalog_workspace_skills(skills_dir))
            return 0
        if args.skills_command == "audit":
            payload = audit_workspace_skills(skills_dir, strict=bool(args.strict), provenance=bool(args.provenance))
            _print(payload)
            return 0 if payload.get("status") == "pass" else 1
        if args.skills_command == "route":
            _print(route_workspace_skills(args.query, skills_dir, limit=args.limit))
            return 0
        if args.skills_command == "update-plan":
            payload = build_skill_update_plan(Path(args.workspace_root).resolve())
            _print(payload)
            return 0 if payload.get("status") == "pass" else 1
    if args.command == "journal":
        presets_dir = Path(args.presets_dir) if getattr(args, "presets_dir", None) else None
        if args.journal_command == "catalog":
            _print(catalog_journals(domain=args.domain, tier=args.tier, presets_dir=presets_dir))
            return 0
        if args.journal_command == "verify":
            _print(verify_journal_presets(presets_dir))
            return 0
        if args.journal_command == "route":
            _print(
                route_journals(Path(args.project_dir), domain=args.domain, limit=args.limit, presets_dir=presets_dir)
            )
            return 0
        if args.journal_command == "report":
            _print(write_journal_report(Path(args.project_dir), domain=args.domain, presets_dir=presets_dir))
            return 0
    if args.command == "guard" and args.guard_command == "check":
        _print(run_guard_check(Path(args.project_dir)))
        return 0
    if args.command == "query":
        if args.query_command == "validate":
            _print(validate_query_plan(Path(args.project_dir)))
            return 0
        if args.query_command == "compile":
            _print(compile_query_plan(Path(args.project_dir)))
            return 0
    if args.command == "retrieval":
        if args.retrieval_command == "plan":
            _print(build_retrieval_plan(Path(args.project_dir)))
            return 0
        if args.retrieval_command == "audit":
            _print(audit_retrieval(Path(args.project_dir)))
            return 0
    if args.command == "idea" and args.idea_command == "tournament":
        _print(run_idea_tournament(Path(args.project_dir)))
        return 0
    if args.command == "stage" and args.stage_command == "audit":
        payload = audit_stage(Path(args.project_dir), target_mode=args.target_mode)
        _print(payload)
        return 0 if payload.get("gate_eligible") is True else 1
    if args.command == "benchmark" and args.benchmark_command == "validate":
        payload = validate_benchmark_report(Path(args.project_dir))
        _print(payload)
        return 0 if payload.get("gate_eligible") is True else 1
    if args.command == "benchmark" and args.benchmark_command == "aggregate":
        payload = aggregate_benchmark_file(
            Path(args.project_dir),
            input_path=Path(args.input) if args.input else None,
            output_path=Path(args.output) if args.output else None,
        )
        _print(payload)
        return 0 if payload.get("gate_eligible") is True else 1
    if args.command == "graph" and args.graph_command == "query":
        try:
            payload = query_operational_graph(
                args.query,
                scope=args.scope,
                limit=args.limit,
                graph_path=Path(args.graph_path) if args.graph_path else None,
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            payload = {"status": "block", "issues": [str(exc)]}
        _print(payload)
        return 0 if payload.get("status") == "ok" else 1
    if args.command == "machine" and args.machine_command == "audit":
        strict = bool(args.strict)
        payload = run_machine_audit(Path(args.workspace_root), strict=strict)
        _print(payload)
        if strict and payload.get("status") != "pass":
            return 1
        return 0
    if args.command == "machine" and args.machine_command == "doctor":
        payload = machine_doctor(Path(args.workspace_root), Path(args.project_dir) if args.project_dir else None)
        _print(payload)
        return 0 if payload.get("status") == "pass" else 1
    if args.command == "machine" and args.machine_command == "release-audit":
        payload = release_audit(Path(args.project_dir))
        _print(payload)
        return 0 if payload.get("gate_eligible") is True else 1
    if args.command == "style" and args.style_command == "ptbr-audit":
        payload = write_audit_reports(
            args.paths,
            Path(args.output) if args.output else None,
            Path(args.json_output) if args.json_output else None,
        )
        _print(payload)
        if payload["status"] == "block" and not args.allow_issues:
            return 1
        return 0
    if args.command == "style" and args.style_command == "anti-ai-audit":
        payload = write_audit_reports(
            args.paths,
            Path(args.output) if args.output else None,
            Path(args.json_output) if args.json_output else None,
            profile="anti_ai",
            title="Auditoria Anti-IA De Escrita Científica",
            strict=bool(args.strict),
        )
        _print(payload)
        if payload["status"] == "block" and not args.allow_issues:
            return 1
        return 0
    if args.command == "style" and args.style_command == "ptbr-brief":
        text = build_generation_brief(deliverable=args.deliverable, audience=args.audience)
        if args.output:
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(text, encoding="utf-8")
            _print({"status": "written", "path": str(output)})
        else:
            print(text)
        return 0
    if args.command == "style" and args.style_command == "ptbr-naturalize":
        input_path = Path(args.input_path)
        output_path = Path(args.output)
        original_text = read_text_for_audit(input_path)
        revised_text = naturalize_text(original_text)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(revised_text, encoding="utf-8")
        payload = {
            "status": audit_text(revised_text, path=output_path)["status"],
            "input": str(input_path),
            "output": str(output_path),
            "original_report": audit_text(original_text, path=input_path),
            "revised_report": audit_text(revised_text, path=output_path),
        }
        if args.json_output:
            json_output = Path(args.json_output)
            json_output.parent.mkdir(parents=True, exist_ok=True)
            json_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        _print(payload)
        return 0
    if args.command == "style" and args.style_command == "anti-ai-naturalize":
        input_path = Path(args.input_path)
        output_path = Path(args.output)
        original_text = read_text_for_audit(input_path)
        revised_text = anti_ai_naturalize_text(original_text)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(revised_text, encoding="utf-8")
        payload = {
            "status": audit_text(revised_text, path=output_path, profile="anti_ai")["status"],
            "input": str(input_path),
            "output": str(output_path),
            "original_report": audit_text(original_text, path=input_path, profile="anti_ai"),
            "revised_report": audit_text(revised_text, path=output_path, profile="anti_ai"),
        }
        if args.json_output:
            json_output = Path(args.json_output)
            json_output.parent.mkdir(parents=True, exist_ok=True)
            json_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        _print(payload)
        return 0
    return 1
