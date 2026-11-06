# Instala somente as dependências diretas e transitivas necessárias ao modelo.
# Fontes: CRAN oficial; versão/licença/dependências consultadas em 2026-11-02.
args <- commandArgs(trailingOnly = TRUE)
script_arg <- grep("^--file=", commandArgs(), value = TRUE)
script_path <- sub("^--file=", "", script_arg[[1]])
model_root <- normalizePath(file.path(dirname(script_path), ".."), winslash = "/", mustWork = TRUE)
lib <- file.path(model_root, "ambiente", "biblioteca")
dir.create(lib, recursive = TRUE, showWarnings = FALSE)
options(repos = c(CRAN = "https://cran.r-project.org"))
.libPaths(c(lib, .Library.site, .Library))
pacotes <- c("ggplot2", "patchwork", "gtsummary", "gt", "flextable",
             "officer", "ragg", "svglite", "metafor", "jsonlite")
db <- available.packages()
print(db[pacotes, c("Version", "License", "Depends", "Imports"), drop = FALSE])
deps <- tools::package_dependencies(pacotes, db = db,
  which = c("Depends", "Imports", "LinkingTo"), recursive = TRUE)
closure <- unique(c(pacotes, unlist(deps, use.names = FALSE)))
closure <- intersect(closure, rownames(db))
installed_local <- rownames(installed.packages(lib.loc = lib))
installed_system <- installed.packages(lib.loc = .Library)
system_core <- installed_system[!is.na(installed_system[, "Priority"]) &
  installed_system[, "Priority"] %in% c("base", "recommended"), "Package"]
to_install <- setdiff(closure, c(installed_local, system_core))
cat("Pacotes principais:", length(pacotes), "; dependências obrigatórias da pilha:", length(closure),
    "; novas instalações locais nesta execução:", length(to_install), "\n")
if (length(to_install)) {
  install.packages(to_install, lib = lib, dependencies = FALSE, type = "binary")
}
.libPaths(c(lib, .Library.site, .Library))
faltam <- pacotes[!vapply(pacotes, requireNamespace, logical(1), quietly = TRUE)]
if (length(faltam)) stop("Pacotes principais ausentes após instalação: ", paste(faltam, collapse = ", "))
renv::snapshot(project = model_root, library = lib,
  lockfile = file.path(model_root, "ambiente", "renv.lock"),
  type = "all", prompt = FALSE, force = TRUE)
writeLines(capture.output(utils::sessionInfo()),
  file.path(model_root, "ambiente", "sessao_r_2026-11-02.txt"), useBytes = TRUE)
cat("PASS: dependências obrigatórias instaladas localmente e lockfile renv gerado.\n")
