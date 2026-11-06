---
name: academic-office-deliverables
description: Use when scientific work must become editable DOCX, PPTX, LaTeX, PDF, thesis-defense slides, group-meeting slides, paper-reading reports, template-matched Office files, Zotero-backed document packages, or local-first academic writing workspaces with layout QA.
---

# Academic Office Deliverables

Use this skill when the main output is an editable academic document or
presentation, not just prose. It bridges Article Machine evidence discipline with
practical DOCX/PPTX/LaTeX deliverables.

## Scope

Use for:

- Paper-reading reports, thesis chapters, response packages, and submission
  support documents in DOCX or LaTeX.
- Defense, qualification, group meeting, lab meeting, and course-report slides.
- Template-matched PPTX/DOCX work where style preservation matters.
- Local-first academic writing workspaces that combine LaTeX, Python figures,
  Zotero references, Git/history, and repeatable exports.

For congress decks, posters, abstracts, or submission packs, use
`conference-deliverable-router` first. HTML remains canonical for the Article
Machine congress pipeline; PPTX is an export/fallback unless the task is
explicitly Office-native.

## Operating Rules

1. Work inside the active `projects/<project_id>/` whenever the deliverable
   contains scientific claims.
2. Read project contract files and the relevant claim map before generating
   scientific text.
3. Never overwrite the user's original DOCX, PPTX, PDF, LaTeX, or template.
   Write versioned output under `deliverables/`, `exports/`, or `drafts/`.
4. Keep source labels visible for claims, parameters, figures, datasets, tables,
   and equations until the user asks for a final clean export.
5. Preserve formulas, variable names, statistical units, figure numbers,
   reference keys, and software commands exactly unless a verified correction is
   needed.

## Workflow

1. Identify the deliverable type, audience, duration/page budget, required
   template, language, and export format.
2. Build an evidence-backed outline before making Office or LaTeX files.
3. Route references through `zotero-reference-manager` or `drafts/references.bib`
   when citations are required.
4. Use local parsing/conversion tools such as `liteparse`, `pdf`, `docx`,
   `pptx`, `xlsx`, `pptx-export-bridge`, or Playwright QA when applicable.
5. For slides, use action titles, one main claim per slide, and figures/tables
   as evidence rather than decoration.
6. For documents, use structured headings, tables only where useful, source
   labels, and a references section that resolves to verified metadata.
7. Validate layout before calling the deliverable usable.

## QA Checklist

Check what is feasible for the file type:

- Text overflow, stale placeholders, broken images, distorted aspect ratios.
- Missing source labels, unsupported claims, mismatched numbers, and table/figure
  contradictions.
- Garbled characters, font fallback, missing equations, broken citations, and
  unresolved reference keys.
- Export readability: PDF screenshots, slide thumbnails, extracted text, or
  package XML inspection.

## ClaudePrism Boundary

ClaudePrism is useful as a usability reference: local-first storage, offline
LaTeX compilation, project Python environments, Git history, Zotero integration,
and skill installation UX. In its public repository it is an application, not a
drop-in Article Machine skill catalog. Do not treat it as installed capability
unless its runtime is actually installed and tested on this machine.

## Artifact Destinations

- `deliverables/<slug>/` for structured packages.
- `exports/` for rendered DOCX/PPTX/PDF outputs.
- `reviews/layout_qa.md` or `reviews/layout_qa.json` for QA evidence.
- `context/task_packets/` for non-trivial deliverable setup decisions.
