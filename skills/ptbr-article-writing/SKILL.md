---
name: ptbr-article-writing
description: Use when drafting, rewriting, naturalizing, or auditing scientific manuscripts, abstracts, thesis chapters, posters, decks, or Article Machine outputs in Portuguese, especially Brazilian Portuguese, pt-BR versus pt-PT variant control, natural scientific prose without AI-like tone, journal/editorial profiles, IMRAD, structured abstracts, SciELO metadata, ABNT, Vancouver/ICMJE/NLM, APA, IEEE, Chicago, citation/reference formatting, ptbr-audit, Evidence Lock, or Portuguese style review.
---

# PT-BR Article Writing

## Overview

Escreva primeiro em português científico natural. O padrão local é português brasileiro acadêmico, mas a variante deve ser congelada como `pt-BR` ou `pt-PT` quando houver revista-alvo. Não traduza um molde em inglês; reconstrua a frase a partir do objetivo, método, resultado, público, destino editorial e limite real da evidência.

## Mandatory Flow

1. Identifique o projeto ativo em `projects/<project_id>/` e leia `project.yaml`, `protocol.yaml`, `standards.yaml` e `compute.yaml` quando a tarefa envolver evidência, análise, descoberta, manuscrito ou entrega científica.
2. Congele o perfil editorial antes de redigir: variante (`pt-BR` ou `pt-PT`), área, tipo de manuscrito, revista/congresso/banca, seção, sistema de citação e limite de palavras.
3. Atualize ou consulte um Task Packet antes de redigir texto substantivo.
4. Gere um perfil de escrita com:

```powershell
article-machine style ptbr-brief --deliverable "<tipo>" --audience "<leitor>" --output "<project_dir>/context/ptbr_generation_brief.md"
```

5. Use o perfil, o protocolo, o mapa de claims e as regras do periódico/congresso para escrever. Não invente fato para melhorar fluidez.
6. Para texto existente com cheiro de tradução, rode:

```powershell
article-machine style ptbr-naturalize "<entrada.md>" --output "<saida.md>" --json-output "<relatorio.json>"
```

7. Audite antes de chamar de pronto:

```powershell
article-machine style ptbr-audit "<arquivo.md>" --output "<audit.md>" --json-output "<audit.json>"
```

8. Se houver conteúdo factual, rode o fluxo de Evidence Lock/Review Trinity aplicável. Texto bonito sem claim seguro continua reprovado.

Use o caminho `.venv\Scripts\article-machine.exe` quando o comando não estiver no PATH.

## Citation Style Extension

Antes de formatar citações ou referências:

1. Identifique o estilo exigido pelo periódico, congresso, banca ou instituição.
2. Leia `references/citation-and-reference-styles.md`.
3. Não misture famílias: ABNT autor-data/numeric, Vancouver numeric, APA autor-data, IEEE numeric e Chicago notas/autor-data têm lógicas diferentes.
4. Confirme a edição vigente da norma ou manual. ABNT deve ser verificada em fonte institucional/ABNT; gerador automático não é prova.
5. Corrija metadados antes da pontuação: autor, título, periódico, ano, volume, número, páginas/eLocation, DOI, PMID/PMID Central, URL e data de acesso quando exigida.
6. Sincronize `drafts/references.bib`, citações no texto e `evidence/claim_map.jsonl`. Citação perfeita para fonte errada continua erro científico.

Pare se o usuário pedir "ABNT" genericamente para submissão biomédica sem informar o destino. ABNT costuma reger trabalhos acadêmicos no Brasil; muitos periódicos biomédicos exigem Vancouver/ICMJE/NLM mesmo quando o texto está em português.

## Editorial Profile Gate

Use `references/editorial-portuguese-profiles.md` quando o pedido envolver revista-alvo, SciELO, Elsevier, Acta Médica Portuguesa, Cadernos de Saúde Pública, Revista de Saúde Pública, pt-PT, metadados, resumo estruturado, "sem tom de IA", "natural", "não parecer tradução" ou "perfil editorial".

- Perfil ABNT acadêmico brasileiro: use para tese, TCC, dissertação, trabalho institucional e banca. ABNT organiza documento e referência; não substitui guia de revista.
- Perfil biomédico/Vancouver: use para manuscritos de saúde quando o destino pedir ICMJE, Vancouver, NLM ou citação numérica.
- Perfil SciELO/periódico brasileiro: trate metadados em inglês, palavras-chave DeCS/MeSH, ciência aberta e declaração de uso de IA como parte do produto editorial quando exigidos.
- Perfil pt-PT: use apenas quando o destino pedir português europeu; não misture "Aplicámos/Obtivemos/Pretendeu-se" com pt-BR.
- Fallback seguro: texto científico em português com IMRAD explícito, resumo proporcional, variante consistente, hedging e pós-edição anti-calque.

## Writing Standard

| Elemento | Faça | Bloqueie |
|---|---|---|
| Resumo | Objetivo, método, resultados principais e conclusão proporcional | Resumo que promete mais do que o corpo mostra |
| Introdução | Problema, lacuna e objetivo no fim da seção | Nariz de cera, revisão extensa sem pergunta clara |
| Métodos | Delineamento, fonte, período, população, análise e critérios | "Foi utilizada uma abordagem robusta" sem detalhe operacional |
| Resultados | Números, medidas, intervalos e direção do efeito | Interpretação antes de apresentar o achado |
| Discussão | Principal achado, comparação, limites e implicação prudente | Conclusão causal sem desenho causal |
| Conclusão | Responder ao objetivo com incerteza explícita | "Mais estudos são necessários" como frase vazia |

