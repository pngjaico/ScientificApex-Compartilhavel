---
name: life-science-router
description: Use when a biomedical, drug-discovery, omics, genetics, protein, pathway, microbiome, clinical, or public-dataset question should be routed through Life Science Research plugin skills inside Article Machine projects.
---

# Life Science Router

Use this skill to connect Article Machine projects with the `Life Science Research` plugin.

## When To Use
- The question involves targets, genes, variants, proteins, pathways, drugs, ligands, clinical trials, microbiome, metabolomics, proteomics, single-cell data, or public biomedical datasets.
- A discovery or evidence project needs structured biomedical retrieval before analysis, manuscript writing, slides, or posters.

## Contract
- Start with `article-machine life-science plan <project_dir> --question "<question>"`.
- Read `context/life_science/retrieval_plan.yaml`.
- Use only the selected downstream plugin skills unless the question clearly needs another source.
- Save raw or summarized outputs under `evidence/life_science/`.
- Promote only checked findings into `evidence/claim_map.jsonl`.

## Plugin Bridge
- The active plugin capability is `Life Science Research`.
- Resolve `plugin:life-science-research` through `.machine/plugin_bindings.json`
  before opening plugin resources. Exactly one version must be bound; zero or
  multiple candidates is a blocker, not a guess.
- For broad questions, use `<binding-root>/skills/research-router-skill/SKILL.md`.
- For narrow questions, route to the specific plugin skill selected by `article-machine life-science plan` or by entity class: gene/protein, disease, variant, compound, pathway, clinical evidence, public dataset, expression, metabolomics, proteomics, microbiome, structure, or literature.
- Do not copy all plugin skills into the workspace. This local skill is the gateway; the plugin remains the execution source.

## Evidence Rules
- Treat database outputs as hypothesis-generating until validated.
- Do not infer causality from association-only evidence.
- State cohort, ancestry, tissue, assay, and study-design limitations.
- Keep database evidence out of congress deliverables until Evidence Lock approves the claim.

## Useful Commands
```bash
article-machine life-science catalog
article-machine life-science plan projects/<project_id> --question "Find target and compound evidence for JAK signaling in IBD."
```
