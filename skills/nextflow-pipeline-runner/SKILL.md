---
name: nextflow-pipeline-runner
description: Use when a scientific analysis should run as a scalable, portable, containerized, HPC/cloud-ready, nf-core-compatible, or production-grade Nextflow pipeline with trace, timeline, report, DAG, and reproducible parameters.
---

# Nextflow Pipeline Runner

Use this skill when a project needs production pipeline discipline beyond ad hoc scripts.

## Workflow
1. Check whether `nextflow` is installed; if absent, stop with setup instructions.
2. Prefer existing nf-core or vetted pipelines when they fit the task.
3. Keep parameters in project `compute.yaml` or a dedicated `nextflow.config`.
4. Run with traceability flags when supported: trace, timeline, report, and DAG.
5. Store outputs under `analysis/nextflow/` and logs under `.machine/runs/<run_id>/`.
6. Register outputs in the Article Machine manifest and RO-Crate provenance when available.

## Use Nextflow When
- many samples, HPC/cloud, containers, large omics, production genomics, or repeated reruns are expected.

## Gates
- Do not run unpinned remote pipelines for regulated or thesis-critical outputs.
- Do not mix manual intermediate edits into a Nextflow output without recording them as separate steps.
