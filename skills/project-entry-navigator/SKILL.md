---
name: project-entry-navigator
description: Use when an agent must select, create, resume, or orient inside an Article Machine project under projects/<project_id>/ before evidence, analysis, discovery, drafting, or deliverables.
---

# Project Entry Navigator

Use this skill whenever the next step depends on the active Article Machine project.

## Purpose
- Prevent agents from doing scientific work at the workspace root.
- Make project contracts the first source of truth.
- Route agents into the next allowed Article Machine mode before they touch claims, analysis, or drafts.

## Required Flow
1. Identify the active project under `projects/<project_id>/`.
2. If no project fits, use `.\.venv\Scripts\python.exe -m article_machine init "<name>" --type <project_type>`.
3. Read these files before doing work:
   - `project.yaml`
   - `protocol.yaml`
   - `standards.yaml`
   - `compute.yaml`
4. Run preflight when execution, R, analysis, or reproducibility matters:
   - `.\.venv\Scripts\python.exe -m article_machine preflight <project_dir>`
5. Build or refresh context before substantive work:
   - `.\.venv\Scripts\python.exe -m article_machine context build <project_dir> --mode <mode> --hypothesis "..."`
6. Confirm the next allowed mode; do not skip gates.

## Hard Rules
- Do not write manuscript claims outside `evidence/claim_map.jsonl` and `drafts/manuscript.md`.
- Do not call a draft ready without Evidence Lock.
- Do not run Review Trinity or submission steps without the required project artifacts.
- Do not copy root legacy content into a project without a source registry entry or migration note.
