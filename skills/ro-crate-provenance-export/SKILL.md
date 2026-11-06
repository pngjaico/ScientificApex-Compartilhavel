---
name: ro-crate-provenance-export
description: Use when a project, analysis run, R/Python pipeline, discovery workflow, benchmark, manuscript, deck, poster, or submission pack needs FAIR provenance, RO-Crate, Workflow Run Crate, hashes, environment capture, or reproducibility packaging.
---

# RO-Crate Provenance Export

Use this skill to package a scientific run so another agent or researcher can audit and replay it.

## Workflow
1. Identify the run directory and all inputs, outputs, scripts, configs, manifests, logs, and environment files.
2. Capture software versions: Python, R, packages, system tools, containers, workflow engine, and model versions.
3. Compute file hashes and byte sizes.
4. Describe provenance as prospective workflow plus retrospective execution.
5. Write an RO-Crate-like manifest, preferably under `.machine/runs/<run_id>/ro-crate-metadata.json`.
6. Include limitations and non-replayable dependencies.

## Minimum Metadata
- project id, run id, timestamps, operator/agent, command line, working directory
- inputs, outputs, code, configs, environment, logs, random seeds
- claim ids or deliverable ids affected by the run

## Gates
- Do not mark a run reproducible if inputs are missing, URLs are unpinned, or environment versions are absent.
- For sensitive data, record metadata without leaking protected content.
