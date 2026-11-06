---
name: conference-requirements-importer
description: Use when congress rules, submission pages, PDFs, screenshots, or pasted instructions must be normalized before generating scientific deliverables.
---

# Conference Requirements Importer

Normalize ad hoc congress requirements into `conference.yaml`.

## When To Use
- The user gives a congress URL, PDF, screenshot, markdown, or pasted edital text.
- Slide count, duration, orientation, dimensions, abstract limits, logos, or submission rules matter.

## Contract
- Preserve the original source in `conference.yaml.source`.
- Extract kind, profile, limits, dimensions, logos, and portal URL.
- Use Playwright crawling only when useful and available; otherwise keep the URL as provenance and ask for pasted/PDF rules if needed.
- Do not guess strict limits when the source is ambiguous. Mark missing rules as pending.

## CLI
```bash
article-machine congress import <project_dir> --source "<url|text|path>" --kind deck --slug <slug>
article-machine congress import <project_dir> --source "<url>" --kind poster --crawl
```
