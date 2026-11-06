# Extraction Contract

## Supported Dataset Lanes

- SIH/RD: hospitalization admissions; default MVP lane.
- SIM: mortality.
- SIA: outpatient production.
- SINASC: live births.
- CNES: facilities and capacity context.
- PNI: immunization.
- IBGE: geography and denominators when available.

## Download Rules

- Download by UF, year, month, dataset, and group where applicable.
- Cache every file under `data/parquet/<dataset>/<group>/<uf>/<year>/`.
- Never re-download cached files unless `force_refresh=true`.
- Log every attempted file with status: `cached`, `downloaded`, `missing`, `failed`, `schema_error`.
- Implement retry with backoff for temporary network failures.
- Full Brazil multi-year extraction must require explicit production mode.

## PySUS Pattern

Prefer high-level PySUS functions for direct DataFrame work in MVPs:

```python
from pysus.api import sih, sim, cnes

df = sih(state="SP", year=2024, month=[1, 2], group="RD")
```

For a production engine, prefer lower-level catalog/download/read operations so provenance is explicit:

```python
from pysus import PySUS

async with PySUS() as client:
    files = await client.query(dataset="sih", group="RD", state="SP", year=2024, month=1)
    local_paths = [await client.download(item) for item in files]
    frame = client.read_parquet(local_paths, mode="union").df()
```

Check the installed PySUS version and adapt imports if the API moved. Do not silently switch APIs without logging it.

## DuckDB Contract

Create `data/duckdb/meddatasus.duckdb` with:

- `sih_rd`
- `sim_do`
- `sia`
- `cnes`
- `study_registry`
- `code_validation`
- `data_quality_log`
- `generated_outputs`

Create per-study views:

- `vw_{study_id}_cohort`
- `vw_{study_id}_annual_summary`
- `vw_{study_id}_by_sex`
- `vw_{study_id}_by_age_group`
- `vw_{study_id}_by_region`
- `vw_{study_id}_by_admission_type`

## Cohort Filters

Apply filters transparently and export counts before and after each filter:

- CID principal prefix.
- CID secundario prefix.
- SIGTAP procedure.
- UF, region, year, month.
- sex, age, admission type.
- optional exclusions.

The selection flow must be saved as table and narrative.
