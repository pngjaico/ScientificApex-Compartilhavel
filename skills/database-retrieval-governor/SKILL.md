---
name: database-retrieval-governor
description: Use when planning or auditing PubMed, Europe PMC, OpenAlex, Crossref, ORCID, ROR, retraction metadata, or any database retrieval that needs cache, rate limits, query hashes, manifests, and offline replay.
---

# Database Retrieval Governor

Use this skill before retrieval touches a remote API.

## Gate
- Build the offline contract with `article-machine retrieval plan <project_dir>`.
- Audit manifests with `article-machine retrieval audit <project_dir>`.
- Keep tests offline; future online commands must add cache, throttling, `mailto` or tool identification when required, and replay files.

## Manifest Minimum
- `provider`
- `query_hash`
- `retrieved_at`
- `record_count`
- `records_sha256`

## Provider Rules
- PubMed/NCBI follows the E-utilities API-key rate contract.
- Crossref retrieval must identify the tool/contact route and back off on server limits.
- OpenAlex live use must account for its current API key and credit model.
- ORCID/ROR evidence resolves identity or institution; it does not prove scientific merit by itself.
