# Fontes, modelos e proveniência

Consulta documental inicial: 02/11/2026. Estes links são pontos de entrada, não um cache de regras permanentemente válidas. Buscar retificações e confirmar modalidade/versão a cada uso. Sínteses autorais; os templates de `assets/` não são formulários oficiais.

## Normas e roteiros oficiais

| ID | Fonte | Uso e limite |
|---|---|---|
| F-MS | https://fapesp.br/bolsas/ms | Norma MS consultada indica vigência desde 01/09/2026; verificar elegibilidade e documentos no texto integral. |
| F-DR | https://fapesp.br/bolsas/dr | Rota da modalidade; confirmar destino e norma efetiva. Texto consultado também em https://fapesp.br/261/bolsa-de-doutorado-norma-vigente-a-partir-de-01062024 . |
| F-DD | https://fapesp.br/bolsas/dd | Modalidade distinta de DR; consultar requisitos próprios. |
| F-BOLSA | https://fapesp.br/253/projeto-de-pesquisa | Roteiro geral de projeto de bolsa, atualização indicada 24/01/2020; não é roteiro do Regular. |
| F-APR | https://fapesp.br/apr | Norma do Auxílio Regular; conferir elegibilidade, orçamento e documentos; não reutilizar teto antigo sem verificação. |
| F-REG | https://fapesp.br/10408/roteiro-para-formatacao-do-projeto-de-pesquisa-auxilio-a-pesquisa-regular | Formatação específica do Regular, atualização indicada 24/03/2025. |
| F-PGD | https://fapesp.br/gestaodedados | Conteúdo do PGD e exceções por chamada; não há modelo único. |
| F-SC | https://fapesp.br/sumula | Roteiro e modelo de súmula; atualização indicada março de 2025. |
| F-REV | https://fapesp.br/595 | Entrada do formulário de parecer do Regular; abrir a versão aplicável antes da revisão. |
| C-44 | https://www.gov.br/cnpq/pt-br/chamadas/todas-as-chamadas/chamadas-2024/chamada-ndeg-44-2024/chamada-publica-cnpq-mcti-fndct-ndeg-44-2024-universal | Chamada histórica Universal 44/2024, encerrada; documentos originais e FAQ. |
| C-FAQ44 | https://www.gov.br/cnpq/pt-br/chamadas/todas-as-chamadas/chamadas-2024/chamada-ndeg-44-2024/FAQChamadaUniversal_2024v23122024.pdf | FAQ histórico: campos de até 4.000 caracteres e restrição do anexo; não generalizar para outra chamada. |
| C-29 | https://www.gov.br/cnpq/pt-br/chamadas/todas-as-chamadas/chamadas-2024/chamada-ndeg-29-2024-1 | Chamada histórica de saúde com anexos; observar a finalidade de cada arquivo e o eixo específico. |

## Modelos históricos disponíveis

Os downloads oficiais da criação desta skill estão em `projects/article-machine-governance-2026/context/fapesp-cnpq-research/`, com URLs e SHA-256 no relatório `sources-research.md`. Esse arquivo de pesquisa é rastreabilidade local, não dependência para usar a skill. Baixar novamente pelas fontes oficiais quando os arquivos não estiverem presentes.

- Universal 44/2024: documento de chamada; não é proposta individual aprovada.
- Chamada 29/2024: PDF integral inclui modelo estruturado; DOC separado é folha de rosto. A numeração/paginação precisa corresponder à edição efetivamente utilizada.
- Modelos institucionais em branco são referência editorial secundária. Se divergirem da norma da agência, prevalece a norma aplicável, com o conflito registrado.
- Modelo institucional UNESP FEB em branco, baixado e identificado como template, sem comprovação de aprovação de proposta: https://www.feb.unesp.br/Home/Administracao110/DTA/STAEPE/modelo-de-projeto-de-pesquisa.pdf . Serve para estudar organização; pode refletir formatação antiga.

Conflito verificado na pesquisa inicial: a página antiga FAPESP `/12981` ainda traz limites antigos do Regular (20 páginas, 24 meses e referência a R$200 mil); o roteiro `/10408`, atualizado em 2025, informa 25 páginas, e a norma atual ligada por `/apr` deve controlar vigência/duração/custeio. Não usar a página antiga como atalho. Registrar a resolução da regra aplicável na matriz da proposta.

Dois exemplos oficiais históricos de resumos de projetos financiados, com registros e metadados na BV FAPESP:

- https://bv.fapesp.br/pt/auxilios/111549/indo-alem-do-primeiro-ciclo-de-colheita-nas-florestas-tropicais-da-amazonia-brasileira/
- https://bv.fapesp.br/pt/auxilios/112133/explorando-o-potencial-da-cannabis-no-tratamento-de-doencas-neurodegenerativas/

A BV fornece descrições públicas, não o projeto integral submetido. Esses registros não demonstram que a redação pública reproduz a proposta avaliada. Não copiar frases nem transferir alegações científicas para outro domínio. Para modelos integrais fornecidos pelo usuário: confirmar autorização, remover dados pessoais da cópia de trabalho e registrar aprovação somente se houver documento comprobatório.

## Como atualizar

Para cada chamada real, salvar em `sources/funding/` os documentos normativos públicos necessários, URL original/final, título, edição, seção/página e SHA-256 quando houver download. Preencher `requirements.yaml` com as regras daquela proposta; não marcar uma fonte como verificada apenas porque seu domínio é oficial. Marcar exemplos como `historical-example`, mesmo que o endereço tenha sido acessado hoje.

Downloads locais não concedem licença de redistribuição. Preservar autoria; preferir links oficiais e sínteses próprias em pacotes compartilháveis. Não incorporar propostas confidenciais ou dados humanos a esta skill reutilizável.
