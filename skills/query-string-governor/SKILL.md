---
name: query-string-governor
description: Use when creating, validating, compiling, or auditing database search strings, Boolean logic, field tags, exclusions, date filters, language filters, escaping, wildcards, or provider-specific query syntax.
---

# Query String Governor

Use this skill before any database search string is accepted as valid.

## Gate
- Store the source plan in `context/query_plan.yaml`.
- Run `article-machine query validate <project_dir>`.
- Run `article-machine query compile <project_dir>`.
- Do not execute retrieval when validation reports broken parentheses, ambiguous raw booleans inside terms, dangerous wildcards, unknown providers, incompatible fields, or missing concepts.

## Required Contract
- `contract: QueryPlan`
- `topic`
- `providers`
- `concepts` with `id`, `terms` or `synonyms`, and `field`
- optional `date_range`, `languages`, `exclusions`, `limits`, `rationale`

## Red Flags
- Terms containing raw `AND`, `OR`, or `NOT`
- Wildcards before three leading characters
- DOI, PMID, ORCID, author, or affiliation fields sent to providers that do not support them
- A query copied from a manuscript without a structured plan
