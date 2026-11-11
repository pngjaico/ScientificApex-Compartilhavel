---
name: systematic-screening
description: Triple-agent systematic screening protocol (Trinity). Mimics Rayyan with two independent blinded reviewers and an adjudicator for inclusion/exclusion decisions.
allowed-tools: Read Write Edit Bash
license: MIT License
metadata:
    skill-author: Antigravity / K-Dense Custom
---

# Systematic Screening (Trinity Protocol)

## Overview
This skill implements the **Trinity Protocol**, a rigorous, multi-agent approach to screening scientific literature. It uses three specialized LLM personas to evaluate studies based on predefined inclusion/exclusion criteria.

## The Trinity Personas
1.  **Reviewer A (The Methodologist):** Focuses on study design, sample size, and statistical rigor.
2.  **Reviewer B (The Clinician):** Focuses on clinical relevance, population (PICO), and outcomes.
3.  **The Adjudicator (The Judge):** Resolves conflicts between A and B using the Master Criteria.

## Workflow
### 1. Define Criteria
Use `scientific-critical-thinking` to generate a `criteria.md` file.

### 2. Run Screening
```bash
python scripts/trinity_screening.py --input sources/search_results.json --criteria criteria.md -o sources/screening_results.json
```

### 3. Generate PRISMA Flow
Use `scientific-visualization` or `markdown-mermaid-writing` to visualize the results (Identified -> Screened -> Included).

## Integration
This skill is part of **Layer 2 [CONTEXT MANAGER]**. It destilles thousands of search results into a clean set of included studies for Layer 3 [MODELING].

---
> **Note:** For maximum cost efficiency, Reviewers A and B use `gemini-3-flash-lite`, while the Adjudicator uses `gemini-3-flash` for high-stakes decisions.
