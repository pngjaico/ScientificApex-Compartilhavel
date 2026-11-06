---
name: open-targets-drug-targeting
description: Use when drug discovery, target validation, disease biology, gene prioritization, indication expansion, or mechanism analysis needs Open Targets evidence, target-disease scores, genetics, drugs, pathways, tractability, safety, or target prioritization.
---

# Open Targets Drug Targeting

Use this skill to ground target hypotheses in systematic target-disease evidence.

## Workflow
1. Resolve disease/phenotype and target identifiers before querying.
2. Retrieve target-disease association evidence, datasource contributions, tractability, safety, known drugs, pathways, and genetic support.
3. Separate genetic, somatic, expression, literature, animal-model, pathway, and drug evidence.
4. Rank targets by evidence strength and actionability, not by one score alone.
5. Save outputs under `evidence/life_science/open_targets/`.

## Gates
- Do not infer clinical efficacy from target association.
- State datasource limitations and update version/date.
- Mark outputs `hypothesis-generating` until validated with independent evidence or experiments.
