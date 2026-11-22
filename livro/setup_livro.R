# Configuração comum a todos os capítulos. Os números do livro são lidos das
# tabelas geradas pelo pipeline (targets::tar_make()), como nos slides: se a
# referência for revisada e o pipeline rodar de novo, o livro se atualiza.
knitr::opts_chunk$set(echo = FALSE, message = FALSE, warning = FALSE,
                      fig.align = "center", out.width = "100%", comment = "")
options(knitr.kable.NA = "")
# No PDF, tabelas em Markdown (pipe) para que negrito/código nas células sejam renderizados
if (knitr::is_latex_output()) options(knitr.table.format = "pipe")
suppressPackageStartupMessages({ library(readr); library(dplyr); library(stringr) })

LIVRO <- getwd()                      # pasta livro/
RAIZ  <- normalizePath("..")          # raiz do projeto

# Os chunks "Mão na massa" rodam a partir da RAIZ do projeto, como o aluno roda
# (caminhos como "dados/processado/corpus.csv"); vale também para os chunks Python,
# que rodam no mesmo processo (reticulate). As funções auxiliares abaixo usam
# caminhos absolutos, por isso não dependem do diretório de trabalho.
knitr::opts_knit$set(root.dir = RAIZ)

# Python (via reticulate) para os blocos "Em Python". Para usar outro interpretador:
#   Sys.setenv(PYTHON_LIVRO = "/caminho/para/python") antes de compilar.
ld_original <- Sys.getenv("LD_LIBRARY_PATH")
py_livro <- Sys.getenv("PYTHON_LIVRO", "/home/jodavid/anaconda3/bin/python")
if (file.exists(py_livro)) reticulate::use_python(py_livro, required = TRUE)
reticulate::py_run_string(sprintf(paste(
  "import os, sys, warnings",
  "sys.path.insert(0, os.path.join(r'%s', 'python'))",
  "warnings.filterwarnings('ignore')",
  "import matplotlib; matplotlib.use('Agg')",
  "import pandas as pd",
  "pd.set_option('display.width', 100); pd.set_option('display.max_columns', 12)",
  "pd.set_option('display.max_colwidth', 60)",
  sep = "\n"), RAIZ))
# O reticulate põe as bibliotecas do Python no LD_LIBRARY_PATH; os processos-filhos
# do R (ex.: o callr usado pelo targets) não precisam delas e reclamam de versões.
Sys.setenv(LD_LIBRARY_PATH = ld_original)
le   <- function(...) read_csv(file.path(RAIZ, ...), show_col_types = FALSE)
tab  <- function(f) le("resultados/tabelas", f)

corpus    <- le("dados/processado/corpus.csv")
ref       <- le("dados/anotacoes/referencia_completa.csv")
ouro      <- le("dados/anotacoes/amostra_ouro.csv")
val       <- tab("validade_instrumentos.csv")
base      <- tab("baselines.csv")
base_py   <- le("resultados/python/tabelas/baselines.csv")
conf      <- tab("confiabilidade.csv")
est       <- tab("estimativas_punir.csv")
est_campo <- tab("estimativas_punir_campo.csv")
sim       <- tab("simulacao_cobertura.csv")
vies      <- tab("vies_diferencial_campo.csv")
ele       <- tab("validade_eleitoral.csv")

pc <- function(x, d = 0) paste0(format(round(100 * x, d), nsmall = d, decimal.mark = ","), "%")
nf <- function(x, d = 2) format(round(x, d), nsmall = d, decimal.mark = ",")
k  <- function(nome) val$kappa[val$instrumento == nome]
e  <- function(nome, col = "estimativa") est[[col]][est$estimador == nome]
cob <- function(nome, n) sim$cobertura[sim$estimador == nome & sim$n_ouro == n]
verdade <- est$verdade[1]
melhor_llm <- val |> filter(str_detect(instrumento, "^LLM v\\d \\(t=0\\)")) |> slice_max(kappa, n = 1)

# Copia uma figura do pipeline para dentro do livro e a inclui
fig <- function(nome) {
  dir.create(file.path(LIVRO, "img"), showWarnings = FALSE)
  arq <- paste0(nome, ".png")
  file.copy(file.path(RAIZ, "resultados/figuras", arq), file.path(LIVRO, "img", arq), overwrite = TRUE)
  # caminho relativo à pasta livro/ (os chunks rodam na raiz, por isso error = FALSE)
  knitr::include_graphics(file.path("img", arq), error = FALSE)
}

# Extrai do código-fonte do minicurso uma função de nível superior (com comentários),
# para que o livro mostre exatamente o código que roda
trecho <- function(arquivo, funcao) {
  linhas <- readLines(file.path(RAIZ, arquivo), encoding = "UTF-8")
  ini <- grep(paste0("^", funcao, " <- function"), linhas)[1]
  fim <- ini - 1 + which(grepl("^\\}", linhas[ini:length(linhas)]))[1]
  linhas[ini:fim]
}

# Insere um arquivo Markdown do repositório (sem o título de nível 1)
inclui_md <- function(arquivo) {
  linhas <- readLines(file.path(RAIZ, arquivo), encoding = "UTF-8")
  linhas <- linhas[!grepl("^# ", linhas)]
  cat(sub("^##", "###", linhas), sep = "\n")
}

# No PDF, o pandoc define a largura das colunas pela quantidade de traços da linha
# separadora da tabela; `larguras()` fixa essas proporções (ex.: c(15, 55, 30)).
larguras <- function(k, w) {
  if (!knitr::is_latex_output()) return(k)
  i <- grep("^\\|?[-:| ]+\\|?$", k)[1]
  seg <- strsplit(gsub("^\\||\\|$", "", k[i]), "\\|")[[1]]
  k[i] <- paste0("|", paste0(mapply(\(s, n) paste0(if (startsWith(s, ":")) ":" else "-", strrep("-", n),
                                                     if (endsWith(s, ":")) ":" else "-"), seg, w),
                            collapse = "|"), "|")
  k
}
