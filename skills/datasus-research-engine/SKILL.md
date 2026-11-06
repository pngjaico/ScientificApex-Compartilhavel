---
name: datasus-research-engine
description: Use when creating, running, auditing, or expanding DATASUS/SUS epidemiology workflows from natural-language topics or YAML, including PySUS, SIH/RD, SIM, SIA, SINASC, CNES, PNI, IBGE, TABNET/FTP transfer, Parquet/DuckDB caching, cohort filters, indicators, figures, tables, reports, and scientific quality gates.
---

# DATASUS Research Engine

## Core Rule

Build the workflow as `topic -> study YAML -> source extraction -> cache -> cohort -> analysis -> figures/tables -> report -> QC`. Do not collapse these stages into one notebook or script.

The output is a complete research dossier for human review, not a publication-ready article. CID-10 and SIGTAP codes must stay separated as `suggested`, `user_confirmed`, and `analysis_used`.

## First Actions

1. Work inside an Article Machine project when the task involves evidence, analysis, or manuscript output.
2. Read `project.yaml`, `protocol.yaml`, `standards.yaml`, and `compute.yaml`.
3. If the user gives only a topic, generate a study YAML first; use `scripts/create_study_yaml.py` for common starting points.
4. Mark codes and procedures as pending validation unless the user explicitly confirms them.
5. Start with MVP extraction before full Brazil: default smoke test is SIH/RD, SP, 2024, months 1-2, CID K40.

## References To Load

- `references/source-notes.md`: verified official sources and current PySUS surface.
- `references/study-yaml-contract.md`: canonical study config and validation statuses.
- `references/extraction-contract.md`: DATASUS/PySUS extraction, cache, DuckDB, retry, and no-overdownload rules.
- `references/analysis-reporting-contract.md`: indicators, tables, plots, reports, and scientific language gates.
- `references/platform-architecture.md`: full MedDataSUS Research Engine API/CLI/package architecture.

## Downstream Skills

- Use `database-retrieval-governor` before bulk retrieval or ambiguous data-source selection.
- Use `statistical-analysis`, `statsmodels`, and `statistical-power` for trend models, denominators, regression, and sample-size/power claims.
- Use `scientific-visualization` for article/congress figures.
- Use `ptbr-article-writing` for Portuguese reports, abstracts, or manuscripts.
- Use `conference-deliverable-router` before congress output.
- Use `evidence-lock-hardener` before claim-map promotion or manuscript readiness.

## Non-Negotiable Safeguards

- Do not load all-Brazil, multi-year microdata into pandas at once.
- Do not require an LLM for extraction or analysis.
- Do not invent CIDs, SIGTAP procedures, denominators, results, or references.
- Do not infer causality from ecological or administrative data.
- Do not hide partial extraction, missing months, unavailable files, schema drift, or failed downloads.
- Do not compare groups without naming the method and design limitations.

## Minimal Acceptance For A Real Implementation

- `pip install -e .` works.
- `pytest` passes.
- CLI can generate YAML from a topic.
- MVP `run-full` downloads or reads cached SIH/RD SP 2024 months 1-2, filters K40, and produces tables, figures, and a Markdown report.
- Outputs include reproducibility log, data quality log, and code-validation status.
- Reports label manuscript text as draft for human review.
