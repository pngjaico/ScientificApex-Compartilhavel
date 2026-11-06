---
name: extraction-schema-governor
description: Use when designing, validating, piloting, or auditing structured extraction forms, variable dictionaries, dual extraction, conflict resolution, or data provenance.
---

# Extraction Schema Governor

Use this skill before extracting evidence from papers, registries, PDFs, spreadsheets, or public datasets.

## Gate
- Write the extraction schema before extraction starts.
- Store it under `context/extraction_schema.yaml`.
- Define variable name, type, unit, allowed values, source location, extraction rule, missingness code, and reviewer notes.
- Pilot the schema on at least two heterogeneous records before full extraction.
- Record conflicts and resolutions; do not silently overwrite reviewer values.

## Required Outputs
- `context/extraction_schema.yaml`
- `analysis/extraction_pilot_report.json`
- `evidence/extraction_manifest.jsonl`
- conflict log when dual extraction is used

## Red Flags
- Extracting numeric outcomes without units/timepoints.
- Mixing adjusted and unadjusted estimates in one column.
- Converting medians/IQRs or graph-derived values without an explicit method.
- Using LLM extraction without page, quote, table/figure, and confidence provenance.

## Integration
- Use with `risk-of-bias-assistant` for bias fields.
- Use with `tooluniverse-meta-analysis` only after effect direction, scale, and standard error rules are explicit.
- Use with `evidence-lock-hardener` before any extracted value supports a manuscript claim.
