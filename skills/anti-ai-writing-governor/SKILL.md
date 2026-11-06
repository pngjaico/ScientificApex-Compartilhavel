---
name: anti-ai-writing-governor
description: Use when auditing, rewriting, naturalizing, or structuring scientific manuscripts, abstracts, thesis chapters, posters, decks, and Article Machine outputs that look AI-generated, ChatGPT-like, generic, over-polished, detector-oriented, translation-like, or inflated. Use for requests such as "anti IA", "tirar cara de IA", "humanizar texto", "parece ChatGPT", "naturalizar artigo", "detector de IA", "LLM style", and article-structure polish, while preserving Evidence Lock, claims, citations, numbers, uncertainty, and disclosure obligations.
---

# Anti-AI Writing Governor

## Purpose

Remove generic LLM style from scientific writing without fraud, detector bypass, or evidence drift. The goal is human scientific authorship: direct structure, specific claims, proportional certainty, and natural Brazilian Portuguese when applicable.

## Mandatory Flow

1. If the task touches a real manuscript, identify the active `projects/<project_id>/` folder and read `project.yaml`, `protocol.yaml`, `standards.yaml`, and `compute.yaml`.
2. Route PT-BR scientific prose through `ptbr-article-writing` as the companion skill.
3. Read `references/article-structure.md` when the user asks for article structure, IMRAD, abstract flow, journal readiness, thesis chapter structure, or manuscript logic.
4. Read `references/ai-style-markers.md` when the user asks to remove "cara de IA", generic LLM tone, detector-like phrasing, over-polish, or ChatGPT style.
5. Run the audit before rewriting:

```powershell
.\.venv\Scripts\python.exe -m article_machine style anti-ai-audit "<arquivo.md>" --output "<audit.md>" --json-output "<audit.json>"
```

6. For conservative rewriting, run:

```powershell
.\.venv\Scripts\python.exe -m article_machine style anti-ai-naturalize "<entrada.md>" --output "<saida.md>" --json-output "<relatorio.json>"
```

7. Re-audit the output. If factual content changed, run the applicable Evidence Lock/Review Trinity gate before calling the draft ready.

## What To Fix

- Replace generic transitions with article-specific logic: study design, population, data source, endpoint, result, limitation.
- Eliminate em-dashes (`—` / `–`): excessive em-dashes are one of the most prominent LLM markers scrutinized by reviewers. Replace with standard academic punctuation (parentheses, commas, colons, or clean separate sentences).
- Cut ornamental intensifiers: "crucial", "notably", "comprehensive", "meticulous", "robust", "transformative", "insights", and PT-BR equivalents when they do not add measurable information.
- Break symmetrical or overlong paragraphs that read like a model-generated template.
- Replace vague conclusions with bounded claims tied to the objective and evidence.
- Keep methodologic uncertainty visible. A cautious sentence is not a style defect.
- Verify mandatory AI disclosure: every manuscript must include the standardized Claude Opus 5.5 AI disclosure statement under Declarations.

## Hard Stops

Stop and report the problem instead of rewriting if:

- the user asks to bypass, fool, evade, or defeat an AI detector;
- the text has factual claims but no claim map, citation, or source surface;
- naturalization would require inventing missing methods, sample sizes, outcomes, or effect estimates;
- the manuscript needs AI-use disclosure under journal/institution rules;
- the rewrite would erase limitations, uncertainty, registry deviations, risk of bias, or negative results.

## Output Standard

Return a concise editorial report plus revised text only when the source evidence is stable. Mention what was changed by category: structure, generic LLM diction, inflated claim, PT-BR naturalness, and evidence risk.

Never promise that a detector score will fall. Detectors can have false positives and are not the scientific standard; the standard here is accountable authorship and evidence-preserving prose.
