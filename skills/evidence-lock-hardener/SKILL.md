---
name: evidence-lock-hardener
description: Use when validating claims, citations, excerpts, DOI/PMID strings, factual manuscript sentences, bibliography synchronization, or anti-hallucination gates before draft, review, routing, or submission.
---

# Evidence Lock Hardener

Use this skill before calling any manuscript or report ready.

## Gate
- Run `article-machine draft <project_dir>`.
- Block if factual text lacks `{{claim:...}}`.
- Block if a claim is missing from `evidence/claim_map.jsonl`.
- Block if the source path does not exist.
- Block if the excerpt is not found in the source.
- Block if `reference_key` is absent from `drafts/references.bib`.
- Block invalid DOI/PMID strings when declared.
- Block unsupported or duplicate claims.

## Confidence Language
Do not allow "perfect", "world-best", "production-grade", "perfeito", or equivalent language without a passing benchmark report from `agent-benchmark-harness`.
