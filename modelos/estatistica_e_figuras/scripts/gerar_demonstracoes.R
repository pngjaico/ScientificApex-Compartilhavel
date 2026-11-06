# Demonstra\u{e7}\u{f5}es estat\u{ed}sticas sint\u{e9}ticas para revis\u{e3}o de m\u{e9}todos
# R 4.6.1; depend\u{ea}ncias locais em ../ambiente/biblioteca.
# Uso: Rscript --vanilla scripts/gerar_demonstracoes.R <diretorio_de_saida>
args <- commandArgs(trailingOnly = TRUE)
# Use a Windows single-byte locale so UTF-8 source escapes render as accents.
if (.Platform$OS.type == "windows") {
  try(Sys.setlocale("LC_CTYPE", "English_United States.1252"), silent = TRUE)
}
script_arg <- grep("^--file=", commandArgs(), value = TRUE)
script_path <- sub("^--file=", "", script_arg[[1]])
model_root <- normalizePath(file.path(dirname(script_path), ".."), winslash = "/", mustWork = TRUE)
library_path <- file.path(model_root, "ambiente", "biblioteca")
.libPaths(c(library_path, .Library.site, .Library))

required <- c("ggplot2", "patchwork", "gtsummary", "gt", "flextable", "officer",
              "ragg", "svglite", "metafor", "jsonlite")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) stop("Pacotes ausentes na biblioteca local: ", paste(missing, collapse = ", "))
if (length(args) != 1) stop("Informe um \u{fa}nico diret\u{f3}rio de sa\u{ed}da.")
out_root <- normalizePath(args[[1]], winslash = "/", mustWork = FALSE)
if (!dir.exists(out_root)) dir.create(out_root, recursive = TRUE)
for (lang in c("portugues", "ingles")) {
  dir.create(file.path(out_root, lang), recursive = TRUE, showWarnings = FALSE)
}
pt_dir <- file.path(out_root, "portugues")
en_dir <- file.path(out_root, "ingles")
seed <- 20261102L
set.seed(seed)

# A base \u{e9} artificial e tem apenas vari\u{e1}veis abstratas; n\u{e3}o simula uma coorte cl\u{ed}nica.
n <- 240L
grupo <- factor(rep(c("A", "B"), each = n / 2), levels = c("A", "B"))
medida <- rnorm(n, mean = ifelse(grupo == "A", 0, 0.28), sd = 1)
indicador <- rbinom(n, 1, plogis(-0.25 + 0.35 * (grupo == "B")))
medida[seq(19, n, by = 31)] <- NA_real_
dados <- data.frame(grupo = grupo, medida_sintetica = medida,
                    indicador_sintetico = factor(indicador, levels = 0:1,
                                                  labels = c("N\u{e3}o", "Sim")))
dados_en <- dados
levels(dados_en$indicador_sintetico) <- c("No", "Yes")
dados_para_csv <- data.frame(
  grupo = as.character(dados$grupo),
  medida_sintetica = dados$medida_sintetica,
  indicador_sintetico = as.character(dados$indicador_sintetico),
  stringsAsFactors = FALSE
)
dados_para_csv$indicador_sintetico[dados_para_csv$indicador_sintetico == "N\u{e3}o"] <- "Nao"
write.csv(dados_para_csv, file.path(out_root, "dados_sinteticos_compartilhados.csv"),
          row.names = FALSE, na = "", fileEncoding = "UTF-8")

# Base sint\u{e9}tica de estudos: a unidade s\u{e3}o estudos simulados, n\u{e3}o pessoas nem dados publicados.
estudos <- data.frame(
  estudo = paste0("Estudo ", LETTERS[1:6]),
  grupo_sintetico = factor(rep(c("A", "B"), 3), levels = c("A", "B")),
  estimativa = c(0.10, 0.28, -0.06, 0.19, 0.34, 0.05),
  erro_padrao = c(0.16, 0.21, 0.18, 0.15, 0.24, 0.17)
)
ajuste <- metafor::rma.uni(yi = estimativa, sei = erro_padrao, data = estudos,
                           method = "REML", test = "knha")
