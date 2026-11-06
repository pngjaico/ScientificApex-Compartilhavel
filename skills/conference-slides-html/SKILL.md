---
name: conference-slides-html
description: Use when creating HTML-first scientific slide decks with animations, speaker notes, timing, QA, and export to PDF/PPTX.
---

# Conference Slides HTML

Use HTML as the canonical slide source.

## When To Use
- The deliverable kind is `deck`.
- The user asks for 3, 5, 10, or 15 minute talks, seminars, thesis defense slides, or animated congress presentations.

## Contract
- Build from `storyboard.yaml`, not from free text.
- Use only approved `source_claim_ids`.
- Keep animations in HTML; degrade complex motion to PPTX build steps.
- Run QA before export.

## CLI
```bash
article-machine deck plan <deliverable_dir>
article-machine deck build <deliverable_dir>
article-machine deck qa <deliverable_dir>
article-machine deck export <deliverable_dir>
```
