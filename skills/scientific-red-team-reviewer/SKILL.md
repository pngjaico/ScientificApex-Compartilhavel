---
name: scientific-red-team-reviewer
description: Use when stress-testing a scientific claim, manuscript, protocol, analysis, discovery result, slide deck, poster, grant, or thesis for hallucination, weak evidence, causal overreach, missing controls, statistical flaws, or reproducibility failures.
---

# Scientific Red Team Reviewer

Use this skill before submission, presentation, or any strong scientific claim.

## Workflow
1. List the strongest claims and decisions in the artifact.
2. Attack each claim from evidence, methods, statistics, causal inference, external validity, novelty, and reproducibility angles.
3. Identify what would make the claim false or misleading.
4. Check whether claims have `claim_id`, source evidence, references, and appropriate validation labels.
5. Produce a prioritized issue list with required fixes and optional improvements.

## Review Lenses
- Evidence lock and citation integrity
- Bias/guideline compliance
- Statistical validity and uncertainty
- Reproducibility and environment capture
- Overclaim and clinical-safety risk
- Visual or dissemination distortion

## Gate
If a claim cannot survive red-team review, downgrade or remove it before export or submission.
