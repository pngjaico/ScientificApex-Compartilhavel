---
name: openalex-literature-graph
description: Use when literature discovery needs OpenAlex works, authors, institutions, citation graph, concept/topic mapping, bibliometrics, author disambiguation, venue analysis, or open scholarly metadata.
---

# OpenAlex Literature Graph

Use this skill for broad literature mapping and citation-network context before deep full-text review.

## Workflow
1. Translate the question into OpenAlex query terms, filters, and date bounds.
2. Retrieve works with DOI, title, year, venue, authorships, institutions, cited-by counts, concepts/topics, and open-access links.
3. Build clusters by topic, author group, venue, year, or citation neighborhood.
4. Identify seed papers, recent papers, review papers, and likely missing terminology.
5. Save raw metadata and summary tables under `sources/openalex/` or `evidence/literature_graph/`.

## Gates
- Treat OpenAlex metadata as discovery metadata, not final extracted evidence.
- Verify bibliographic details against DOI/publisher/PubMed before final citation.
- Record filters so searches are reproducible.
