---
name: metodos-ml-clinico
description: Use for developing or validating clinical prediction models with regression, machine learning, or deep learning; covers patient-level nested validation, calibration, uncertainty, external validation, TRIPOD+AI reporting, PROBAST+AI appraisal, and paired PT-BR/English scientific outputs. Not for bedside diagnosis or treatment decisions.
---

# Métodos de ML clínico

Versão local: 2026-11-01. Curadoria baseada nas skills locais `risk-of-bias-assistant`, `in-silico-validation-governor`, `statistical-analysis` e `experimental-design-planner`; não representa atualização upstream instalada.

## Fluxo

1. Trabalhe dentro do projeto ativo. Leia `project.yaml`, `protocol.yaml`, `standards.yaml` e `compute.yaml`; defina população, cenário de uso, horizonte, desfecho, preditores disponíveis no momento da decisão e estimando antes de modelar. Registre decisões no Task Packet e no protocolo.
2. Entregue relatórios e texto científico em pares PT-BR/EN, em subpastas `portugues/` e `ingles/` sob pastas-base portuguesas. Mantenha código, dados analíticos, modelo e lock de ambiente uma só vez na área compartilhada; não duplique artefatos técnicos por idioma. Use `bilingual-scientific-writing` e `article-machine workflow audit-language`; preserve números, unidades, IDs, citações, direção dos efeitos, força dos claims, limitações e disclosures. A checagem automatizada é lexical; uma pessoa deve revisar a fidelidade semântica.
3. Separe os dados por unidade de independência. Repetições do mesmo paciente nunca podem cair em treino e teste diferentes. Use validação cruzada aninhada: a camada interna seleciona hiperparâmetros e a externa estima desempenho sem esse viés de seleção. Agrupe por paciente; use divisão temporal ou por centro quando a pergunta for transporte no tempo ou entre serviços.
4. Compare com baselines clínicos e estatísticos simples, incluindo regressão apropriada ao desfecho. Considere DL somente se o usuário pedir ou se volume, modalidade e estrutura dos dados justificarem a complexidade. PyTorch é opcional e sob demanda; não instale nem mude o ambiente compartilhado para fazê-lo funcionar.
5. Relate discriminação e calibração. AUC/C-statistic isolada não sustenta utilidade clínica: inclua calibração gráfica, intercepto e inclinação, Brier quando adequado, e avaliação de benefício/decisão apenas para limiares e ações clinicamente definidos. Estime intervalos de confiança coerentes com paciente, centro e desenho; preserve prevalência, composição da amostra e horizonte.
6. Faça validação externa em dados realmente independentes do desenvolvimento. Não chame reamostragem interna de validação externa. Se recalibrar ou atualizar o modelo, descreva a mudança e avalie em dados ainda não usados nessa atualização.
7. Procure vazamento por paciente, tempo, centro, pré-processamento, imputação, seleção de variáveis e ajuste de hiperparâmetros. Examine dados ausentes, definição do desfecho, censura, mudanças de prática, desempenho por subgrupos relevantes e limites de transportabilidade.
8. Use TRIPOD+AI para transparência do relato; ele não é ferramenta de qualidade nem prova de validade. Use PROBAST+AI para julgar qualidade do desenvolvimento, risco de viés da avaliação e aplicabilidade. Registre julgamentos com evidência e incerteza; não atribua baixo risco por falta de informação.
9. **Gratuidade Estrita e Acesso Aberto dos Dados (Zero-Cost Mandate):** Toda base de dados clínica utilizada para desenvolvimento, validação ou benchmark DEVE ser 100% gratuita e de acesso público/aberto, com custo financeiro zero para o pesquisador. É estritamente proibido selecionar ou desenhar projetos dependentes de bases com cobrança de taxas administrativas, tarifas de processamento de arquivos (como taxas de US$ 200 a US$ 1.000 da SRTR/SAF), assinaturas ou paywalls de dados, exceto sob instrução expressa e financiamento garantido pelo usuário. Priorize repositórios abertos (Zenodo, Dryad, Harvard Dataverse, PhysioNet, OpenML, Kaggle) e bases governamentais de acesso público gratuito (como DATASUS/SNT, SEER público, etc.).

## Saída e limite clínico

Guarde plano, código, ambiente, sementes, partições, resultados e validações em `projects/<id>/analysis/`, com proveniência suficiente para reproduzir cada estimativa. Afirmações factuais do manuscrito seguem `evidence/claim_map.jsonl`, Evidence Lock e Review Trinity. Desempenho preditivo não demonstra causalidade, benefício clínico ou segurança. Não recomende uso assistencial sem validação externa pertinente, avaliação de impacto e governança clínica.

## Referências de método

- [TRIPOD+AI (BMJ, 2024)](https://www.bmj.com/content/385/bmj-2023-078378): guia de relato para modelos de predição com regressão ou ML.
- [PROBAST+AI (BMJ, 2025)](https://www.bmj.com/content/388/bmj-2024-082505): qualidade, risco de viés e aplicabilidade.
