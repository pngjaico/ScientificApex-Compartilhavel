---
name: manuscript-integrity-response-governor
description: Use when reviewer comments, rebuttal letters, response to reviewers, parecerista responses, manuscript consistency, claim-strength calibration, reference integrity, citation integrity, figure/table-to-text consistency, or pre-submission manuscript repair is needed.
---

# Manuscript Integrity And Response Governor

Use this skill when the task is not just "make the prose nicer" but keeping a
scientific manuscript internally consistent, evidence-locked, and defensible
under reviewer pressure.

## Scope

Use for:

- Reviewer response letters, rebuttals, revision memos, and point-by-point response tables.
- Claim-strength calibration before submission, revision, thesis defense, or congress.
- Citation, reference, figure, table, abstract, result, limitation, and conclusion consistency checks.
- Detecting unsupported novelty, inflated language, missing caveats, and manuscript-wide contradictions.

Do not use this skill as a shortcut around `Evidence Lock`, `Review Trinity`, or
the active project mode. Use `ptbr-article-writing` for Portuguese prose style,
`anti-ai-writing-governor` for generic LLM-style cleanup, and
`scientific-red-team-reviewer` when the whole artifact needs adversarial review.

## Required Inputs

Before drafting or editing, inspect the available project artifacts:

1. `project.yaml`, `protocol.yaml`, `standards.yaml`, and `compute.yaml`.
2. `drafts/manuscript.md` or the target manuscript file.
3. `evidence/claim_map.jsonl`.
4. `drafts/references.bib`.
5. Reviewer comments, editor letter, tracked changes, or internal critique.
6. Figures, tables, supplementary files, and statistical outputs that are cited in text.

If any of these are missing, say what is missing and continue only with a
clearly labeled partial audit.

## Workflow

1. Build a reviewer/comment matrix with: comment id, reviewer, requested action,
   affected section, evidence needed, proposed response, manuscript change, and
   status.
2. Classify each issue as evidence gap, methods gap, analysis gap, wording gap,
   reference gap, formatting gap, or scope disagreement.
3. For each factual response, link to a claim id, source excerpt, statistic,
   figure/table, or mark it as unsupported.
4. Strength-calibrate every conclusion: supported, suggestive, exploratory,
   hypothesis-generating, or unsupported.
5. Check manuscript consistency across title, abstract, methods, results,
   tables, figures, discussion, limitations, and conclusion.
6. Check references against `drafts/references.bib`; use Zotero/Crossref/PubMed
   helpers when metadata integrity is uncertain.
7. Write only changes that can be defended. Do not concede a scientific point
   or promise a new analysis unless the project can actually support it.

## Artifact Destinations

Prefer these project paths:

- `reviews/reviewer_response_matrix.md`
- `drafts/response_to_reviewers.md`
- `reviews/manuscript_integrity_audit.md`
- `reviews/manuscript_integrity_audit.json`
- `evidence/claim_map.jsonl` updates only when claim support is actually added
- `drafts/references.bib` updates only when reference metadata is verified

## Gates

- Do not mark a reviewer issue resolved until the manuscript change and response
  text agree.
- Do not strengthen a claim beyond the Evidence Lock support level.
- Do not invent citations, reviewer intent, analysis results, subgroup results,
  p-values, confidence intervals, or journal rules.
- Run or request `Evidence Lock` after factual edits and `Review Trinity` before
  submission.

## Useful Pairings

- `zotero-reference-manager`, `citation-management`, `crossref-unpaywall-resolver`,
  `pubmed-database`, and `opencitations-citation-audit` for reference integrity.
- `tooluniverse-self-review` for task-specific binary acceptance criteria.
- `scientific-red-team-reviewer` for final adversarial review.
- `ptbr-article-writing` for Portuguese manuscript/rebuttal wording.
