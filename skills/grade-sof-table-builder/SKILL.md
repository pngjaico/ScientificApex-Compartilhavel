---
name: grade-sof-table-builder
description: Use when a review, meta-analysis, guideline, health technology assessment, diagnostic review, or clinical evidence project needs GRADE certainty ratings, Summary of Findings tables, evidence profiles, footnotes, or GRADEpro-ready outputs.
---

# GRADE SoF Table Builder

Use this skill after extraction, risk-of-bias assessment, and quantitative or narrative synthesis.

## Workflow
1. Define each critical and important outcome.
2. Pull effect estimates, absolute risks, event counts, sample sizes, and certainty inputs.
3. Rate risk of bias, inconsistency, indirectness, imprecision, publication bias, and upgrade factors when applicable.
4. Write transparent footnotes for every downgrade or upgrade.
5. Produce a Summary of Findings table and a GRADEpro-ready export when possible.
6. Link each row to `claim_id` entries and references.

## Gates
- Do not produce final recommendations from GRADE certainty alone.
- Block if risk-of-bias inputs are absent for included studies.
- Label narrative-only certainty separately from meta-analytic certainty.
