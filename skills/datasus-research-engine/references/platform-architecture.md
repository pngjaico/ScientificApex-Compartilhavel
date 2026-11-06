# Platform Architecture

Implement first as an MVP. Do not attempt the full platform before the smoke lane runs.

## MVP Lane

- Python package with CLI.
- FastAPI endpoint `/studies/{study_id}/run-full`.
- SIH/RD only.
- SP, 2024, months 1-2.
- CID K40.
- Parquet cache and DuckDB registration.
- Three figures, three tables, Markdown technical report.
- Tests for topic parsing, YAML generation, cohort filters, indicators, and report creation.

## Full Package Layout

```text
med-datasus-research-engine/
  pyproject.toml
  data/
    raw/
    parquet/
    duckdb/
    exports/
    dictionaries/
  studies/
    examples/
    generated/
  notebooks/
    generated/
  reports/
    templates/
    generated/
  figures/generated/
  tables/generated/
  src/meddatasus/
    api/
    cli/
    datasources/
    dictionaries/
    topic_parser/
    cohort/
    storage/
    analysis/
    visualization/
    reporting/
    workflows/
    utils/
  tests/
```

## Required API

- `GET /`
- `GET /health`
- `POST /studies/from-topic`
- `GET /studies`
- `GET /studies/{study_id}`
- `POST /studies/{study_id}/validate-codes`
- `POST /studies/{study_id}/download-data`
- `POST /studies/{study_id}/build-cohort`
- `POST /studies/{study_id}/run-analysis`
- `POST /studies/{study_id}/generate-figures`
- `POST /studies/{study_id}/generate-report`
- `POST /studies/{study_id}/run-full`
- `GET /studies/{study_id}/outputs`
- `GET /catalog/icd10/search`
- `GET /catalog/sigtap/search`
- `GET /datasets/availability`

## Required CLI

```bash
meddatasus create-study "hernia inguinal no Brasil de 2018 a 2025"
meddatasus run-full studies/generated/hernia_inguinal_brazil_2018_2025.yaml
meddatasus download --dataset SIH --group RD --states SP RJ MG --years 2018 2019 2020
meddatasus api
meddatasus export --study-id hernia_inguinal_brazil_2018_2025
```

## Optional LLM Mode

- The non-LLM path must run from user-provided YAML.
- LLM mode may suggest question, codes, outcomes, and YAML.
- `OPENAI_API_KEY` is optional and must never be required for extraction or analysis.
- LLM outputs are suggestions only, never validated codes.
