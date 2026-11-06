---
name: hypothesis-tournament
description: Use when a scientific project needs hypothesis generation, comparison, debate, ranking, or evolution before protocol, computational discovery, experiment design, drug repurposing, target prioritization, or manuscript claims.
---

# Hypothesis Tournament

Use this skill to turn loose ideas into ranked, testable hypotheses without overclaiming.

## Workflow
1. Define the research objective, population/system, intervention or perturbation, comparator/control, outcome, and constraints.
2. Generate 5-12 candidate hypotheses from independent angles: mechanism, clinical, omics, structure, chemistry, epidemiology, and counter-hypothesis.
3. Score each hypothesis on novelty, plausibility, testability, evidence support, feasibility, risk, and potential impact.
4. Run adversarial critique: ask what observation would falsify it, what confounders explain it, and what data source can validate it.
5. Evolve the top candidates by narrowing scope and adding measurable endpoints.
6. Save the ranked output as a project artifact before analysis or drafting.

## Output Contract
- `hypothesis_id`
- `statement`
- `mechanism`
- `minimum_evidence_needed`
- `validation_plan`
- `scores`
- `known_limitations`
- `status: hypothesis-generating`

## Gates
- Do not promote a hypothesis into `evidence/claim_map.jsonl` without source evidence.
- Do not call a computational result clinically validated without external validation.
- If novelty cannot be checked, label it `novelty-unverified`.
