---
name: author-identity-resolver
description: Use when resolving author identity, ORCID, PubMed author records, affiliations, ROR organizations, author fit, professor profiles, or collaborator-specific publication strategy.
---

# Author Identity Resolver

Use this skill before using author reputation, affiliation, or publication history as evidence.

## Gate
- Treat names as ambiguous strings until verified.
- Resolve identity with ORCID, PubMed author metadata, institutional pages, or ROR-backed affiliation evidence.
- Keep author fit at moderate weight unless identity, topic overlap, and affiliation are all documented.

## Blockers
- Inferring reputation from a name alone
- Merging two authors with similar names
- Treating institutional affiliation as proof of topical expertise
- Using unverifiable author-fit claims in journal routing
