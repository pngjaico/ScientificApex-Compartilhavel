---
name: scientific-novelty-checker
description: Use when evaluating whether a hypothesis, drug target, mechanism, biomarker, model, thesis aim, or manuscript claim is novel, already known, incremental, contradicted, or unsupported in the literature.
---

# Scientific Novelty Checker

Use this skill before committing to a research direction, grant aim, discovery report, or strong novelty claim.

## Workflow
1. Normalize the claim into searchable concepts: entities, disease, mechanism, model system, intervention, outcome, and synonyms.
2. Search at least three evidence surfaces when available: literature metadata, full text/preprints, and structured databases.
3. Separate novelty dimensions: new entity, new mechanism, new context, new method, new combination, or new validation.
4. Classify the result as `known`, `incremental`, `plausibly novel`, `contradicted`, or `insufficient-search`.
5. Record exact sources and negative-search boundaries.

## Recommended Sources
- OpenAlex, PubMed/Europe PMC, Crossref, Semantic Scholar, bioRxiv/medRxiv.
- Open Targets, ChEMBL, BindingDB, AlphaFold/PDB, GWAS Catalog, ClinVar when biomedical.

## Output Contract
- `claim_or_hypothesis`
- `search_queries`
- `matched_prior_art`
- `novelty_class`
- `confidence`
- `what_would_disprove_novelty`

## Gate
Never write "first", "novel", "unprecedented", or "world-first" unless the novelty class and search boundary are explicit.
