# Compila o livro em ../docs/ (pronto para o GitHub Pages) e anexa os slides
# e um .zip com o material completo. Rode a partir da pasta livro/:
#   setwd("livro"); source("build.R")
bookdown::render_book("index.Rmd", quiet = TRUE)

docs <- normalizePath("../docs")
file.create(file.path(docs, ".nojekyll"))
dir.create(file.path(docs, "slides"), showWarnings = FALSE)
# Todos os decks: versão resumida, Parte 1 (conceitos) e minicurso completo em R e em Python.
# Compile-os antes (quarto render slides/<deck>.qmd); os PDFs, se existirem, também são copiados.
decks <- c("slides", "parte1_conceitos", "completo_R", "completo_python")
for (d in decks) for (ext in c(".html", ".pdf")) {
  orig <- file.path("../slides", paste0(d, ext))
  if (file.exists(orig)) file.copy(orig, file.path(docs, "slides", paste0(d, ext)), overwrite = TRUE)
  else if (ext == ".html") warning("Deck não compilado: ", orig)
}

# Material para reprodução: só códigos, dados, prompts e resultados de referência
# (sem slides, sem fontes do livro, sem roteiro do ministrante, sem caches locais)
dir.create(file.path(docs, "material"), showWarnings = FALSE)
zip_destino <- file.path(docs, "material/minicurso_IA_medicao.zip")
unlink(zip_destino)
raiz <- normalizePath("..")
arquivos <- list.files(raiz, recursive = TRUE, all.files = TRUE)
incluir <- "^(README\\.md|LICENSE(\\.md)?|CODEBOOK\\.md|CHECKLIST\\.md|requirements\\.txt|_targets\\.R|\\.gitignore)$|^(R|python|dados|prompts|modelos|material_apoio|resultados)/"
arquivos <- arquivos[grepl(incluir, arquivos)]
arquivos <- arquivos[!grepl("__pycache__|\\.ipynb_checkpoints|^material_apoio/respostas/", arquivos)]
withr::with_dir(raiz, zip(zip_destino, arquivos, flags = "-q9"))
message("Livro em ", docs)
