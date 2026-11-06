---
name: semantic-scholar-citation-graph
description: Use when Semantic Scholar paper lookup, citation graph expansion, recommendations, influential citations, author-paper context, or AI2 Academic Graph cross-checking is needed.
---

# Semantic Scholar Citation Graph

Use this skill when Article Machine needs citation-neighborhood evidence that is not adequately covered by PubMed, Crossref, OpenAlex, or Europe PMC alone.

## Gate
- Run after `query-string-governor` and `database-retrieval-governor` for systematic retrieval, or after a seed paper has already been resolved by DOI/PMID.
- Store raw responses under `sources/semantic_scholar/`.
- Record endpoint, query, identifiers, selected fields, retrieved_at, record_count, and response hash in a retrieval manifest.
- Do not promote Semantic Scholar recommendations directly into `evidence/claim_map.jsonl`; first verify paper metadata and source text through DOI, publisher, PubMed, PMC, or another primary source.

## Required Uses
- Backward and forward citation expansion from seed papers.
- Recommendation checks for missed adjacent papers.
- Influential-citation triage before a narrative review or novelty claim.
- Cross-checking citation context when OpenAlex and Crossref disagree.

## Provider Rules
- Prefer the official Semantic Scholar Graph API.
- Use an API key for anything beyond light exploratory use.
- Keep fields narrow; avoid fetching full author/citation payloads when DOI/title/year/abstract fields are enough.
- Respect the current official rate limits; do not parallelize until the manifest records the allowed request budget.

## Red Flags
- Treating the recommendation endpoint as comprehensive search.
- Claiming a paper is seminal because of citation count alone.
- Using AI-generated summaries as evidence text.
- Failing to de-duplicate against PubMed/OpenAlex/Crossref records.
