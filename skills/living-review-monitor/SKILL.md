---
name: living-review-monitor
description: Use when setting up, auditing, or refreshing living searches, update alerts, surveillance queries, new preprint checks, trial updates, or evidence-change monitoring.
---

# Living Review Monitor

Use this skill when a project needs evidence freshness rather than a one-time search snapshot.

## Gate
- Start from `context/query_plan.yaml`; do not invent a new live query outside the approved search strategy.
- Define providers, cadence, date windows, alert thresholds, owner, and stop conditions.
- Store snapshots under `sources/living_review/<provider>/<date>/`.
- Record new records, changed records, deduplication keys, and screened/unscreened status in a manifest.
- Do not update manuscript conclusions until new evidence passes screening, extraction, risk-of-bias, and Evidence Lock.

## Provider Routes
- PubMed/Europe PMC for biomedical literature.
- bioRxiv/medRxiv for recent preprints with explicit preprint caveats.
- ClinicalTrials.gov for trial status/results changes.
- Crossref/OpenAlex/Semantic Scholar for metadata/citation changes.
- Retraction/integrity routes for safety checks.

## Required Outputs
- `context/living_review_plan.yaml`
- `sources/living_review/manifest.jsonl`
- `reviews/evidence_freshness_report.md`

## Red Flags
- Treating a new preprint as practice-changing evidence.
- Updating the claim map without refreshing references and source excerpts.
- Running broad recurring searches without deduplication and stop rules.
