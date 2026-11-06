---
name: skill-upgrade-governor
description: Use when researching, selecting, installing, auditing, or routing new Article Machine skills, external skill repositories, APIs, or agent capability upgrades.
---

# Skill Upgrade Governor

Use this skill before changing the Article Machine skill layer.

## Gate
- Start inside an active project when the work changes scientific capability, routing, evidence retrieval, analysis, or manuscript production.
- Search current installed skills before adding new ones.
- Prefer skills with executable wrappers, official APIs, explicit provenance rules, or strong methodological safeguards.
- Do not install giant overlapping catalogs blindly; add broad external catalogs only through curated gateway skills unless every installed skill has a clear routing purpose.
- After installation, update `article_machine/agent_skills.py`, `SKILL_INDEX.md`, `SKILLS_CANON.md`, and tests.
- Run `article-machine skills audit` and relevant route smoke tests.

## Selection Criteria
- Must improve evidence integrity, retrieval coverage, reproducibility, analysis correctness, clinical/scientific safety, or review quality.
- Must state provider limitations and avoid presenting database output as final proof.
- Must have a clear project artifact destination under `sources/`, `context/`, `evidence/`, `analysis/`, or `reviews/`.
- Must be maintainable in the local workspace; fragile tools go behind caveats, not core gates.

## Red Flags
- Adding a skill only because it sounds impressive.
- Duplicating K-Dense coverage without a stronger wrapper or different evidence source.
- Adding clinical or biomedical tools without rate-limit, license, or source-provenance rules.
- Claiming the machine is stronger without a benchmark or route/audit smoke test.
