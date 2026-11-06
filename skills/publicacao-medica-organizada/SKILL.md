---
name: publicacao-medica-organizada
description: Use to organize a medical manuscript and its journal-specific versions inside an existing Article Machine project, create an empty publication index, preserve canonical drafts/evidence paths, prepare paired PT-BR/English deliverables, or audit a journal submission checklist. Does not submit manuscripts or move existing material.
---

# Publicação médica organizada

Versão local: 2026-11-01. Curadoria baseada nas skills locais `ptbr-article-writing`, `bilingual-scientific-writing`, `anti-ai-writing-governor`, `venue-templates` e no helper local de organização; não representa atualização upstream instalada.

## Estrutura por projeto

1. Escolha o projeto ativo e leia `project.yaml`, `protocol.yaml`, `standards.yaml` e `compute.yaml`. Mantenha rascunhos, análises, contratos, claim map e referências nos caminhos canônicos do projeto.
2. Para indexar uma versão destinada a uma revista, use `projects/article-machine-governance-2026/analysis/codex-first-2026-11-01/organizar_publicacoes.py` com `--raiz` apontando para a raiz do workspace, `--projeto <slug>`, `--revista <slug>` e `--identificador <versão>`. O `--dry-run` é o padrão e só valida/exibe o destino. Só use `--criar` quando a pessoa pediu a criação; o script cria pastas vazias e um manifesto, não importa arquivos.
3. O caminho é `projects/<projeto>/publicacoes/<revista>/<versão>/`. A estrutura gerada separa protocolo, busca/referências, dados autorizados, análises, tabelas, figuras, manuscrito, revisão e submissão. Use nomes `tipo_assunto_YYYY-MM-DD_vNN.ext`.
4. Não mova, renomeie nem copie manuscritos antigos, evidências, dados humanos ou PDFs para a estrutura nova. O manifesto deve apontar aos caminhos canônicos. Não duplique pacotes em `deliverables/`; registre apenas referência aprovada ao pipeline canônico. Se o destino já existir, pare e preserve-o.

## Pares PT-BR/EN

Toda entrega textual científica/editorial deve ter versões PT-BR e EN. Preserve nomes-base de pastas em português e organize os pares em subpastas `portugues/` e `ingles/`, por exemplo `07_manuscrito/portugues/` e `07_manuscrito/ingles/`, com pares equivalentes em `08_revisao/` e `09_submissao/` quando houver esses documentos. Se `LEIA-ME.md` for parte do pacote entregue, forneça também sua versão em inglês. Código, dados, análise, claims, referências canônicas e locks permanecem compartilhados uma vez; não crie cópias divergentes por idioma. Use `bilingual-scientific-writing` e `article-machine workflow audit-language`, seguidos de revisão humana de fidelidade semântica. Preserve números, IDs, citações, incerteza, força dos claims e disclosure.

## Preparação editorial

- Encaminhe texto em pt-BR a `ptbr-article-writing`; use `bilingual-scientific-writing` para manter fidelidade entre idiomas e `anti-ai-writing-governor` para naturalizar sem apagar limitações, citações, números ou disclosure de IA.
- Para a revista exata, tipo de artigo e etapa, confira instruções oficiais atuais e registre URL e data da consulta via `venue-templates`. Faça checklist de escopo, formato e limite de palavras, resumo, tabelas/figuras, referências, anonimização quando exigida, ética/consentimento, registro, autoria, financiamento, conflitos, dados/código, IA e suplementos.
- Preserve números e referências; resolva divergências com fontes do projeto. Alinhe fatos a `evidence/claim_map.jsonl`, mantenha `drafts/references.bib` sincronizado e aplique Evidence Lock e Review Trinity antes de afirmar prontidão científica.
- A skill pode preparar checklist e arquivos locais de apoio. Não envia manuscrito, não usa portal de submissão, não declara submissão concluída e não confirma requisitos atuais sem consultar a fonte oficial do destino.
