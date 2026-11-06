# Workflow Router

Use this reference after the active Article Machine project is identified.

## Evidence Synthesis

Use for biomarker reviews, GLP-2 comparisons, microbiome/SBS reviews, preclinical perfusion meta-analysis, and umbrella reviews.

Outputs:
- PICO/PECO and eligibility criteria.
- Search strategy by database.
- Corpus manifest and deduplication log.
- Screening log, extraction table, risk-of-bias table.
- Synthesis plan before results.

Quality gates:
- Register systematic reviews or NMA before extraction when feasible.
- Use PRISMA/PRISMA-NMA as applicable.
- Use QUADAS-2 for diagnostic biomarkers, SYRCLE/CAMARADES for animal perfusion studies, ROB 2/ROBINS-I for clinical intervention or observational evidence.
- Do not pool human and preclinical studies.

## Registry, Policy, And Implementation

Use for SRTR/OPTN, NHSBT, DATASUS, SNT, RBT, ABTO, SUS incorporation, access, center distribution, or cost/implementation questions.

Outputs:
- Data dictionary and extraction date.
- Cohort definition and exclusion flow.
- Graft-type taxonomy.
- Descriptive analysis, survival plan, sensitivity analyses.
- Limitation table for low event counts and center effects.

Quality gates:
- State registry version, years, age group, graft type, and era.
- Treat small-n models skeptically; prefer transparent survival/descriptive models before generic ML.
- Do not compare graft types without acknowledging indication and severity confounding.

## Translational And Preclinical

Use for machine perfusion, I/R, organoids, barrier repair, perfusate biomarkers, and animal studies.

Outputs:
- Experimental design with primary endpoint.
- Control groups, randomization, blinding, exclusion criteria.
- Collection map for tissue, perfusate, serum, histology, omics.
- Validation plan and failure modes.

Quality gates:
- Use ARRIVE and SYRCLE for animal work.
- Define one primary endpoint before protocol freeze.
- Keep organoid/ex vivo findings separate from clinical claims.
- For omics, require QC, batch handling, multiple-testing correction, and independent validation plan.

## Computational Discovery

Use for drug repurposing, target selection, digital pathology, digital twin, or ML prediction.

Outputs:
- Data sources and leakage audit.
- Baseline model before complex ML.
- Cross-validation plan and external validation target.
- Interpretability and sensitivity analyses.
- In-silico validation label.

Quality gates:
- Run `in-silico-validation-governor` before conclusions.
- Do not call a target therapeutic without wet-lab or orthogonal evidence.
- For WSI, require annotation provenance and patient-level splits.
- For rare intestinal transplant registries, report calibration and uncertainty, not only AUROC.

## Congress And Journal Routing

Use only after the claim source is clear.

Outputs:
- Venue fit table.
- Rule import under the deliverables pipeline.
- Abstract or manuscript outline tied to `evidence/claim_map.jsonl`.

Quality gates:
- Import official rules with `conference-requirements-importer` when building deliverables.
- Use `conference-deliverable-router` for decks, posters, abstracts, and submission packs.
- Do not build submission-ready material from unverified strategic claims.
