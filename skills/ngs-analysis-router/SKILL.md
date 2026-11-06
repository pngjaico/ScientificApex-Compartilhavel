---
name: ngs-analysis-router
description: Use when Article Machine projects need Life Sciences NGS Analysis plugin routing for sequencing data including BCL run folders, FASTQ, BAM/CRAM, VCF, count matrices, scRNA-seq, bulk RNA-seq, ATAC-seq, ChIP-seq, CUT&RUN/CUT&Tag, WGS/WES/panel variant calling, microbiome amplicon, shotgun metagenomics, demultiplexing, QC, trimming, alignment, differential expression, peak calling, UMAP/annotation, or NGS runtime preflight.
---

# NGS Analysis Router

## Purpose

Route sequencing work into the `Life Sciences NGS Analysis` plugin while keeping raw data read-only, preflight-first, and Article Machine provenance-safe.

## Mandatory Flow

1. Identify the active `projects/<project_id>/` before analysis or claim generation.
2. Inspect available inputs before asking questions: run folders, FASTQ, BAM/CRAM, VCF, count matrices, sample sheets, reference files, BED/GTF/FASTA, and metadata.
3. Resolve `plugin:ngs-analysis` through `.machine/plugin_bindings.json`.
   Exactly one binding is required; missing or multiple versions block work.
   Read `<binding-root>/skills/ngs-analysis-router/SKILL.md`.
4. For pipeline details, use the plugin-root references:
   - `<binding-root>/references/intake-schema.json`
   - `<binding-root>/references/pipeline-registry.json`
   - `<binding-root>/references/run-envelope-schema.json`
5. Resolve the minimal missing setup fields: input type, assay, objective, organism/reference, paired-end status, design metadata, runtime/container constraints, and cloud-upload permission for human data.
6. Prefer preflight and install-plan artifacts before execution. Do not install tools or download large references unless the user explicitly asks.
7. Store Article Machine outputs under `analysis/ngs/<run_id>/` with manifests, logs, summaries, and checksums. Promote biological findings into `evidence/claim_map.jsonl` only after validation.

## Routing Families

- BCL/demultiplexing: `ngs-bcl-to-fastq`
- FASTQ QC/trimming: `ngs-fastq-qc`
- DNA variants: `ngs-dna-variant-calling`, `ngs-dna-germline-variants`, `ngs-dna-somatic-variants`, `ngs-dna-umi-panel-variants`
- Bulk RNA-seq: `ngs-bulk-rnaseq`, `ngs-bulk-rnaseq-counts-qc`, `ngs-bulk-rnaseq-differential-expression`
- Single-cell: `ngs-scrna-seq`, `scrna-seq-qc`
- Epigenomics: `ngs-epigenomics-peaks`, `ngs-atacseq-peaks-qc`, `ngs-chip-cutrun-peaks-qc`
- Microbiome: `ngs-amplicon-microbiome`, `ngs-shotgun-metagenomics`
- Runtime setup: `ngs-runtime-env`

## Stop Conditions

- Human data would leave the machine without explicit cloud-upload permission.
- Required sample metadata, reference genome, or assay design is missing.
- The requested pipeline requires proprietary/EULA tools and the user has not approved them.
- Preflight says required tools or references are absent and no install/download approval exists.
- The user asks to treat unvalidated exploratory NGS output as final evidence.

## Reference

Read `references/ngs-article-machine-handoff.md` for artifact layout and caveats.
