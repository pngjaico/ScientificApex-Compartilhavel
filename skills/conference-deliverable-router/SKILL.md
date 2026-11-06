---
name: conference-deliverable-router
description: Use when a research project must become a congress deliverable such as an oral deck, poster, abstract, handout, or submission pack.
---

# Conference Deliverable Router

Route dissemination work without weakening the research gates.

## When To Use
- The user asks for slides, poster, abstract, congress material, seminar, oral presentation, defense, or submission pack.
- A project already has `project.yaml` and must produce files under `projects/<project>/deliverables/<slug>/`.

## Contract
- Keep research in the project root and dissemination in `deliverables/<slug>/`.
- Start with `article-machine congress import <project_dir> --source "<rules>" --kind <deck|poster> --slug <slug>`.
- Then run `deck|poster plan`, `build`, `qa`, and `export`.
- Never put unsupported findings into `storyboard.yaml`.

## Outputs
- `conference.yaml`
- `storyboard.yaml`
- `theme.yaml`
- `qa_report.json`
- `manifest.json`
