---
name: content-preservation-guardian
description: Use when reorganizing, cleaning, staging, deleting, moving, graphing, or indexing the Doutorado workspace could affect raw scientific content, legacy folders, full text, patient/source dumps, or generated corpora.
---

# Content Preservation Guardian

Use this skill before any workspace cleanup, reorganization, staging, move, delete, bulk graph, or migration action.

## Purpose
- Protect scientific source material while making the workspace easier for agents.
- Separate navigation metadata from source content.
- Force explicit migration manifests before moving or transforming legacy/raw data.

## Required Checks
1. Run `git status --short --branch`.
2. Read `docs/WORKSPACE_REORG_PLAN.md`.
3. Read `graphify-out/GRAPH_REPORT.md`.
4. Identify whether the target is one of:
   - root legacy folders
   - raw PDFs or full text
   - patient/source dumps
   - generated graphify, cache, or venv files
   - project evidence, analysis, or drafts
5. If content could be moved or transformed, produce a migration manifest first:
   - source path
   - destination path
   - reason
   - checksum or preservation note
   - rollback path
   - user confirmation status

## Allowed Without Confirmation
- Add navigation metadata.
- Add read-only graph nodes that point to existing files.
- Add `.gitignore` protection for generated/cache/raw corpus areas.
- Add tests that verify navigation and protection rules.

## Requires Explicit User Confirmation
- Moving legacy folders.
- Deleting or deduplicating source material.
- Rewriting raw full text, patient/source dumps, PDFs, or project evidence.
- Uploading human data or large raw data to cloud tools.

## Hard Rules
- Do not stage `.env`, `.venv`, caches, graphify transient files, raw fulltexts, or patient/source dumps.
- Do not treat a graph node as proof of scientific content.
- Do not weaken Evidence Lock or Review Trinity to make reorganization look complete.
