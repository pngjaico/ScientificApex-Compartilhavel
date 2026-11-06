---
name: experimental-design-planner
description: Use when designing wet-lab, dry-lab, in silico, preclinical, organoid, animal, clinical, simulation, or validation experiments with controls, endpoints, sample size, randomization, blinding, and reproducibility requirements.
---

# Experimental Design Planner

Use this skill to convert a hypothesis into a protocol-ready design.

## Workflow
1. State the primary hypothesis and endpoint.
2. Define system, inclusion/exclusion criteria, intervention/perturbation, controls, replicates, time points, and stopping criteria.
3. Identify bias controls: randomization, blinding, batch effects, leakage, confounding, and missing data.
4. Specify statistical analysis, effect size assumptions, sensitivity analyses, and uncertainty reporting.
5. Define preregistration/protocol artifacts and required standards: ARRIVE, CONSORT, STROBE, TRIPOD, STARD, PRISMA, or domain-specific equivalents.
6. Produce a minimal execution plan and a failure/rollback plan.

## Output Contract
- `design_id`
- `hypothesis_id`
- `primary_endpoint`
- `controls`
- `replication_plan`
- `analysis_plan`
- `bias_controls`
- `reproducibility_artifacts`
- `go_no_go_criteria`

## Gates
- Block if no negative/vehicle/control condition is defined.
- Block if the endpoint cannot falsify the hypothesis.
- Label exploratory designs separately from confirmatory designs.
