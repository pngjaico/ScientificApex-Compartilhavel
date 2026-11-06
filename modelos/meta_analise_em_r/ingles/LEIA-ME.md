# Scientific R environment and meta-analysis template

Starting template for the scientific machine's R 4.6.1 (`renv 1.3.1`) environment. This is not a completed clinical study and has no registered protocol.

## Installed and locked stack (`renv.lock`)

The script `analysis/00_pacotes_do_ambiente.R` declares and validates 69 direct CRAN packages (and their full transitive closure in `renv.lock` and `ambiente/renv.lock`), organized into four pillars:

1. **Clinical machine learning, explainability (XAI), and prediction (TRIPOD+AI / PROBAST+AI):** `tidymodels`, `probably`, `dcurves`, `xgboost`, `lightgbm`, `glmnet`, `ranger`, `pROC`, `rms`, `DALEX`, `DALEXtra`, `ingredients`, `iBreakDown`, `pdp`, `kernelshap`, `shapviz`.
2. **Pairwise, multilevel, network (NMA), diagnostic (DTA), and dose-response meta-analysis:** `metafor`, `meta`, `netmeta`, `clubSandwich`, `mada`, `dosresmeta`, `robvis`, `PRISMA2020`, `metadat`.
3. **Scientific graphics, survival, and interactivity:** `ggplot2`, `patchwork`, `ggpubr`, `survminer`, `cowplot`, `ggridges`, `ggrepel`, `viridis`, `scales`, `RColorBrewer`, `ragg`, `svglite`, `plotly`.
4. **Data wrangling, imputation, clinical tables, and reporting:** `dplyr`, `tidyr`, `readr`, `purrr`, `tibble`, `stringr`, `forcats`, `lubridate`, `data.table`, `janitor`, `skimr`, `readxl`, `writexl`, `mice`, `gtsummary`, `gt`, `flextable`, `officer`, `broom`, `broom.mixed`, `parameters`, `performance`, `effectsize`, `emmeans`, `marginaleffects`, `rmarkdown`, `knitr`, `quarto`, `shiny`, `DT`, `jsonlite`.

## Deliberate governance exclusions

- **`dmetar`:** not on CRAN (GitHub-only package); influence, Baujat, leave-one-out, publication bias, and subgroup diagnostics are natively covered by `metafor` and `meta`.
- **`gemtc` / `BUGSnet`:** require an external OS installation of JAGS/Stan (`rjags`); standard NMA uses `netmeta` and `metafor::rma.mv`.
- **`highcharter`:** wraps the proprietary Highcharts JavaScript library (paid commercial license); interactive HTML charts use `plotly` (MIT license).
- **`chattr` / `ellmer`:** calling external LLMs from inside R scripts breaks offline deterministic reproducibility and zero-trust data governance; AI orchestration runs outside R via Article Machine.
- **`keras` / `tensorflow` / `torch`:** Deep Learning runs in the isolated Python environment (`PyTorch 2.15.0+cpu` under `modelos/aprendizado_de_maquina_clinico/ambientes/aprendizado_profundo/`).

## How to verify and use

- Verify the environment: `"Rscript" --vanilla analysis/00_pacotes_do_ambiente.R`
- Refresh/synchronize the lockfile from the workspace root: `"Rscript" --vanilla scripts/atualizar_ambiente_meta_analise.R`
- Run an R script in an active project (after verified final PROSPERO/OSF registration): `.\.venv\Scripts\python.exe -m article_machine run-r projects/<id> projects/<id>/analysis/<script>.R`

All new scientific deliverables must be paired in `portugues/` and `ingles/`, using Portuguese base filenames and shared code/data/locks.
