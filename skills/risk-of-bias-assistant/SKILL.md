---
name: risk-of-bias-assistant
description: Use when assessing study quality or risk of bias with RoB 2, ROBINS-I, QUADAS-2, PROBAST, ROBIS, AMSTAR 2, SYRCLE, TACIT, or diagnostic, randomized, observational, prediction, animal, and systematic-review bias tools.
---

# Risk Of Bias Assistant

Use this skill as semi-automation only; final risk-of-bias judgments require human review.

## Workflow
1. Identify study design and route to the correct tool.
2. Extract verbatim support passages for each domain or signalling question.
3. Propose domain-level judgment with rationale.
4. Flag missing information as `unclear` or `some concerns`; do not infer low risk from silence.
5. Produce a reviewer-ready table with evidence snippets and uncertainty.
6. Save outputs under `evidence/risk_of_bias/`.

## Tool Routing
- RCT: RoB 2
- Non-randomized intervention: ROBINS-I
- Diagnostic accuracy: QUADAS-2
- Prediction model: PROBAST
- Systematic review: ROBIS or AMSTAR 2
- Animal/preclinical: SYRCLE or ARRIVE-adjacent tools

## Gates
- Block manuscript claims if required bias assessment is missing.
- Never overwrite human judgments; preserve disagreements.
