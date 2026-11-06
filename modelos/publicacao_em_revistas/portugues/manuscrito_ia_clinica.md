> MODELO NÃO PREENCHIDO. Não é manuscrito pronto nem evidência. Substitua campos entre colchetes somente com informação verificada. Pesquisa bloqueada até registro final PROSPERO/OSF revisado; preparar protocolo é permitido. Nunca inventar resultados, registro, ética, autores ou declarações. Claims factuais no rascunho canônico usam `{{claim:ID}}` e referências verificadas. Antes do envio: Evidence Lock, Review Trinity, auditoria numérica PT/EN e conferência humana de conteúdo/layout e das regras atuais da revista.

# [Título: desenvolvimento/validação de modelo de predição]
## Resumo
[Uso pretendido, desenho, fonte/período, pacientes/eventos, validação, discriminação/calibração e IC, limites; TRIPOD+AI.]
## Introdução
[Decisão clínica, população-alvo, comparador real e contribuição incremental.]
## Métodos
[Registro e estimando; aquisição/consentimento; momento de predição; desfecho independente; unidade paciente; splits por paciente/centro/tempo; amostra justificada; baseline simples; imputação, transformação e seleção somente no treino; nested CV para seleção e avaliação; protocolo externo separado; tuning e orçamento; calibração sem vazamento; métricas/IC por paciente; utilidade clínica; fairness justificada e precisão por subgrupo; versões/seed/locks.]
[DL/imagens: proveniência, desidentificação DICOM, duplicatas, splits por paciente, anotações cegas/discordâncias, pesos e licença, augmentation só no treino, shift de dispositivo/centro. Não tratar Grad-CAM/SHAP como validação causal ou clínica.]
## Resultados
[Fluxo e prevalência, baseline versus modelo no mesmo teste, AUC e AUPRC conforme contexto, calibração/intercepto/inclinação, Brier, IC, validação externa quando feita, erros/falhas e limites de implantação. Ausência de validação externa explicitada.]
## Discussão
[PROBAST+AI, risco de vazamento/viés/transportabilidade, benefício clínico ainda não demonstrado quando só retrospectivo.]
## Suplementos
[Checklist TRIPOD+AI, auditoria PROBAST+AI, dicionário, plano, model card, código e manifesto de splits sem dados pessoais.]
