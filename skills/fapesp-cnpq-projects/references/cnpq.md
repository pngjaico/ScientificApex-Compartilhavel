# CNPq: chamada e formulário são a unidade de conformidade

Não existe neste pacote um modelo oficial único válido para todo CNPq. Identificar a chamada e ler edital, anexos, FAQ e retificações. Bolsa institucional de pós-graduação, apoio a projeto Universal, bolsa de produtividade e chamada temática seguem fluxos distintos. Não apresentar Universal como bolsa individual de mestrado.

## Exemplos históricos, não editais abertos

- Universal 44/2024: o FAQ oficial consultado informa campos de texto de até 4.000 caracteres e anexo reservado a elementos inadequados a texto corrido. Um PDF integral de projeto no anexo não substitui os campos. Usar esse caso para testar a habilidade de adaptar e condensar, não para afirmar limites atuais de outra chamada.
- Chamada CNPq/Decit/SECTICS/MS 29/2024: exemplo de chamada de saúde com modelo estruturado em seus anexos. Abrir a versão efetivamente baixada, conferir numeração dos anexos, limite, eixo temático e instruções. Não confundir folha de rosto com modelo completo. Não transplantar o tema/limites para uma futura Universal.

Os arquivos e hashes históricos foram registrados no projeto de governança; ver `sources.md`. Não rotular como projetos premiados/aprovados. São documentos de chamada e modelos oficiais, não propostas individuais concedidas.

## Transformação em campos

1. Transcrever nomes de campos, obrigatoriedade e limites do formulário real para `requirements.yaml`; guardar evidência da interface sem dados pessoais.
2. Manter texto-mestre rastreável e versões por campo em `drafts/funding/`. Cada campo deve fazer sentido sem exigir um anexo proibido.
3. Contar caracteres, incluindo espaços e quebras; conferir de novo depois de colar no sistema. Sistemas podem contar Unicode/normalização de forma diferente do Python.
4. Verificar equipe, titulação/vínculos, currículo Lattes atualizado, instituição executora, faixas, itens financiáveis, bolsas, restrições e vedações na chamada. Não reutilizar teto financeiro antigo.
5. Mapear objetivos, métodos, metas, resultados, impactos, cronograma e orçamento nos critérios de julgamento efetivos. Pesos só entram na matriz se o edital os declarar; sem pesos, usar avaliação qualitativa.

Após redigir: preservar precisão ao reduzir caracteres. Não remover limitações, comparador, definição do desfecho ou justificativa amostral apenas para caber. Se não couber, reestruturar e priorizar o objetivo central.
