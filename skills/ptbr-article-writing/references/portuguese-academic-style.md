# Portuguese Academic Style Calibration

Use this reference to calibrate scientific writing in Brazilian Portuguese. It is not a grammar textbook; it is a safety and naturalness checklist for Article Machine outputs.

## Source Lessons

- Revista de Saúde Pública instructions: original articles need clear objectives/hypotheses, design, methods, results, discussion and conclusions; structured abstracts use Objective, Methods, Results and Conclusion. Source: https://rsp.fsp.usp.br/pt-br/instrucoes-aos-autores/
- Pan American Journal of Public Health author instructions: authors are strongly advised to write in their mother tongue; weak command of a second language can obscure meaning and precision. Original research and systematic reviews use a structured abstract with Objectives, Methods, Results and Conclusions; abbreviations should be defined and avoided when possible. Source: https://journal.paho.org/sites/default/files/2019-01/Instrucoes%20aos%20autores_PT_170701.pdf
- Cadernos de Saúde Pública abstract guidance: the abstract should contain objective, method, main results and conclusion; avoid abbreviations and empty conclusion formulas. Source: https://www.scielo.br/media/files/Leia_mais_Resumo_PORT_LINK_1.pdf
- PRISMA 2020 Brazilian Portuguese version: systematic reviews must transparently report why the review was done, what was done and what was found; PRISMA 2020 includes a 27-item checklist, abstract checklist and flow diagrams. Source: https://www.scielosp.org/article/rpsp/2022.v46/e112/pt/
- Plain-language guidance from gov.br and public communication manuals: active voice, direct order, short sentences, fewer jargon terms, fewer foreign words, and fewer verb nominalizations improve comprehension. Sources: https://www.gov.br/servidor/pt-br/assuntos/laboragov/curadoria-tematica/linguagem-simples and https://www.gov.br/servicoscompartilhados/pt-br/acesso-a-informacao/acoes-e-programas/governanca/arquivos_figuras/linguagem_simples_roedel.pdf

## Article-Like Portuguese Patterns

Prefer these patterns because they sound like Brazilian scientific prose rather than translated English:

- "O objetivo deste estudo foi avaliar..."
- "Foi realizada revisão sistemática..."
- "Foram incluídos X estudos..."
- "A busca foi conduzida em..."
- "A estimativa foi apresentada como..."
- "Os achados sugerem associação entre..."
- "A interpretação deve considerar..."
- "A principal limitação foi..."

Avoid these translated patterns:

- "Nós encontramos que..."
- "Este papel demonstra..."
- "No contexto de uma framework..."
- "A camada de análise mostrou um sinal robusto..."
- "Os resultados são promissores e transformadores..."
- "Este estudo prova que..." when the design does not prove causality.

## Section Moves

### Title

Name the design or object when relevant: revisão sistemática, meta-análise, coorte, estudo transversal, ensaio clínico, série temporal, estudo metodológico. Do not add novelty claims unless already proven.

### Abstract

Use one sentence for each function:

1. Objective: what was evaluated, compared or estimated.
2. Methods: design, population/source, period, databases, model or synthesis.
3. Results: number of studies/participants and the main quantitative results.
4. Conclusion: answer the objective with uncertainty and scope.

### Introduction

Use three moves:

1. Establish the clinical/scientific problem.
2. Name the evidence gap, not just "there is controversy".
3. End with a clear objective.

### Methods

Use past tense for what was done. Put operational details before interpretation: data source, eligibility, variables, outcomes/desfechos, risk of bias, synthesis model, software, sensitivity analyses.

### Results

Use numbers before interpretation. Report effect measure, confidence/credible interval and direction. If precision is poor, say so.

### Discussion

Start with the main answer, then compare with prior literature, explain plausible mechanisms only if supported, state limitations, and end with the practical or research implication. Do not hide a fragile estimate behind fluent prose.

### Conclusion

No generic ending. Do not use "mais estudos são necessários" alone. Say what kind of uncertainty remains and what evidence would reduce it.

## Anti-Translation Lexicon

| Avoid | Prefer |
|---|---|
| framework | estrutura metodológica, modelo de trabalho |
| endpoint | desfecho |
| outcome | desfecho |
| baseline | início do seguimento, avaliação inicial |
| layer/camada | análise, estrato, conjunto de estudos, etapa |
| signal/sinal | associação, estimativa, padrão observado, achado |
| hub | estudo dominante, nó central da rede |
| robusto | preciso, consistente, pouco sensível à análise, if actually true |
| no contexto de | na análise de, entre, para, considerando |
| em termos de | quanto a |
| à luz de | considerando |

## Rewrite Examples

Bad:
"No contexto do framework, o endpoint apresentou um sinal robusto no baseline."

Better:
"Na análise planejada, o desfecho apresentou associação no início do seguimento; a precisão da estimativa deve ser verificada pelo intervalo de confiança."

Bad:
"Nós encontramos que a intervenção prova benefício."

Better:
"Observou-se associação entre a intervenção e menor ocorrência do desfecho. O delineamento não permite afirmar causalidade."

Bad:
"A camada contextual reforçou o eixo obesidade-metabolismo."

Better:
"A análise separada avaliou a relação entre obesidade, alterações metabólicas e risco do desfecho."

## Final Gate

Before delivery, verify:

- The text was written or reconstructed in Portuguese, not translated sentence-by-sentence.
- All factual claims remain supported by `evidence/claim_map.jsonl` where required.
- The venue structure is respected.
- `ptbr-audit` has no blocking issue.
- Any remaining warning is either fixed or explicitly justified.
