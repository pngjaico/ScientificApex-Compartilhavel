---
name: cwl-workflow-bridge
description: Use when a scientific command-line workflow needs a vendor-neutral Common Workflow Language bridge for portability, reuse, standards compliance, workflow exchange, or execution across multiple CWL-compatible platforms.
---

# CWL Workflow Bridge

Use this skill when portability and standard workflow description matter more than convenience.

## Workflow
1. Identify command-line tools, inputs, outputs, parameters, and file formats.
2. Describe each tool as a CWL `CommandLineTool`.
3. Compose tools into a CWL `Workflow` with explicit data flow.
4. Keep example inputs and expected outputs in the project.
5. Validate with a CWL runner when available.
6. Add CWL files to provenance and replay artifacts.

## Use CWL When
- the workflow should be shared across institutions, registries, platforms, or long-term archival systems.

## Gates
- Do not claim portability if local paths, interactive prompts, or hidden environment variables are required.
- Prefer RO-Crate export for packaging CWL plus run evidence.
