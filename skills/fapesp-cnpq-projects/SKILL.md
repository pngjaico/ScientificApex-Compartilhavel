---
name: fapesp-cnpq-projects
description: Use when drafting, adapting or critically reviewing FAPESP or CNPq research proposals, postgraduate scholarship projects, budgets, data management plans, curricular summaries or responses to funding reviewers in Brazil.
---

# Projetos FAPESP e CNPq

Produzir propostas rastreáveis, executáveis e adequadas à modalidade. Escrever bem não corrige inelegibilidade, amostra inviável nem método incapaz de responder à pergunta. Nunca prometer aprovação ou completude universal.

## Entrada e seleção

No Article Machine, selecionar `projects/<project_id>/`, ler os quatro contratos e construir Task Packet antes de pesquisar ou redigir conteúdo científico. Esta skill cobre fomento brasileiro; `research-grants` permanece complementar para outras agências, sem importar regras NIH/NSF.

Na máquina canônica em D:, obedecer `.AGENTES`: preparar protocolos/propostas é permitido, mas corpus, triagem, extração, análise, descoberta e manuscrito científico exigem registro final PROSPERO/OSF revisado e verificado. Projeto OSF ou declaração local não satisfazem o gate. Não submeter registro sem autorização específica. Entregar documentos novos em pares `portugues/` e `ingles/` quando exigido pela política local.

1. Identificar agência, modalidade, chamada/ano, versão e retificações, prazo/fuso, candidato, responsável, instituição-sede, executora, colaboradores e produto pedido. Bolsa de aluno, auxílio do orientador e submissão ao programa de pós-graduação são processos diferentes.
2. Ler [fontes e vigência](references/sources.md), depois [FAPESP](references/fapesp.md) ou [CNPq](references/cnpq.md). Buscar a norma oficial vigente em https://fapesp.br/ e https://www.gov.br/cnpq/; abrir o texto integral e retificações. Resultado de busca e modelo antigo não bastam. Não preencher credenciais nem enviar formulários ao pesquisar.
3. Registrar cada exigência em `context/funding/requirements.yaml` a partir de [requirements.yaml](assets/requirements.yaml). Conservar URL, seção/página, data de acesso, versão, modalidade, limite, caráter obrigatório/recomendado e conflito. Se o portal divergir do edital, documentar e resolver; não escolher silenciosamente a regra mais conveniente.
4. Exigências específicas e retificações válidas prevalecem sobre o roteiro geral. Tratar modelos históricos como referência de organização, nunca como norma atual nem como prova de concessão. Se a chamada estiver indefinida, gerar minuta-base com pendências, sem alegar conformidade.

## Escrita e adaptação

- Usar [bolsa](assets/bolsa.md), [Regular](assets/regular.md) ou [CNPq por campos](assets/cnpq-fields.md). São templates autorais adaptáveis, não formulários oficiais. Copiar somente os arquivos necessários para `drafts/funding/`; preservar originais do usuário.
- Antes do texto longo, fechar pergunta, hipótese, desfecho primário, estimando, população, desenho e plano de análise. Ler [régua científica e clínica](references/scientific-review.md) para pesquisa hospitalar, biomarcadores ou imagem.
- Escrever a cadeia problema → lacuna demonstrada → pergunta → objetivo → método → análise → resultado verificável. Cada objetivo deve ter dado acessível, responsável, custo, prazo e critério de conclusão. Separar contribuição esperada de resultado já observado; separar novidade verificada de hipótese.
- Produzir [orçamento](assets/budget.csv), [cronograma](assets/timeline.csv) e [PGD](assets/data-management.md) quando pertinentes. Conferir rubricas, itens financiáveis, limites, contrapartidas e duplicidade com outros apoios na chamada efetiva. Cotação tem data, moeda e validade; valor desconhecido fica pendente. Não presumir que bolsa financia integralmente kits, tomografias ou equipe.
- Para súmula, usar o roteiro oficial vigente: selecionar contribuições demonstráveis e explicar relação com o projeto; não inventar índices, vínculos, prêmios ou produtividade. Histórico do aluno e trajetória do orientador também são avaliados; texto persuasivo não substitui os documentos.
- Preservar a voz e participação intelectual do candidato. Não ocultar uso de IA quando houver exigência de declaração. Para inglês/PT-BR e DOCX/PDF editável, acionar `bilingual-scientific-writing` e `academic-office-deliverables` conforme o produto.

## Integridade e revisão

Evidência científica vai para `sources/registry.jsonl`, `evidence/claim_map.jsonl` e `drafts/references.bib`. Manter `{{claim:id}}` no rascunho factual da máquina, com resolução conforme o contrato local; exportação limpa somente após validação. Dados preliminares exigem origem, N e análise reais. Nunca converter previsão, simulação ou exemplo em dado preliminar.

Revisar com [checklist](references/review.md). Em reconsideração, responder ponto a ponto: parecer literal → diagnóstico → alteração/localização → evidência → limite residual; não fabricar parecer nem fazer ataque pessoal. Verificar as regras de reconsideração da modalidade.

Entregar:
- `context/funding/requirements.yaml` e registro das fontes oficiais;
- `drafts/funding/` com versão narrativa ou campos do sistema;
- orçamento, cronograma, PGD e lista de documentos aplicáveis;
- `reviews/funding_review.md` com falhas, pendências, conflitos e verificações executadas;
- para submissão, pacote de arquivos com hash/versão e mapa arquivo → campo do portal.

O script `scripts/check_packet.py <requirements.yaml>` verifica apenas metadados, presença das evidências normativas, atualidade declarada e limites de caracteres. Não verifica mérito, elegibilidade real, páginas, layout, referências nem o portal. Exigir conferência humana/visual dos arquivos finais e Evidence Lock/Review Trinity antes de declarar pacote pronto. Preparar pacote não autoriza submissão externa; pedir confirmação somente quando o envio concreto estiver revisável.

No workspace, executar com `.\.venv\Scripts\python.exe skills/fapesp-cnpq-projects/scripts/check_packet.py projects/<project_id>/context/funding/requirements.yaml`. Dependência: PyYAML no ambiente Python. A advertência após 30 dias é heurística local de revisão, não prazo de validade definido pela agência; checar a fonte ao usar mesmo dentro desse intervalo.
