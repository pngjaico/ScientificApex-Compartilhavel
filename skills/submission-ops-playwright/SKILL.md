---
name: submission-ops-playwright
description: Use when preparing or dry-running congress portal submission with browser automation and explicit final confirmation requirements.
---

# Submission Ops Playwright

Automate submission only behind hard safety gates.

## When To Use
- The user asks to test, dry-run, or perform congress portal submission.
- A deliverable has passed QA and exports exist.

## Contract
- `dry-run` may inspect readiness and portal state but must not submit.
- `run` requires explicit user confirmation and a fresh Playwright snapshot before clicking final submit.
- Never reuse stale element references.
- Record dry-run and run artifacts in `submission/`.

## CLI
```bash
article-machine submit dry-run <deliverable_dir>
article-machine submit run <deliverable_dir> --confirm
```
