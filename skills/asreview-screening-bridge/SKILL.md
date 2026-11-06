---
name: asreview-screening-bridge
description: Use when systematic review title/abstract screening needs active learning, ASReview-compatible exports, prioritization, reviewer labels, stopping rules, recall audits, or transparent semi-automated screening.
---

# ASReview Screening Bridge

Use this skill to accelerate screening while preserving auditability and human reviewer control.

## Workflow
1. Prepare records with title, abstract, DOI/PMID, source database, and deduplication status.
2. Export a clean CSV/TSV suitable for active-learning screening.
3. Define inclusion/exclusion criteria from `protocol.yaml`.
4. Track reviewer labels, conflicts, model prioritization, and stopping decisions.
5. Save screening logs under `evidence/screening/`.
6. Update PRISMA counts only from auditable screening decisions.

## Gates
- Do not let active learning silently exclude records.
- Require human review for included studies and uncertain exclusions.
- Record the stopping rule before using it.
