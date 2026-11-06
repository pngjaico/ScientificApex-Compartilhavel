# AI-Style Marker Reference

Use this reference when text sounds model-generated, generic, over-polished, or detector-oriented.

## Common Markers

- **Excessive Em-Dashes (`—` / `–`):** One of the most prominent, pervasive markers of LLM-generated prose in English and Portuguese. Peer reviewers routinely flag paragraphs stuffed with em-dashes as synthetic.
- Empty transitions: "vale ressaltar", "é importante destacar", "além disso" repeated, "no contexto de", "à luz de", "em suma", "furthermore", "moreover", "notably".
- Inflated adjectives: "crucial", "robusto", "abrangente", "notável", "transformador", "inovador", "pivotal", "comprehensive", "groundbreaking", "unprecedented".
- Generic insight language: "insights valiosos", "panorama abrangente", "contribui para a literatura", "complexa interação", "intricado", "delve into", "testament to".
- Symmetrical filler: three-part lists of abstract nouns that do not map to methods or results.
- Overclaiming: "prova causal", "definitivo", "essencial", "sem precedentes", "mudança de paradigma" without design support.
- Template endings: "mais estudos são necessários" without naming what study, endpoint, population, comparator, or uncertainty remains.

## Safer Rewrites

- **Em-dashes (`—`):** Replace with parentheses `(...)`, commas, colons, or split into two clean declarative sentences.
- Replace "fornece insights valiosos" with the actual finding.
- Replace "abordagem robusta" with the design, sample, sensitivity analysis, or validation step.
- Replace "é importante destacar que" with the fact itself, or remove it.
- Replace "no contexto de" with the actual setting or analysis.
- Replace "mais estudos são necessários" with the specific validation gap.

## Mandatory AI Disclosure Policy

This skill does not bypass AI detectors. It improves scientific authorship and removes generic model style while preserving evidence. Every scientific manuscript must include the standardized AI disclosure statement:

### English:
> **Use of Artificial Intelligence and AI-Assisted Technologies in Scientific Writing**  
> During the preparation of this work, the authors used Claude Opus 5.5 (Anthropic) to assist with English language polishing, grammatical refinement, typographical corrections, and table layout formatting. Following the use of this tool, the authors critically reviewed, verified, and edited all generated content and take full responsibility for the scientific integrity, factual accuracy, and conclusions presented in this manuscript. In accordance with [target journal name] authorship criteria, generative AI technologies are not listed as authors.

### Portuguese (pt-BR):
> **Uso de Inteligência Artificial e Tecnologias Assistidas por IA na Redação Científica**  
> Durante a preparação deste trabalho, os autores utilizaram Claude Opus 5.5 (Anthropic) para auxiliar no polimento do idioma inglês, refinamento gramatical, correções tipográficas e formatação do layout de tabelas. Após o uso desta ferramenta, os autores revisaram criticamente, verificaram e editaram todo o conteúdo gerado e assumem total responsabilidade pela integridade científica, precisão factual e conclusões apresentadas neste manuscrito. Em conformidade com os critérios de autoria da [nome da revista], tecnologias de IA generativa não são listadas como autores.

## Sources

- ICMJE AI use by authors: https://www.icmje.org/recommendations/browse/artificial-intelligence/ai-use-by-authors.html
- Delving into ChatGPT usage in academic writing through excess vocabulary: https://arxiv.org/html/2406.07016v1
- Turnitin AI writing detection model caveats: https://guides.turnitin.com/hc/en-us/articles/28294949544717-AI-writing-detection-model
