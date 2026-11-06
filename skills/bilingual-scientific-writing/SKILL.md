---
name: bilingual-scientific-writing
description: Use when drafting, reviewing or translating scientific manuscripts in English or português brasileiro, writing abstracts, bilingual terminology glossaries, or checking semantic fidelity between languages.
---

# Bilingual scientific writing

Declare the target language (`en` or `pt-BR`) and journal/style before writing.
Write natively in that language. In PT-BR use the local ptbr-article-writing skill;
in English use the curated scientific-writing and venue-templates instructions.
Never assume translating prose validates the science.

## English Scientific Writing Rules (Anti-LLM & Journal-Ready)

1. **Avoid Em-Dashes (`—` / `–`):** Do not use conversational em-dashes in academic English. Excessive em-dash density is one of the most conspicuous hallmarks of LLM-generated prose scrutinized by editors and reviewers. Replace em-dashes with standard academic punctuation: parentheses, commas, colons, or split into two clean declarative sentences.
2. **Eliminate Ornamental LLM Filler:** Strictly eliminate conversational transitions ("Furthermore", "Moreover", "Notably" used redundantly) and unquantified puffery ("pivotal", "transformative", "crucial", "delve into", "valuable insights", "testament").
3. **Always Route Through Writing Skills:** Always use `bilingual-scientific-writing`, `ptbr-article-writing`, and `anti-ai-writing-governor` during manuscript preparation.

## Mandatory AI Disclosure Statement

Every scientific manuscript prepared in the Article Machine must include the canonical AI disclosure section under Declarations:

### English Manuscript Version:
```markdown
### Use of Artificial Intelligence and AI-Assisted Technologies in Scientific Writing
During the preparation of this work, the authors used Claude Opus 5.5 (Anthropic) to assist with English language polishing, grammatical refinement, typographical corrections, and table layout formatting. Following the use of this tool, the authors critically reviewed, verified, and edited all generated content and take full responsibility for the scientific integrity, factual accuracy, and conclusions presented in this manuscript. In accordance with [insert target journal name] authorship criteria, generative AI technologies are not listed as authors.
```

### Portuguese Manuscript Version (pt-BR):
```markdown
### Uso de Inteligência Artificial e Tecnologias Assistidas por IA na Redação Científica
Durante a preparação deste trabalho, os autores utilizaram Claude Opus 5.5 (Anthropic) para auxiliar no polimento do idioma inglês, refinamento gramatical, correções tipográficas e formatação do layout de tabelas. Após o uso desta ferramenta, os autores revisaram criticamente, verificaram e editaram todo o conteúdo gerado e assumem total responsabilidade pela integridade científica, precisão factual e conclusões apresentadas neste manuscrito. Em conformidade com os critérios de autoria da [inserir nome da revista-alvo], tecnologias de IA generativa não são listadas como autores.
```

## Bilingual Glossary and Invariance Rules

Build a glossary at `context/terminology_glossary.json`: concept ID, English term,
PT-BR term, abbreviation, definition and source. Keep study IDs, claim IDs, DOI,
reference keys, endpoints, comparator direction and numeric values unchanged.
Preserve decimal meaning: 0.05 in English may render 0,05 in PT-BR; never alter
effect size, CI bounds, p values, n, units or inequality direction.

Audit claim strength across versions: association is not causation, exploratory
is not confirmatory, non-significance is not equivalence, and model performance
is not clinical benefit. Retain limitations, uncertainty and AI disclosure.

Use `article-machine workflow audit-language <project> --language en|pt-BR`
for deterministic marker/citation/numeric preservation against an explicit
`--reference` draft. The audit is a lexical regression aid; an independent
scientific reader must still verify semantic fidelity and natural style.

Drafts and bilingual audits stay under drafts/ and reviews/. Each final language
version requires Evidence Lock and editorial/methodological review before use.
