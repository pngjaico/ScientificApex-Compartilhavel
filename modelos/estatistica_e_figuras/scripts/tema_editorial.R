# Modulo compartilhado de identidade visual cientifica (R 4.6.1)
# Uso: source("analysis/tema_editorial.R") ou source("scripts/tema_editorial.R")
# Fornece paleta Okabe-Ito estendida, tema_editorial() sem cortes de margem
# e salvar_par_figura() para exportacao bilingue simultanea em PNG 300 DPI (ragg) e SVG (svglite).

paleta_editorial_doutorado <- c(
  blue   = "#0072B2",
  orange = "#D55E00",
  green  = "#009E73",
  purple = "#CC79A7",
  amber  = "#E69F00",
  sky    = "#56B4E9",
  navy   = "#1B365D",
  slate  = "#4A5568",
  grey   = "#718096"
)

tema_editorial_doutorado <- function(base_size = 11.5) {
  ggplot2::theme_minimal(base_size = base_size, base_family = "sans") +
    ggplot2::theme(
      plot.background = ggplot2::element_rect(fill = "white", color = NA),
      panel.background = ggplot2::element_rect(fill = "white", color = NA),
      panel.grid.minor = ggplot2::element_blank(),
      panel.grid.major.y = ggplot2::element_line(color = "#EDF2F7", linewidth = 0.45),
      panel.grid.major.x = ggplot2::element_line(color = "#EDF2F7", linewidth = 0.45),
      axis.line.x = ggplot2::element_line(color = "#2D3748", linewidth = 0.45),
      axis.ticks.x = ggplot2::element_line(color = "#2D3748", linewidth = 0.35),
      axis.title = ggplot2::element_text(face = "bold", color = "#1A202C", size = base_size),
      axis.text = ggplot2::element_text(color = "#2D3748", size = base_size - 1),
      plot.title = ggplot2::element_text(face = "bold", color = "#0F172A", size = base_size + 2, margin = ggplot2::margin(b = 3)),
      plot.subtitle = ggplot2::element_text(color = "#475569", size = base_size - 0.8, margin = ggplot2::margin(b = 8)),
      plot.caption = ggplot2::element_text(color = "#64748B", size = base_size - 2.2, hjust = 0, margin = ggplot2::margin(t = 8)),
      plot.title.position = "plot",
      plot.caption.position = "plot",
      legend.position = "bottom",
      legend.background = ggplot2::element_rect(fill = "white", color = NA),
      legend.title = ggplot2::element_text(face = "bold", size = base_size - 1),
      legend.text = ggplot2::element_text(size = base_size - 1.2),
      strip.text = ggplot2::element_text(face = "bold", color = "#0F172A", size = base_size),
      plot.margin = ggplot2::margin(10, 14, 10, 10)
    )
}

salvar_par_figura_bilingue <- function(plot_pt, plot_en, pt_dir, en_dir, nome_base, width = 13.5, height = 6.5, dpi = 300) {
  dir.create(pt_dir, recursive = TRUE, showWarnings = FALSE)
  dir.create(en_dir, recursive = TRUE, showWarnings = FALSE)
  for (info in list(list(p = plot_pt, d = pt_dir), list(p = plot_en, d = en_dir))) {
    ggplot2::ggsave(
      filename = file.path(info$d, paste0(nome_base, ".png")),
      plot = info$p,
      device = ragg::agg_png,
      width = width,
      height = height,
      units = "in",
      dpi = dpi,
      bg = "white"
    )
    ggplot2::ggsave(
      filename = file.path(info$d, paste0(nome_base, ".svg")),
      plot = info$p,
      device = svglite::svglite,
      width = width,
      height = height,
      units = "in",
      bg = "white"
    )
  }
}
