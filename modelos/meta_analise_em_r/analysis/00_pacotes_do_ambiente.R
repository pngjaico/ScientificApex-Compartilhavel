# Declara e confere o ambiente R completo da maquina cientifica (R 4.6.1 / renv 1.3.1).
# Uso: Rscript analysis/00_pacotes_do_ambiente.R
#
# Este script permite que o renv descubra todas as dependencias diretas do
# ambiente cientifico e valida que cada pacote carrega sem erro.

pacotes <- c(
  # 1. Machine Learning Clinico, Explicabilidade (XAI) & Modelagem Preditiva (TRIPOD+AI / PROBAST+AI)
  "tidymodels",       # ecossistema unificado (parsnip, recipes, rsample, tune, workflows, yardstick, dials)
  "bonsai",           # extensao parsnip para lightgbm e arvores condicionais (partykit)
  "censored",         # extensao parsnip para modelos de sobrevida em tidymodels
  "finetune",         # tuning acelerado de hiperparametros via corrida ANOVA/racing
  "themis",           # tratamento de desbalanceamento de classes em recipes (SMOTE, upsample, downsample)
  "probably",         # calibracao de probabilidades, Brier e limiares de decisao
  "dcurves",          # Decision Curve Analysis (beneficio liquido clinico)
  "xgboost",          # Gradient Boosting de alto desempenho
  "lightgbm",         # Gradient Boosting baseado em histogramas
  "glmnet",           # regressao penalizada (LASSO, Ridge, Elastic-Net)
  "ranger",           # Random Forests rapidas e de sobrevida
  "pROC",             # curvas ROC, AUC e intervalos DeLong/bootstrap
  "rms",              # regressao clinica, splines restritos e calibracao (Harrell)
  "lme4",             # modelos lineares e generalizados mistos / multinivel
  "DALEX",            # Explainable AI (XAI) agnostico a modelo (importancia por permutacao, residuos, perfis)
  "DALEXtra",         # integracao direta entre DALEX e fluxos tidymodels/workflows
  "ingredients",      # importancia de variaveis, dependencia parcial e efeitos locais acumulados (ALE)
  "iBreakDown",       # atribuicoes locais por observacao/paciente (Break-Down e interacoes)
  "pdp",              # Partial Dependence Plots (PDP) e curvas ICE
  "kernelshap",       # calculo rapido de valores SHAP exatos/amostrados em R puro
  "shapviz",          # visualizacoes SHAP (beeswarm, waterfall, force e dependencia) em ggplot2

  # 2. Meta-Analise Pairwise, Multinivel, Em Rede (NMA), Diagnostica (DTA), Dose-Resposta e PRISMA 2020
  "metafor",          # motor estatistico REML, HKSJ, meta-regressao e multinivel (rma.mv)
  "meta",             # sintese pairwise, forest/funnel/drapery plots e intervalos de predicao
  "netmeta",          # Network Meta-Analysis (NMA) frequentista, consistencia e P-scores
  "clubSandwich",     # variancia robusta a clusters (CRVE) para efeitos dependentes
  "mada",             # meta-analise de acuracia diagnostica (Reitsma bivariado / HSROC)
  "dosresmeta",       # meta-analise dose-resposta multivariada
  "robvis",           # visualizacao de risco de vies (RoB 2, ROBINS-I, QUADAS-2)
  "PRISMA2020",       # diagramas de fluxo PRISMA 2020 oficiais e interativos
  "DiagrammeR",       # motor de grafos e fluxogramas estruturados (Graphviz/Mermaid)
  "DiagrammeRsvg",    # conversao de diagramas PRISMA/DiagrammeR para SVG vetorial
  "rsvg",             # renderizacao nativa de SVG vetorial para PNG/PDF de alta resolucao
  "webshot2",         # captura fiel de tabelas/diagramas HTML via Chrome/Chromium
  "metadat",          # bases de referencia para validacao de modelos meta-analiticos

  # 3. Inferencia Causal Observacional, Riscos Competitivos, Epidemiologia e Poder Amostral
  "MatchIt",          # pareamento por escore de propensao (nearest, optimal, full, genetic, CEM)
  "WeightIt",         # ponderacao pelo inverso da probabilidade de tratamento (IPTW, CBPS, entropy balancing)
  "cobalt",           # diagnostico de balanco de covariaveis e Love Plots prontos para publicacao
  "tidycmprsk",       # riscos competitivos (Fine-Gray e incidencia cumulativa de Gray) integrados ao gtsummary
  "ggsurvfit",        # curvas de sobrevida e incidencia cumulativa nativas em ggplot2
  "epiR",             # epidemiologia clinica (tabelas 2x2, NNT, razao de taxas, concordancia e acuracia)
  "pwr",              # calculo de poder estatistico e tamanho amostral para protocolos clinicos

  # 4. Graficos Cientificos de Alta Qualidade, Sobrevida e Interatividade
  "ggplot2",          # gramatica dos graficos
  "patchwork",        # composicao de paineis cientificos (+, /, plot_annotation)
  "ggpubr",           # formatacao para publicacao cientifica
  "survminer",        # curvas de Kaplan-Meier com tabela de numero em risco
  "cowplot",          # grades e alinhamento editorial de figuras
  "ggridges",         # distribuicoes em cristas (ridge/raincloud)
  "ggrepel",          # rotulos sem sobreposicao
  "viridis",          # paletas perceptualmente uniformes e seguras para daltonismo
  "scales",           # formatacao de eixos e escalas
  "RColorBrewer",     # paletas cartograficas e cientificas
  "ragg",             # renderizacao raster PNG de alta definicao (anti-aliasing)
  "svglite",          # exportacao vetorial SVG editavel
  "plotly",           # graficos HTML interativos (MIT) via ggplotly()

  # 4. Manipulacao de Dados, Imputacao, Tabelas Clinicas e Relatorios
  "dplyr",            # manipulacao relacional de tabelas
  "tidyr",            # pivotagem e organizacao tidy
  "readr",            # leitura rapida e deterministica de CSV/TSV
  "purrr",            # programacao funcional
  "tibble",           # data frames modernos
  "stringr",          # processamento de texto e regex
  "forcats",          # manipulacao de fatores categoricos
  "lubridate",        # datas, tempos e janelas de seguimento
  "data.table",       # processamento tabular ultrarrapido em memoria
  "janitor",          # limpeza de nomes de colunas e tabulacoes (clean_names, tabyl)
  "skimr",            # diagnostico descritivo e completude de variaveis
  "readxl",           # leitura nativa de planilhas Excel (.xls/.xlsx)
  "writexl",          # exportacao nativa de planilhas Excel (.xlsx) sem dependencia Java
  "mice",             # imputacao multipla por equacoes encadeadas (MAR/MNAR)
  "gtsummary",        # Tabela 1 descritiva e tabelas de regressao clinica
  "gt",               # tabelas HTML/LaTeX estruturadas
  "flextable",        # tabelas Word (.docx) editaveis para submissao
  "officer",          # geracao e manipulacao nativa de documentos Word/PowerPoint
  "broom",            # extracao tidy de coeficientes e metricas de modelos
  "broom.mixed",      # extracao tidy para modelos mistos/multinivel
  "parameters",       # extracao padronizada de parametros, ICs e p-valores (easystats)
  "performance",      # diagnosticos de qualidade de ajuste, R2, ICC e colinearidade
  "effectsize",       # tamanhos de efeito padronizados (d de Cohen, g de Hedges, eta2, OR)
  "emmeans",          # medias marginais estimadas e contrastes pos-ajuste
  "marginaleffects",  # efeitos marginais, predicoes ajustadas e comparacoes contrafactuais
  "rmarkdown",        # renderizacao R Markdown
  "knitr",            # motor literario dinamico
  "quarto",           # interface R para Quarto CLI
  "shiny",            # aplicacoes interativas e paineis locais
  "DT",               # tabelas HTML interativas (DataTables, MIT)
  "jsonlite"          # serializacao JSON para manifestos e proveniencia
)

faltando <- character(0)

for (p in pacotes) {
  ok <- requireNamespace(p, quietly = TRUE)
  if (!ok) {
    faltando <- c(faltando, p)
    cat(sprintf("%-18s AUSENTE\n", p))
  } else {
    cat(sprintf("%-18s %s\n", p, as.character(utils::packageVersion(p))))
  }
}

if (length(faltando) > 0) {
  stop("Pacotes ausentes (", length(faltando), "): ", paste(faltando, collapse = ", "),
       "\nRode: Rscript scripts/atualizar_ambiente_meta_analise.R")
}

cat("\nPASS: Ambiente R cientifico completo (", length(pacotes), " pacotes principais verificados).\n", sep = "")
