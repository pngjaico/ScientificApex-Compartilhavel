# Modelo de ambiente R científico e meta-análise

Modelo inicial do ambiente R 4.6.1 (`renv 1.3.1`) da máquina científica. Não é um estudo clínico concluído nem possui protocolo registrado.

## Pilha instalada e travada (`renv.lock`)

O arquivo `analysis/00_pacotes_do_ambiente.R` declara e valida 69 pacotes CRAN diretos (e seu fecho transitivo completo em `renv.lock` e `ambiente/renv.lock`), organizados em quatro frentes:

1. **Machine learning clínico, explicabilidade (XAI) e predição (TRIPOD+AI / PROBAST+AI):** `tidymodels`, `probably`, `dcurves`, `xgboost`, `lightgbm`, `glmnet`, `ranger`, `pROC`, `rms`, `DALEX`, `DALEXtra`, `ingredients`, `iBreakDown`, `pdp`, `kernelshap`, `shapviz`.
2. **Meta-análise pairwise, multinível, em rede (NMA), diagnóstica (DTA) e dose-resposta:** `metafor`, `meta`, `netmeta`, `clubSandwich`, `mada`, `dosresmeta`, `robvis`, `PRISMA2020`, `metadat`.
3. **Gráficos científicos, sobrevida e interatividade:** `ggplot2`, `patchwork`, `ggpubr`, `survminer`, `cowplot`, `ggridges`, `ggrepel`, `viridis`, `scales`, `RColorBrewer`, `ragg`, `svglite`, `plotly`.
4. **Manipulação de dados, imputação, tabelas clínicas e relatórios:** `dplyr`, `tidyr`, `readr`, `purrr`, `tibble`, `stringr`, `forcats`, `lubridate`, `data.table`, `janitor`, `skimr`, `readxl`, `writexl`, `mice`, `gtsummary`, `gt`, `flextable`, `officer`, `broom`, `broom.mixed`, `parameters`, `performance`, `effectsize`, `emmeans`, `marginaleffects`, `rmarkdown`, `knitr`, `quarto`, `shiny`, `DT`, `jsonlite`.

## Exclusões deliberadas de governança

- **`dmetar`:** ausente do CRAN (pacote apenas no GitHub); diagnósticos de influência, Baujat, leave-one-out, viés de publicação e subgrupos são cobertos nativamente por `metafor` e `meta`.
- **`gemtc` / `BUGSnet`:** dependem de binário externo JAGS/Stan no sistema operacional (`rjags`); a NMA padrão usa `netmeta` e `metafor::rma.mv`.
- **`highcharter`:** envolve a biblioteca JavaScript proprietária Highcharts (licença comercial paga); gráficos HTML interativos usam `plotly` (licença MIT).
- **`chattr` / `ellmer`:** clientes de LLM dentro do runtime R violam a execução determinística offline e a política zero-trust de dados; a orquestração por IA ocorre fora do R via Article Machine.
- **`keras` / `tensorflow` / `torch`:** Deep Learning roda no ambiente Python isolado (`PyTorch 2.15.0+cpu` em `modelos/aprendizado_de_maquina_clinico/ambientes/aprendizado_profundo/`).

## Como verificar e usar

- Conferir o ambiente: `"Rscript" --vanilla analysis/00_pacotes_do_ambiente.R`
- Atualizar/sincronizar lockfile a partir da raiz: `"Rscript" --vanilla scripts/atualizar_ambiente_meta_analise.R`
- Executar script em projeto ativo (após registro final PROSPERO/OSF verificado): `.\.venv\Scripts\python.exe -m article_machine run-r projects/<id> projects/<id>/analysis/<script>.R`

As entregas científicas geradas devem existir em `portugues/` e `ingles/`, com nomes de arquivos em português e dados/código/locks compartilhados.
