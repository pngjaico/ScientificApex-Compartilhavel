---
name: playwright-layout-qa
description: Use when validating HTML scientific slides or posters with browser rendering, screenshots, overflow checks, PDF export, or thumbnails.
---

# Playwright Layout QA

Use real browser rendering for layout gates.

## When To Use
- HTML slides/posters need overflow, screenshot, PDF, or thumbnail validation.
- The user asks for congress-ready visual QA.

## Preconditions
- `npx` must be available.
- If browser launch fails, install Chromium with `npx playwright install chromium`.

## Contract
- QA fails on overflow, missing HTML, wrong orientation, font minimum, unsupported claims, or asset provenance gaps.
- Store browser artifacts under the deliverable `qa/` or `exports/` folder.
- Do not perform final portal submission without explicit user confirmation.

## Python Hook
```python
from article_machine import playwright_ops
```
