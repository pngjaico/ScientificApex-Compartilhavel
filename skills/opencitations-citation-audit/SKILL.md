---
name: opencitations-citation-audit
description: Use when open citation links, COCI DOI-to-DOI citation checks, citation graph audit, reference coverage, or independent citation-network corroboration is needed.
---

# OpenCitations Citation Audit

Use this skill when Article Machine needs an open, reproducible citation-link check that is independent of proprietary citation databases.

## Gate
- Run after DOI normalization through `crossref-unpaywall-resolver`.
- Store raw OpenCitations responses under `sources/opencitations/`.
- Record DOI input set, endpoint, retrieved_at, response hash, and missing DOI counts in the retrieval manifest.
- Use OpenCitations for citation structure; use source papers for factual claims.

## Required Uses
- Verify whether a cited DOI has open DOI-to-DOI incoming or outgoing citation links.
- Compare citation-neighborhood coverage across OpenAlex, Semantic Scholar, Crossref references, and OpenCitations.
- Audit whether a review's seed set is isolated or connected to known citation clusters.

## Caveats
- Coverage is limited to indexed open citation data and DOI-bearing records.
- Missing links do not prove absence of citation.
- Citation count is not evidence quality.

## Red Flags
- Using citation links as direct support for a biomedical mechanism.
- Ignoring non-DOI records in older or regional literature.
- Claiming comprehensiveness from OpenCitations alone.
