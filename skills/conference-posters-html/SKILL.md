---
name: conference-posters-html
description: Use when creating editable vertical or horizontal scientific posters from a claim-safe storyboard and congress size requirements.
---

# Conference Posters HTML

Use editable HTML as the poster source of truth.

## When To Use
- The user asks for A0, 36x48, vertical, horizontal, portrait, landscape, or congress poster output.
- The same scientific story should produce multiple poster orientations.

## Contract
- Use `poster plan`, `build`, `qa`, and `export`.
- Preserve orientation and dimensions from `conference.yaml`.
- Keep all text editable in HTML and PPTX fallback.
- Use `latex-posters` only as print-first fallback when explicitly needed.

## Required Checks
- Orientation match.
- Font minimum.
- Overflow.
- Claim provenance.
- Export artifacts recorded in `manifest.json`.
