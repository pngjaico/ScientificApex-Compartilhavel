# Fluxo para escolher desenho, pergunta e registro

Este roteiro orienta a preparação. Não escolhe método automaticamente e não infere o tema de protocolos ou perguntas antigas.

## 1. O trabalho é uma revisão de evidências?

- **Pergunta estreita sobre efeitos/intervenções ou exposições com busca abrangente e método reproduzível:** considere revisão sistemática. PICO/PICOS é útil quando população, intervenção/exposição, comparador e desfechos são bem definidos. Metanálise não é obrigatória; só combine evidência clinicamente e metodologicamente compatível.
- **Mapear conceitos, tipos de evidência, definições ou lacunas com pergunta ampla:** considere revisão de escopo. PCC costuma organizar população, conceito e contexto. JBI orienta condução; PRISMA-ScR orienta relato. Não use contagem de estudos como prova de benefício.
- **Explicar contexto, mecanismo, história ou debate:** revisão narrativa pode ser adequada, desde que escopo, escolha de fontes e limitações sejam explícitos. Não a rotule como sistemática se seleção/busca não satisfazem esse método.
- **Síntese necessária em prazo decisório curto:** revisão rápida pode ser considerada se as restrições (fontes, datas, idioma, avaliadores, etapas omitidas) forem predefinidas e justificadas. Rapidez não elimina viés; reporte desvios e efeito na confiança.
- **Já existem revisões sistemáticas pertinentes:** overview/umbrella pode sintetizá-las. Defina critérios, evite misturar estudos primários sem plano, mapeie sobreposição e avalie qualidade/risco de viés das revisões incluídas.
- **Evidência nova provável e atualização contínua sustentável:** revisão viva é um modo de manter uma revisão sistemática, não um método independente. Defina vigilância, gatilhos, ciclos, versão e encerramento; não prometa continuidade sem equipe e recurso.
- **Teste diagnóstico contra padrão de referência:** revisão de acurácia diagnóstica; planeje limiar, população, padrão de referência, pares sensibilidade/especificidade, QUADAS-3 v1.2 e modelo bivariado/HSROC se compatível. QUADAS-2 fica para avaliação histórica especificada ou requisito datado.
- **Curso temporal ou fatores prognósticos:** defina evento, horizonte, origem, censura e riscos competitivos; escolha QUIPS para fatores ou PROBAST/PROBAST+AI para modelos, conforme pergunta.
- **Três ou mais intervenções em rede:** NMA apenas se a rede, transitividade e consistência/coerência forem defensáveis; defina nós e modificadores antes de observar rankings.
- **Nenhuma opção acima:** declare tipo de síntese e justificativa; não force etiqueta familiar.

PRISMA é guia de relato, não método de condução nem selo de validade. Se o método é revisão sistemática, use PRISMA-P na preparação do protocolo, guias específicos aplicáveis e checklist de relato pertinente no manuscrito. Consulte extensão e versão vigentes.

## 2. A pergunta exige estudo primário?

- **Intervenção alocada:** defina ensaio, randomização, ocultação, comparador, estimando, desfecho, horizonte, segurança, contaminação e ética. Use SPIRIT 2025 para protocolo e CONSORT 2025 para relato de resultados, com extensões aplicáveis; versão anterior somente para contexto histórico ou requisito datado. Registro específico de ensaio e aprovação ética podem ser obrigações adicionais; PROSPERO/OSF não os substituem.
- **Exposição sem alocação:** escolha coorte, caso-controle, transversal ou outro desenho pela pergunta temporal e fonte de dados; defina confundidores, viés de seleção, estimando e limites de inferência causal.
- **Diagnóstico:** teste índice, limiar, padrão de referência, amostragem, verificação e espectro dos participantes.
- **Prognóstico/risco futuro:** população-alvo, momento de previsão, horizonte, evento, preditores disponíveis e validação.
- **Modelo preditivo/ML:** declare uso e decisão pretendidos, comparador, validação temporal/geográfica e prevenção de leakage em cada etapa. Desempenho não implica benefício clínico.
- **Simulação ou estudo pré-clínico:** declare o sistema, unidade, modelo e validade externa pretendida; não extrapole para pessoas sem validação apropriada.
- Se for outro desenho, escreva a lógica que liga a pergunta à unidade, amostra e método. Não derive isso de perguntas preexistentes.

## 3. Escolha do registro e limite de início

1. Conclua o questionário e o protocolo em preparação/bootstrap ou congelamento de protocolo. Essas etapas de planejamento são permitidas antes do registro.
2. Para revisão sistemática de saúde, verifique os critérios atuais de elegibilidade do PROSPERO; não presuma aceitação só porque o tema é medicina. Protocolo inelegível deve usar OSF Registries ou registro adequado.
3. Para estudos primários observacionais, previsão/ML, simulação e demais projetos científicos fora do escopo do PROSPERO, use registro final OSF conforme política local. Verifique também requisitos institucionais/da revista.
4. Para ensaio clínico, mantenha OSF/PROSPERO conforme escopo e registre também em registro público de ensaio reconhecido aplicável; verifique aprovação do CEP/IRB, consentimento e requisitos legais antes de recrutar/intervir.
5. Finalize e confronte protocolo, formulário, anexos e métodos. Submeta ao registro externo somente com autorização específica e apropriada; nunca envie dados identificáveis de participantes.
6. Aguarde confirmação final do registro. Rascunho, projeto OSF, submissão pendente, DOI de projeto, manuscrito de protocolo ou número fictício não atende à política local.
7. Arquive snapshot datado do registro final no projeto, calcule SHA-256 e peça a um revisor nomeado que confira identidade do registro e correspondência com o protocolo congelado.
8. Use o comando local registry register para declarar metadados do registro já realizado; ele não submete nada. Use registry verify para conferir evidência local revisada e hash. Só então o gate local pode permitir iniciar atividade científica.
9. Antes de corpus, busca/triagem formal, extração, análise, descoberta ou redação científica, confirme gate. Se o protocolo mudar depois, registre emenda com motivo e impacto; reavalie registro, ética e fingerprint antes de retomar.

**Política mais estrita do workspace:** exige registro final PROSPERO ou OSF revisado antes de qualquer trabalho científico, mesmo que a política de um periódico ou registro aceite cadastro posterior. Nunca chame registro retrospectivo de prospectivo. O registro local verifica consistência documental e SHA-256; não prova sozinho autenticidade externa nem validade científica.

## Fontes oficiais consultadas

- [PROSPERO — instruções para registro e elegibilidade](https://www.crd.york.ac.uk/prospero/documents/Registering%20a%20review%20on%20PROSPERO.pdf)
- [OSF — registros e pré-registros](https://help.osf.io/article/330-welcome-to-registrations)
- [PRISMA-P — protocolos de revisão sistemática](https://www.prisma-statement.org/protocols)
- [PRISMA — extensão de escopo](https://www.prisma-statement.org/scoping)
- [EQUATOR — diretrizes de relato](https://www.equator-network.org/reporting-guidelines/)
- [PROBAST/PROBAST+AI](https://www.probast.org/)
- [QUADAS-3 v1.2 — Bristol](https://www.bristol.ac.uk/population-health-sciences/projects/quadas/quadas-3/)
- [SPIRIT 2025/CONSORT 2025](https://www.consort-spirit.org/)
