---
name: snakemake-pipeline-runner
description: Use when a scientific analysis should be converted into a readable Python-friendly Snakemake workflow with rules, conda/container environments, reports, provenance, local reruns, or reproducible multi-step analysis.
---

# Snakemake Pipeline Runner

Use this skill when analysis is outgrowing notebooks or single scripts but still benefits from Python-native workflow logic.

## Workflow
1. Check whether `snakemake` is installed; if absent, stop with setup instructions.
2. Convert each deterministic step into a rule with explicit input, output, params, log, and environment.
3. Keep project parameters in `config.yaml`.
4. Use conda or containers per rule when possible.
5. Run a dry-run before execution.
6. Generate a report or provenance artifact after successful execution.

## Use Snakemake When
- the workflow is local or lab-scale, Python/R-heavy, iterative, and benefits from transparent rule dependencies.

## Gates
- Block if outputs are not declared.
- Block if a rule uses hidden state from the working directory.
- Record every manual intervention outside Snakemake as a separate provenance step.
