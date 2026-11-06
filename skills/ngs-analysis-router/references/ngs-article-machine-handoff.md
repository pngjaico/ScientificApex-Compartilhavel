# NGS Article Machine Handoff

## Artifact Layout

Use this layout for project-level NGS work:

- `sources/ngs/`: source manifests and user-provided sample sheets.
- `analysis/ngs/<run_id>/run_manifest.json`: run envelope.
- `analysis/ngs/<run_id>/validation/`: input and tool preflight.
- `analysis/ngs/<run_id>/logs/`: command logs.
- `analysis/ngs/<run_id>/qc/`, `results/`, `plots/`, `visualizations/`: assay-specific outputs.
- `analysis/ngs/<run_id>/artifact_index.json`: checksums and output index.
- `analysis/ngs/<run_id>/summary.md`: human-readable run summary.

## Minimum Intake

- input type: BCL, FASTQ, BAM/CRAM, VCF, count matrix, or unknown;
- assay: WGS, WES, panel, bulk RNA-seq, sc/snRNA-seq, ATAC, ChIP/CUT&RUN/CUT&Tag, amplicon, shotgun, QC-only;
- objective: QC, counts, differential analysis, variants, peaks, annotation, taxonomic/functional profile, report-only;
- organism and reference build;
- sample metadata and design;
- runtime: local/HPC/cloud, containers, install permission, network permission.

## Caveats

- Raw sequencing data stays read-only.
- Preflight pass is not biological validation.
- Human data cloud upload requires explicit permission.
- Reference and database downloads can be huge and must be planned.
- Proprietary tools such as Cell Ranger or Illumina converters require license/EULA awareness.