## Natural Portuguese Rules

- Prefira ordem direta: sujeito, verbo, complemento.
- Use verbos concretos no lugar de substantivos abstratos quando a frase ficar pesada.
- Em resumos e aberturas, prefira frases de 15 a 30 palavras; acima de 35 palavras, divida salvo necessidade metodológica real.
- Defina siglas na primeira menção e evite sigla no resumo se ela não for inevitável.
- Troque anglicismos dispensáveis: `endpoint` -> desfecho; `baseline` -> início do seguimento; `framework` -> modelo de trabalho ou estrutura metodológica.
- Troque calques e marcadores vazios: `endereçar` -> abordar; `lançar luz` -> examinar; `temática em questão` -> tema; `no que tange a` -> quanto a.
- Use "os achados sugerem", "foi observada associação" ou "a estimativa indicou" quando o desenho não permite causalidade.
- Bloqueie força indevida: "prova", "demonstra definitivamente", "altamente significativo", "impactante" e "robusto" sem número, intervalo, desenho ou referente empírico.
- Mantenha termos internacionais quando forem a forma reconhecida da medida, mas explique em português: razão de riscos instantâneos (hazard ratio, HR).
- Corte frases longas antes de polir adjetivos. Uma frase com duas relações metodológicas deve virar duas frases.

## Evidence And Claims

- Use `{{claim:claim-id}}` para qualquer afirmação factual em `drafts/manuscript.md`.
- Não transforme cautela metodológica em fraqueza estilística. Incerteza bem escrita é melhor do que precisão falsa.
- Não apague números, intervalos, datas, nomes de bases, critérios de inclusão, ferramentas de risco de viés ou limitações para deixar o texto mais "natural".
- Se uma frase ficar feia porque a evidência é incompleta, preserve a feiura metodológica e registre a pendência.

## Calibration Reference

Leia `references/portuguese-academic-style.md` quando:

- for escrever manuscrito, resumo expandido, tese, poster ou deck em português;
- o texto tiver muitos anglicismos, voz passiva ou nominalizações;
- o usuário pedir "não parecer tradução";
- o periódico/congresso exigir resumo, IMRAD, PRISMA, Vancouver, DeCS/MeSH ou estrutura específica.

Leia `references/editorial-portuguese-profiles.md` quando:

- for escolher entre ABNT acadêmico, biomédico/Vancouver, SciELO/periódico brasileiro ou pt-PT;
- houver revista-alvo, guia de autores, metadados bilíngues, resumo estruturado ou exigência de transparência sobre IA;
- o usuário pedir texto natural, sem tom de IA, sem cara de tradução, ou adaptação para português europeu;
- precisar decidir se a primeira pessoa do plural é aceitável ou se deve usar impessoalidade.

Leia `references/citation-and-reference-styles.md` quando:

- o usuário pedir ABNT, NBR 6023, NBR 10520, NBR 14724, NBR 6028, Vancouver, ICMJE, NLM, Citing Medicine, APA, IEEE, Chicago, AMA ou "normas de referência";
- for converter bibliografia entre estilos;
- houver conflito entre norma institucional, instruções de periódico e saída de gerador bibliográfico;
- precisar auditar se as citações no texto batem com a lista de referências.

## Common Mistakes

| Erro | Correção |
|---|---|
| Traduzir "we found that" como "nós encontramos que" | "Observou-se que", "Os dados mostraram" ou "Foi identificada associação" |
| Usar "no contexto de" para qualquer coisa | Nomeie a análise, população ou cenário real |
| Chamar todo resultado de "sinal" | Use associação, estimativa, resultado, padrão observado ou achado |
| Dizer "robusto", "inovador", "definitivo" | Mostre desenho, amostra, precisão e limite |
| Dizer "lança luz", "impactante", "altamente significativo" | Troque por objetivo, medida, magnitude e cautela |
| Usar "endereçar uma questão" | "abordar uma questão", "avaliar uma hipótese" ou "examinar uma lacuna" |
| Misturar pt-BR e pt-PT | Congele a variante e normalize léxico, pessoa verbal e títulos de seção |
| Reescrever conclusão para soar forte | Ajuste a força à evidência; se necessário, reduza a conclusão |
| Auditar só ortografia | Rode `ptbr-audit` e Evidence Lock; estilo e verdade são gates separados |
| Aplicar ABNT 6023:2018 por hábito | Verifique a edição vigente; em 2025 a NBR 6023 recebeu atualização/substituição |
| Chamar todo estilo numérico de Vancouver | Vancouver biomédico deve seguir ICMJE/NLM/Citing Medicine ou a instrução do periódico |
| Deixar Zotero/gerador decidir sozinho | Use gerador só como rascunho; confira metadados e regra do destino |

## Stop Conditions

Pare e reporte falha claramente se:

- `Rscript` for necessário pelo projeto e estiver ausente;
- o texto factual não tiver claim map ou fonte verificável;
- o `ptbr-audit` retornar `block`;
- houver mojibake, caracteres quebrados ou perda de acentos;
- o usuário pedir submissão, poster, slides ou resumo fora do pipeline de deliverables.
- a norma bibliográfica exigida não estiver identificada ou entrar em conflito com a regra do destino.
