---
name: viability-audit
description: Scientific project viability and saturation analysis. Acts as a "Red Team" to challenge project ideas, identify literature gaps, and assess in silico feasibility before execution.
allowed-tools: Read Write Edit Bash
license: MIT License
metadata:
    skill-author: Antigravity / K-Dense Custom
---

# Viability Audit (The Oracle)

## Overview
This skill is designed to be the final gatekeeper before starting a new scientific project. It performs a deep analysis of an idea's novelty, feasibility, and potential for high-impact publication.

## When to Use This Skill
- Before starting a new NMA or *in silico* model.
- When you have a "vague" idea and want to test its resistance against the current state of the art.
- To identify if a field is "saturated" with recent reviews or similar studies.

## Workflow
### 1. Market/Literature Pulse
First, run a broad search using `scopus-search` or `research-lookup` to gather context.

### 2. Run the Oracle
```bash
python scripts/project_oracle.py --idea "Sua ideia aqui" --research_file sources/scopus_results.md
```

### 3. Decision Matrix
The Oracle will provide:
- **Novidade:** Análise de sobreposição com trabalhos existentes.
- **Saturação:** Grau de "overcrowding" do tópico.
- **Veredito:** GO, NO-GO ou PIVOT (sugestão de mudança de rumo).

---
> **Tip:** Be as specific as possible with the `--idea` string. Include your planned methodology to get a better "Red Team" critique.
