---
license: Apache-2.0
name: meta-analise-medica
description: Use for protocol-driven systematic reviews and meta-analyses of clinical evidence in R, from PICO and reproducible search through duplicate screening, extraction, risk of bias, synthesis, small-k uncertainty, GRADE, and paired PT-BR/English outputs. Not for pooling incompatible outcomes or study designs.
---

# Meta-análise médica

Versão local: 2026-11-01. Curadoria baseada nas skills locais `tooluniverse-meta-analysis`, `risk-of-bias-assistant`, `grade-sof-table-builder`, `asreview-screening-bridge` e `statistical-analysis`; a skill ToolUniverse está em `hold` e não é tratada como aprovada ou instalada. Este texto não afirma atualização upstream.

## Entregas bilíngues

Entregue relatórios, tabelas narrativas e texto científico em pares PT-BR/EN, sob subpastas `portugues/` e `ingles/` dentro das pastas-base portuguesas. Código R, dados extraídos, scripts, ambiente e lock são compartilhados uma vez. Use `bilingual-scientific-writing` e `article-machine workflow audit-language`; conserve números, estimandos, IDs de estudo/claim, citações, direção e força dos claims, limitações e disclosures. A auditoria automatizada não verifica equivalência semântica; faça revisão humana das duas versões.

## Protocolo e corpus

1. Entre no projeto ativo e leia `project.yaml`, `protocol.yaml`, `standards.yaml` e `compute.yaml`. Defina PICO/PECO, elegibilidade, desfechos prioritários, estimandos, desenhos elegíveis, sínteses planejadas e subgrupos antes de examinar resultados. Registre protocolo e alterações justificadas.
2. Mantenha busca auditável: bases e plataformas, estratégia completa por base, data, limites, deduplicação e fluxo de registros. Preserve exportações e decisões em `sources/` e `evidence/`; não apresente busca parcial como exaustiva. Use PRISMA 2020 para o relato.
3. Faça triagem obrigatoriamente através do motor triplo-cego canônico (`article-machine corpus screen <project_dir>`), composto por dois revisores cegos independentes (clínico PICO e metodológico) com arbitragem formal pelo árbitro sênior. O motor gera nativamente o arquivo de exportação Rayyan (`rayyan_screening_export.csv`), o ledger de consenso multiagente (`screening/multi_agent_screening_ledger.jsonl`), os checklists oficiais PRISMA 2020 e PRISMA-NMA em `evidence/prisma/` e a tabela de exclusões com justificativas (PRISMA 2020 Item 16b). Extraia definições, denominadores, tempo de seguimento, desenho, estimativa, incerteza, ajustes, perdas e fonte exata. Mantenha tabela rastreável entre artigo, estudo, população e efeito.
4. Avalie risco de viés com ferramenta apropriada ao desenho (por exemplo RoB 2, ROBINS-I, QUADAS-2 ou PROBAST+AI). Registre justificativa por domínio; ausência de informação não significa baixo risco. A síntese não corrige vieses dos estudos incluídos.

## Síntese em R

- Antes de combinar, confirme que população, intervenção/exposição, comparador, desfecho, medida, direção e horizonte são suficientemente compatíveis para o estimando escolhido. Mantenha análises distintas quando não forem.
- Transforme medidas de razão para escala logarítmica e registre a transformação inversa para apresentação. Para medidas contínuas, justifique diferença de médias ou padronização. Não misture efeitos comparativos com proporções brutas. Meta-análise de proporção exige pergunta de prevalência/incidência, denominador e período comparáveis, modelo apropriado e justificativa; proporções incompatíveis não viram um efeito comum por estarem na mesma escala.
- Não trate múltiplos desfechos, tempos, braços ou subgrupos do mesmo estudo como independentes. Pré-especifique a seleção de um efeito ou modele dependência (por exemplo estrutura multivariada/multinível ou variância robusta quando justificável), explicando limites se poucos estudos sustentarem o modelo.
- Escolha efeito comum ou aleatório pela pergunta e pela plausibilidade de uma distribuição de efeitos, nunca pelo teste de heterogeneidade ou um corte de I². Para modelo aleatório, pré-especifique REML para τ² quando apropriado e faça sensibilidade a outro estimador se k ou os eventos forem escassos; nenhum estimador é universalmente superior. Documente pacote/versão R, código e dados derivados em `analysis/`; preserve lock de ambiente do projeto.
- Com poucos estudos, τ², I², intervalos e testes de heterogeneidade são imprecisos. Hartung–Knapp–Sidik–Jonkman (HKSJ) incorpora incerteza e usa distribuição t; pode gerar intervalos excessivamente largos com k muito pequeno, mas em certas condições de heterogeneidade estimada como zero pode até ser estreito demais. Wald pode ignorar incerteza em τ² e também ficar estreito. Com dois ou três estudos, compare abordagens (incluindo variantes modificadas quando justificadas) em sensibilidade, interprete diferenças explicitamente e não escolha o intervalo que favorece a conclusão. Não use previsão para novos estudos como se fosse precisa quando k é pequeno.
- Apresente estimativa e IC, k e participantes, τ², I² com cautela, direção dos efeitos e heterogeneidade clínica/metodológica. Faça análises de sensibilidade previstas; subgrupos e meta-regressão exigem hipótese prévia e número de estudos suficiente. Não use funnel plot/teste de assimetria como diagnóstico confiável com poucos estudos.

## Certeza e comunicação

Depois da síntese, aplique GRADE por desfecho, documentando risco de viés, inconsistência, indireção, imprecisão e viés de publicação, além de justificativas para upgrades quando pertinentes. Vincule tabela SoF e conclusões às fontes/claims do projeto. Diferencie resultado narrativo de estimativa quantitativa. Mantenha `evidence/claim_map.jsonl` e `drafts/references.bib` sincronizados; rode Evidence Lock e Review Trinity antes de declarar manuscrito pronto.

## Referências de método

- [Cochrane Handbook, capítulo 10](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-10): escolha do modelo, REML, HKSJ e limitações quando há poucos estudos.
- [PRISMA 2020](https://www.prisma-statement.org/prisma-2020): relato de revisões sistemáticas.
- [GRADE Book](https://book.gradepro.org/): orientação do grupo GRADE; confira o conteúdo vigente para a pergunta específica.
