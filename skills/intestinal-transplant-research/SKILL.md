---
name: intestinal-transplant-research
description: Use when planning, extracting, routing, or quality-gating research on intestinal transplantation, intestinal failure, short bowel syndrome, GLP-2 therapies, intestinal graft rejection biomarkers, machine perfusion, intestinal organoids, intestinal ischemia-reperfusion, microbiome/omics, digital pathology, or Brazilian SUS/ABTO implementation studies.
---

# Intestinal Transplant Research

## Core Rule

Use this skill as a domain router, not as a substitute for evidence validation. It helps place an intestinal-transplant or intestinal-failure task into the right Article Machine project, downstream skills, evidence gates, and publication route.

Do not promote strategic report statements, database lookups, conference pages, or opaque deep-research citations into `evidence/claim_map.jsonl` until the primary source has been retrieved, saved, and checked.

## First Pass

1. Identify the active project under `projects/<project_id>/` or create one before analysis.
2. Read `project.yaml`, `protocol.yaml`, `standards.yaml`, and `compute.yaml`.
3. Classify the request into one lane:
   - evidence synthesis: systematic review, NMA, umbrella review, scoping review.
   - registry or policy: SRTR/OPTN, NHSBT, DATASUS, SNT, RBT, ABTO, SUS implementation.
   - preclinical/translational: perfusion, I/R, organoids, biomarkers, omics, animal models.
   - computational discovery: target prioritization, drug repurposing, digital pathology, digital twin.
   - congress/journal routing: abstract, deck, poster, venue fit.
4. Route to the appropriate downstream skills before drafting conclusions.
5. Record source provenance and limitations before writing any factual claim.

## Downstream Skill Routing

- Topic selection or portfolio ranking: `topic-ideation-tournament`, then `scientific-novelty-checker`.
- Systematic review, NMA, umbrella review, screening, or risk of bias: `literature-review`, `asreview-screening-bridge`, `risk-of-bias-assistant`, `grade-sof-table-builder`.
- Registry or statistical analysis: `database-lookup`, `statsmodels`, `statistical-analysis`, `scikit-survival` when survival models are needed.
- Biomedical retrieval, omics, microbiome, pathways, targets, compounds, or public datasets: run `article-machine life-science plan <project_dir> --question "<question>"` and follow `life-science-router`.
- Experimental validation, controls, endpoints, or animal/bench protocols: `experimental-design-planner`, `experimental-design`, `statistical-power`.
- Drug repurposing and targets: `open-targets-drug-targeting`, `chembl-bindingdb-miner`, `alphafold-pdb-structure-router`, `in-silico-validation-governor`.
- Digital pathology: `histolab`, `pathml`, `scikit-learn`, `shap`, and `in-silico-validation-governor`.
- Congress or journal deliverables: `conference-deliverable-router`, `conference-requirements-importer`, `venue-templates`, `ptbr-article-writing` when Portuguese output is required.

## Evidence Locks

Apply these hard separations:

- Separate human clinical data from animal, ex vivo, organoid, and in silico evidence.
- Separate isolated intestinal transplant from liver-containing and multivisceral grafts.
- Separate intestinal failure/SBS rehabilitation from transplant outcomes unless the endpoint explicitly bridges them.
- Separate biomarker association from diagnostic accuracy; use QUADAS-2 for diagnostic biomarker claims.
- Separate GLP-2 efficacy, PN reduction, autonomy, safety, and transplant avoidance.
- Label drug discovery and digital-twin outputs as hypothesis-generating until orthogonal validation exists.
- State country, registry, era, graft type, age group, and data extraction date for registry claims.

## Reference Files

- Read `references/domain-ontology.md` when expanding search strings, synonyms, inclusion criteria, or task packets.
- Read `references/workflow-router.md` when choosing the pipeline, outputs, and quality gates.
- Read `references/strategic-portfolio.md` when ranking project ideas, congress targets, or journal routes. Treat it as strategy, not verified evidence.

## Minimal Output Contract

For any substantive task, leave at least one durable artifact in the active project:

- `context/task_packets/<task>.md` for intended work and gates, or
- `context/<topic>_extraction.yaml` for structured extraction, or
- `evidence/life_science/<artifact>.md` for retrieval outputs, or
- `analysis/<artifact>.md` for non-claim analysis.
