---
name: in-silico-validation-governor
description: Use when computational discovery, docking, virtual screening, digital twins, simulations, ML predictions, omics models, drug repurposing, or mechanistic models need validation labels, benchmark design, limitations, leakage checks, or overclaim prevention.
---

# In Silico Validation Governor

Use this skill to keep computational results useful without overstating them.

## Validation Labels
- `exploratory`
- `hypothesis-generating`
- `validated-in-silico`
- `externally-computationally-validated`
- `experimentally-validated`
- `clinically-supported`

## Workflow
1. Identify the claim being made and the model/pipeline that produced it.
2. Check data leakage, train/test split, benchmark relevance, negative controls, baseline comparison, uncertainty, and sensitivity analysis.
3. Assign the strictest defensible validation label.
4. Write limitations in the report, slide, poster, and manuscript.
5. Block any stronger label until the required evidence exists.

## Gates
- Docking score alone is never clinical evidence.
- ML accuracy without external validation is not translational proof.
- Digital twin simulations require parameter provenance and sensitivity analysis.