studies <- transform(estudos,
  inferior = estimativa - qnorm(0.975) * erro_padrao,
  superior = estimativa + qnorm(0.975) * erro_padrao
)
sum_row <- data.frame(
  estudo = "Resumo aleat\u{f3}rio (REML)",
  grupo_sintetico = NA,
  estimativa = as.numeric(ajuste$b),
  erro_padrao = ajuste$se,
  inferior = ajuste$ci.lb,
  superior = ajuste$ci.ub
)
sum_row_en <- sum_row
sum_row_en$estudo <- "Random-effects summary (REML)"
tab_est <- rbind(
  studies[, c("estudo", "estimativa", "erro_padrao", "inferior", "superior")],
  sum_row[, c("estudo", "estimativa", "erro_padrao", "inferior", "superior")]
)
tab_est_en <- tab_est
tab_est_en$estudo <- c(paste("Study", LETTERS[1:6]), sum_row_en$estudo)
write.csv(tab_est, file.path(pt_dir, "tabela_estimativas_sinteticas_2026-11-02_v01.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")
write.csv(tab_est_en, file.path(en_dir, "tabela_estimativas_sinteticas_2026-11-02_v01.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

# Estilo comum: forma al\u{e9}m de cor; linhas e fundos com contraste expl\u{ed}cito.
cores <- c("A" = "#0072B2", "B" = "#D55E00")
formas <- c("A" = 16, "B" = 17)
tema <- ggplot2::theme_minimal(base_size = 11) +
  ggplot2::theme(panel.grid.minor = ggplot2::element_blank(),
    legend.position = "bottom", legend.title = ggplot2::element_blank(),
    plot.title.position = "plot")

make_distribution <- function(language = c("portugues", "ingles")) {
  language <- match.arg(language)
  is_pt <- language == "portugues"
  labels <- if (is_pt) c("Grupo A", "Grupo B") else c("Group A", "Group B")
  title <- if (is_pt) "Distribui\u{e7}\u{e3}o de uma medida sint\u{e9}tica" else "Distribution of a synthetic measure"
  subtitle <- if (is_pt) "240 observa\u{e7}\u{f5}es geradas; aus\u{ea}ncias mantidas e indicadas na tabela" else
    "240 generated observations; missing values retained and shown in the table"
  xlabel <- if (is_pt) "Grupo sint\u{e9}tico" else "Synthetic group"
  ylabel <- if (is_pt) "Medida (unidades arbitr\u{e1}rias)" else "Measure (arbitrary units)"
  ggplot2::ggplot(dados, ggplot2::aes(x = grupo, y = medida_sintetica,
    fill = grupo, color = grupo)) +
    ggplot2::geom_violin(trim = FALSE, alpha = .22, na.rm = TRUE) +
    ggplot2::geom_boxplot(width = .13, alpha = .75, outlier.shape = NA, na.rm = TRUE) +
    ggplot2::stat_summary(fun = median, geom = "point",
      ggplot2::aes(shape = grupo), size = 2.8, color = "black", na.rm = TRUE) +
    ggplot2::scale_fill_manual(values = cores, labels = labels) +
    ggplot2::scale_color_manual(values = cores, labels = labels) +
    ggplot2::scale_shape_manual(values = formas, labels = labels) +
    ggplot2::labs(title = title, subtitle = subtitle, x = xlabel, y = ylabel) + tema
}
p_dist_pt <- make_distribution("portugues")
p_dist_en <- make_distribution("ingles")

make_forest <- function(language = c("portugues", "ingles")) {
  language <- match.arg(language)
  is_pt <- language == "portugues"
  dat <- studies
  dat$rotulo <- if (is_pt) dat$estudo else paste("Study", LETTERS[1:6])
  dat$grupo <- dat$grupo_sintetico
  pooled <- if (is_pt) "Resumo aleat\u{f3}rio (REML)" else "Random-effects summary (REML)"
  dat$rotulo <- factor(dat$rotulo, levels = rev(c(dat$rotulo, pooled)))
  pooled_row <- data.frame(rotulo = factor(pooled, levels = levels(dat$rotulo)),
    grupo = factor(NA, levels = c("A", "B")), estimativa = as.numeric(ajuste$b),
    inferior = ajuste$ci.lb, superior = ajuste$ci.ub)
  forest_data <- rbind(
    data.frame(rotulo = dat$rotulo, grupo = dat$grupo, estimativa = dat$estimativa,
      inferior = dat$inferior, superior = dat$superior),
    pooled_row
  )
  forest_data$tipo <- ifelse(as.character(forest_data$rotulo) == pooled, "Resumo", "Estudo")
  xlabel <- if (is_pt) "Diferen\u{e7}a padronizada sint\u{e9}tica (IC 95%)" else
    "Synthetic standardized difference (95% CI)"
  title <- if (is_pt) "Forest plot did\u{e1}tico \u{2014} dados simulados" else
    "Teaching forest plot \u{2014} simulated data"
  subtitle <- if (is_pt) "Seis estudos artificiais; REML e intervalo Hartung\u{2013}Knapp" else
    "Six artificial studies; REML and Hartung\u{2013}Knapp interval"
  ggplot2::ggplot(forest_data, ggplot2::aes(y = rotulo, x = estimativa,
    xmin = inferior, xmax = superior, color = grupo, shape = grupo)) +
    ggplot2::geom_vline(xintercept = 0, linetype = 2, color = "grey45") +
    ggplot2::geom_errorbar(data = subset(forest_data, tipo == "Estudo"),
      width = .55, orientation = "y", linewidth = .55, na.rm = TRUE) +
    ggplot2::geom_errorbar(data = subset(forest_data, tipo == "Resumo"),
      ggplot2::aes(y = rotulo, xmin = inferior, xmax = superior),
      inherit.aes = FALSE, width = .55, orientation = "y",
      linewidth = 1.05, color = "#222222", na.rm = TRUE) +
    ggplot2::geom_segment(data = subset(forest_data, tipo == "Resumo"),
      ggplot2::aes(x = inferior, xend = superior, y = rotulo, yend = rotulo),
      inherit.aes = FALSE, linewidth = 1.05, color = "#222222", na.rm = TRUE) +
    ggplot2::geom_point(size = 2.7, na.rm = TRUE) +
    ggplot2::geom_point(data = subset(forest_data, tipo == "Resumo"),
      color = "black", shape = 23, fill = "#F0E442", size = 3.3) +
    ggplot2::scale_color_manual(values = cores,
      labels = if (is_pt) c("Grupo A", "Grupo B") else c("Group A", "Group B"),
      na.translate = FALSE) +
    ggplot2::scale_shape_manual(values = formas,
      labels = if (is_pt) c("Grupo A", "Grupo B") else c("Group A", "Group B"),
      na.translate = FALSE) +
    ggplot2::labs(title = title, subtitle = subtitle, x = xlabel, y = NULL,
      caption = if (is_pt) "Pontos/linhas finas = estudos e ICs; losango = estimativa combinada; linha grossa = IC 95% Hartung\u{2013}Knapp; dados simulados." else
        "Points/thin lines = studies and CIs; diamond = pooled estimate; thick line = Hartung\u{2013}Knapp 95% CI; simulated data.") +
    tema + ggplot2::theme(legend.position = "bottom")
}
p_forest_pt <- make_forest("portugues")
p_forest_en <- make_forest("ingles")

# Predi\u{e7}\u{e3}o/calibra\u{e7}\u{e3}o ilustrativa: parti\u{e7}\u{e3}o aleat\u{f3}ria sint\u{e9}tica, treino separado do teste.
set.seed(seed + 1L)
n_pred <- 600L
x <- rnorm(n_pred)
g <- rbinom(n_pred, 1, .5)
prob_geradora <- plogis(-0.45 + 0.75 * x + 0.35 * g)
y <- rbinom(n_pred, 1, prob_geradora)
pred_df <- data.frame(x = x, g = factor(g, levels = 0:1, labels = c("A", "B")), y = y)
idx_train <- sample(seq_len(n_pred), size = floor(.70 * n_pred))
treino <- pred_df[idx_train, ]
teste <- pred_df[-idx_train, ]
modelo_sintetico <- stats::glm(y ~ x + g, data = treino, family = stats::binomial())
teste$prob_predita <- stats::predict(modelo_sintetico, newdata = teste, type = "response")
breaks <- seq(0, 1, length.out = 11)
teste$faixa <- cut(teste$prob_predita, breaks = breaks, include.lowest = TRUE)
cal <- do.call(rbind, lapply(split(teste, teste$faixa, drop = TRUE), function(z) {
  n_bin <- nrow(z)
  eventos <- sum(z$y)
  ci <- stats::binom.test(eventos, n_bin)$conf.int
  data.frame(prob_media = mean(z$prob_predita), fracao_observada = mean(z$y),
    inferior = ci[[1]], superior = ci[[2]], n = n_bin, eventos = eventos)
}))
cal <- cal[order(cal$prob_media), ]
write.csv(cal, file.path(out_root, "calibracao_sintetica_compartilhada.csv"),
  row.names = FALSE, fileEncoding = "UTF-8")
make_calibration <- function(language = c("portugues", "ingles")) {
  language <- match.arg(language)
  is_pt <- language == "portugues"
  group_label <- if (is_pt) "Amostra de teste" else "Test sample"
  title <- if (is_pt) "Calibra\u{e7}\u{e3}o em dados sint\u{e9}ticos" else "Calibration in synthetic data"
  subtitle <- if (is_pt) "Curva agrupada em decis; IC binomial exato por faixa" else
    "Decile-binned curve; exact binomial CI by bin"
  xlabel <- if (is_pt) "Probabilidade m\u{e9}dia predita" else "Mean predicted probability"
  ylabel <- if (is_pt) "Frequ\u{ea}ncia observada" else "Observed frequency"
  caption <- if (is_pt) "Parti\u{e7}\u{e3}o aleat\u{f3}ria 70/30; treino separado; n por faixa nos dados compartilhados." else
    "Random 70/30 split; separate training set; bin n is in the shared data."
  ggplot2::ggplot(cal, ggplot2::aes(x = prob_media, y = fracao_observada,
    color = group_label, shape = group_label)) +
    ggplot2::geom_abline(slope = 1, intercept = 0, linetype = 2, color = "grey45") +
    ggplot2::geom_errorbar(ggplot2::aes(ymin = inferior, ymax = superior), width = 0,
      linewidth = .55) +
    ggplot2::geom_line(linewidth = .55) + ggplot2::geom_point(size = 2.8) +
    ggplot2::scale_color_manual(values = stats::setNames("#0072B2", group_label)) +
    ggplot2::scale_shape_manual(values = stats::setNames(17, group_label)) +
    ggplot2::coord_equal(xlim = c(0, 1), ylim = c(0, 1), expand = FALSE) +
    ggplot2::labs(title = title, subtitle = subtitle, x = xlabel, y = ylabel,
      color = NULL, shape = NULL, caption = caption) + tema
}
p_cal_pt <- make_calibration("portugues")
p_cal_en <- make_calibration("ingles")

# Tabela 1: somente descri\u{e7}\u{e3}o; n\u{e3}o s\u{e3}o executados testes de compara\u{e7}\u{e3}o ou p-valores.
tbl_pt <- gtsummary::tbl_summary(
  data = dados, by = grupo,
  include = c(medida_sintetica, indicador_sintetico),
  label = list(medida_sintetica ~ "Medida sint\u{e9}tica (unidades arbitr\u{e1}rias)",
               indicador_sintetico ~ "Indicador sint\u{e9}tico"),
  statistic = list(gtsummary::all_continuous() ~ "{median} ({p25}, {p75})",
                   gtsummary::all_categorical() ~ "{n} ({p}%)"),
  digits = gtsummary::all_continuous() ~ 1,
  missing = "ifany", missing_text = "Ausente", percent = "column"
)
tbl_en <- gtsummary::tbl_summary(
  data = dados_en, by = grupo,
  include = c(medida_sintetica, indicador_sintetico),
  label = list(medida_sintetica ~ "Synthetic measure (arbitrary units)",
               indicador_sintetico ~ "Synthetic indicator"),
  statistic = list(gtsummary::all_continuous() ~ "{median} ({p25}, {p75})",
                   gtsummary::all_categorical() ~ "{n} ({p}%)"),
  digits = gtsummary::all_continuous() ~ 1,
  missing = "ifany", missing_text = "Missing", percent = "column"
)
tbl_pt <- gtsummary::modify_header(tbl_pt,
  label ~ "**Vari\u{e1}vel**", gtsummary::all_stat_cols() ~ "**{level}**<br>N = {n}")
tbl_en <- gtsummary::modify_header(tbl_en,
  label ~ "**Variable**", gtsummary::all_stat_cols() ~ "**{level}**<br>N = {n}")
tbl_pt <- gtsummary::modify_caption(tbl_pt, "**Tabela 1.** Caracter\u{ed}sticas descritivas da amostra sint\u{e9}tica.")
tbl_en <- gtsummary::modify_caption(tbl_en, "**Table 1.** Descriptive characteristics of the synthetic sample.")
gt::gtsave(gtsummary::as_gt(tbl_pt), file.path(pt_dir, "tabela1_sintetica_2026-11-02_v01.html"))
gt::gtsave(gtsummary::as_gt(tbl_en), file.path(en_dir, "tabela1_sintetica_2026-11-02_v01.html"))
flextable::save_as_docx(gtsummary::as_flex_table(tbl_pt),
  path = file.path(pt_dir, "tabela1_sintetica_2026-11-02_v01.docx"))
flextable::save_as_docx(gtsummary::as_flex_table(tbl_en),
  path = file.path(en_dir, "tabela1_sintetica_2026-11-02_v01.docx"))

# CSV descritivo da Tabela 1, calculado dos mesmos dados e sem testes ou p-valores.
t1_por_grupo <- do.call(rbind, lapply(levels(grupo), function(gp) {
  idx <- dados$grupo == gp
  xg <- dados$medida_sintetica[idx]
  ig <- as.character(dados$indicador_sintetico[idx])
  n_total <- sum(idx)
  data.frame(grupo = gp, n_total = n_total, n_medida = sum(!is.na(xg)),
    mediana_medida = stats::median(xg, na.rm = TRUE),
    q1_medida = unname(stats::quantile(xg, .25, na.rm = TRUE)),
    q3_medida = unname(stats::quantile(xg, .75, na.rm = TRUE)),
    ausentes_medida = sum(is.na(xg)),
    indicador_nao_n = sum(ig == "N\u{e3}o", na.rm = TRUE),
    indicador_nao_pct = 100 * mean(ig == "N\u{e3}o", na.rm = TRUE),
    indicador_sim_n = sum(ig == "Sim", na.rm = TRUE),
    indicador_sim_pct = 100 * mean(ig == "Sim", na.rm = TRUE)
  )
}))
t1_english <- t1_por_grupo
names(t1_english) <- c("group", "total_n", "measure_n", "measure_median",
  "measure_q1", "measure_q3", "measure_missing_n",
  "indicator_no_n", "indicator_no_pct", "indicator_yes_n", "indicator_yes_pct")
write.csv(t1_por_grupo, file.path(pt_dir, "tabela1_sintetica_2026-11-02_v01.csv"),
  row.names = FALSE, fileEncoding = "UTF-8")
write.csv(t1_english, file.path(en_dir, "tabela1_sintetica_2026-11-02_v01.csv"),
  row.names = FALSE, fileEncoding = "UTF-8")

# Tabela de efeitos: as colunas num\u{e9}ricas v\u{ea}m do mesmo objeto em ambos os idiomas.
make_est_tbl <- function(dat, english = FALSE) {
  names(dat) <- if (english) c("Study", "Estimate", "Standard error", "Lower 95% CI", "Upper 95% CI") else
    c("Estudo", "Estimativa", "Erro padr\u{e3}o", "Limite inferior do IC 95%", "Limite superior do IC 95%")
  dat
}
est_pt <- make_est_tbl(tab_est, FALSE)
est_en <- make_est_tbl(tab_est_en, TRUE)
make_simple_gt <- function(dat, caption) {
  gt::gt(dat) |>
    gt::fmt_number(columns = where(is.numeric), decimals = 3) |>
    gt::tab_header(title = caption) |>
    gt::cols_align(align = "center", columns = where(is.numeric))
}
gt::gtsave(make_simple_gt(est_pt, "Estimativas sint\u{e9}ticas e intervalos de confian\u{e7}a"),
  file.path(pt_dir, "tabela_estimativas_sinteticas_2026-11-02_v01.html"))
gt::gtsave(make_simple_gt(est_en, "Synthetic estimates and confidence intervals"),
  file.path(en_dir, "tabela_estimativas_sinteticas_2026-11-02_v01.html"))
flextable::save_as_docx(flextable::flextable(est_pt),
  path = file.path(pt_dir, "tabela_estimativas_sinteticas_2026-11-02_v01.docx"))
flextable::save_as_docx(flextable::flextable(est_en),
  path = file.path(en_dir, "tabela_estimativas_sinteticas_2026-11-02_v01.docx"))

save_plot <- function(plot, dir, basename) {
  ggplot2::ggsave(file.path(dir, paste0(basename, ".svg")), plot = plot,
    device = svglite::svglite, width = 8.2, height = 5.4, units = "in")
  ggplot2::ggsave(file.path(dir, paste0(basename, ".png")), plot = plot,
    device = ragg::agg_png, width = 8.2, height = 5.4, units = "in", dpi = 300)
}
save_plot(p_dist_pt, pt_dir, "figura_distribuicao_sintetica_2026-11-02_v01")
save_plot(p_dist_en, en_dir, "figura_distribuicao_sintetica_2026-11-02_v01")
save_plot(p_forest_pt, pt_dir, "figura_floresta_sintetica_2026-11-02_v01")
save_plot(p_forest_en, en_dir, "figura_floresta_sintetica_2026-11-02_v01")
save_plot(p_cal_pt, pt_dir, "figura_calibracao_sintetica_2026-11-02_v01")
save_plot(p_cal_en, en_dir, "figura_calibracao_sintetica_2026-11-02_v01")
painel_pt <- patchwork::wrap_plots(p_forest_pt, p_cal_pt, ncol = 2) +
  patchwork::plot_annotation(title = "Efeitos e calibra\u{e7}\u{e3}o \u{2014} dados sint\u{e9}ticos")
painel_en <- patchwork::wrap_plots(p_forest_en, p_cal_en, ncol = 2) +
  patchwork::plot_annotation(title = "Effects and calibration \u{2014} synthetic data")
save_plot(painel_pt, pt_dir, "figura_painel_efeitos_calibracao_sinteticos_2026-11-02_v01")
save_plot(painel_en, en_dir, "figura_painel_efeitos_calibracao_sinteticos_2026-11-02_v01")

metadata_pt <- c(
  "# Legendas e textos alternativos", "",
  "- **Distribui\u{e7}\u{e3}o sint\u{e9}tica:** os violinos mostram a distribui\u{e7}\u{e3}o observada da medida arbitr\u{e1}ria em dois grupos simulados; caixa = intervalo interquartil; linha central = mediana. O marcador tamb\u{e9}m codifica o grupo.",
  "- **Forest plot sint\u{e9}tico:** pontos e ICs de 95% mostram seis efeitos artificiais; o losango representa o modelo aleat\u{f3}rio REML com ajuste Hartung\u{2013}Knapp. Escala centrada em zero; nada aqui \u{e9} um efeito cl\u{ed}nico.",
  "- **Calibra\u{e7}\u{e3}o sint\u{e9}tica:** cada ponto resume uma faixa de probabilidades preditas no conjunto de teste; a linha diagonal indica previs\u{e3}o = frequ\u{ea}ncia observada; barras = IC binomial exato de 95%. O gr\u{e1}fico n\u{e3}o valida um modelo cl\u{ed}nico.",
  "- **Painel sint\u{e9}tico:** re\u{fa}ne o forest plot e a calibra\u{e7}\u{e3}o lado a lado; os dois gr\u{e1}ficos mant\u{ea}m escalas, legendas e textos alternativos individuais.",
  "", "Estas s\u{e3}o demonstra\u{e7}\u{f5}es de formato, n\u{e3}o valida\u{e7}\u{e3}o editorial visual nem teste formal de acessibilidade. Dados completos e tamanhos por faixa est\u{e3}o nos CSVs compartilhados."
)
metadata_en <- c(
  "# Captions and alternative text", "",
  "- **Synthetic distribution:** violins show the observed distribution of an arbitrary measure in two simulated groups; box = interquartile range; centre line = median. The marker also encodes group.",
  "- **Synthetic forest plot:** points and 95% CIs show six artificial effects; the diamond is the REML random-effects model with Hartung\u{2013}Knapp adjustment. The scale is centred at zero; nothing here is a clinical effect.",
  "- **Synthetic calibration:** each point summarizes a predicted-probability bin in the test set; the diagonal denotes predicted = observed frequency; bars = exact 95% binomial CIs. The plot does not validate a clinical model.",
  "- **Synthetic panel:** places the forest plot and calibration plot side by side; each keeps its own scales, legend, and alternative text.",
  "", "These are format demonstrations, not editorial visual validation or formal accessibility testing. Full data and bin sizes are in the shared CSV files."
)
writeLines(metadata_pt, file.path(pt_dir, "legendas_e_textos_alternativos.md"), useBytes = TRUE)
writeLines(metadata_en, file.path(en_dir, "legendas_e_textos_alternativos.md"), useBytes = TRUE)

# Proveni\u{ea}ncia t\u{e9}cnica compartilhada; n\u{e3}o \u{e9} artefato cient\u{ed}fico traduzido.
versions <- vapply(required, function(p) as.character(utils::packageVersion(p)), character(1))
prov <- list(
  schema = "demonstracao_sintetica_v1",
  gerado_em_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
  R = R.version.string, semente = seed, n_tabela1 = n,
  estudos_sinteticos = nrow(estudos), n_teste_calibracao = nrow(teste),
  pacotes = as.list(versions), dados_clinicos = FALSE,
  registro = "governance synthetic demonstration; not a scientific project"
)
jsonlite::write_json(prov, file.path(out_root, "manifesto_execucao_sintetica.json"),
  auto_unbox = TRUE, pretty = TRUE)
writeLines(capture.output(utils::sessionInfo()),
  file.path(model_root, "ambiente", "sessao_r_2026-11-02.txt"), useBytes = TRUE)
cat("PASS: synthetic bilingual figures and tables generated. No clinical data or claims.\n")




