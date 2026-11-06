---
name: pptx-export-bridge
description: Use when converting HTML-first decks or posters into editable PowerPoint fallbacks while preserving text editability and provenance.
---

# PPTX Export Bridge

Create editable fallback PowerPoint files without making PPTX the source of truth.

## When To Use
- The congress requires `.pptx`.
- The user wants editable poster or slide files.

## Contract
- HTML remains canonical.
- Text should become editable text boxes where possible.
- Complex HTML animation degrades to build-step or static slides.
- Generated PPTX must be recorded in `manifest.json`.

## Python Hook
```python
from article_machine.pptx_bridge import export_editable_pptx
```
