# =============================================================================
# Funções de medição, validação e inferência
# Implementadas "na mão" de propósito: são poucas linhas e mostram que não há
# mágica nas métricas. Em pesquisa, compare com pacotes (irr, krippendorffsalpha,
# ipd, ppi_py) para conferir os resultados.
# =============================================================================

library(dplyr)
library(tidyr)
library(purrr)
library(readr)
library(stringr)
library(jsonlite)

CATEGORIAS <- c("PUNIR", "REGULAR", "PROMOVER", "OUTRO")
# Instrumento oficial do minicurso: só os caches dele entram nas análises
# (caches de outros modelos, se existirem na pasta, são ignorados)
INSTRUMENTO <- "s5-nano-instruct"

# -----------------------------------------------------------------------------
# Leitura dos dados
# -----------------------------------------------------------------------------
carrega_corpus <- function(raiz = ".") {
  read_csv(file.path(raiz, "dados/processado/corpus.csv"), show_col_types = FALSE)
}

carrega_ouro <- function(raiz = ".") {
  ouro <- read_csv(file.path(raiz, "dados/anotacoes/amostra_ouro.csv"), show_col_types = FALSE)
  if (!any(ouro$revisado)) {
    warning("A amostra-ouro ainda NÃO foi revisada por humanos (coluna `revisado`). ",
            "Os resultados são ilustrativos.", call. = FALSE)
  }
  ouro
}

carrega_llm <- function(raiz = ".", modelo = INSTRUMENTO) {
  arqs <- list.files(file.path(raiz, "dados/cache_llm"), paste0("^", modelo, "__.*\\.jsonl$"), full.names = TRUE)
  map(arqs, \(a) stream_in(file(a), verbose = FALSE)) |>
    list_rbind() |>
    as_tibble() |>
    mutate(categoria_llm = factor(categoria_llm, levels = CATEGORIAS))
}

# -----------------------------------------------------------------------------
# Baseline de dicionário (regras explícitas, totalmente auditáveis)
# -----------------------------------------------------------------------------
REGEX <- list(
  punir    = "c[oó]digo penal|\\bpenas?\\b|\\bcrimes?\\b|criminaliz|tipific|hediond",
  ia       = paste0("intelig[eê]ncia artificial|\\bia\\b|algor[ií]tm|automatiz|automa[cç][aã]o|",
                    "sint[eé]tic|deep ?fake|deepvoice|manipula|chatbot|reconhecimento facial|",
                    "aut[oô]nom|\\binteligente|réplicas? digit|simul"),
  promover = paste0("incentiv|fomento|\\bfundo\\b|curr[ií]cul|ensino|educa[cç]|capacita|",
                    "forma[cç][aã]o|pesquisa|desenvolvimento da|programa nacional|institui o sistema|",
                    "obrigatoriedade d[eo] uso|utiliza[cç][aã]o de (ferramentas|tecnologias|sistemas)"),
  eleitoral = "elei[cç]|eleitora|campanhas? eleitora|candidat|propaganda pol|democr|violência política"
)

classifica_dicionario <- function(ementa) {
  x <- str_to_lower(ementa)
  case_when(
    str_detect(x, REGEX$punir) & str_detect(x, REGEX$ia) ~ "PUNIR",
    !str_detect(x, REGEX$ia)                               ~ "OUTRO",
    str_detect(x, REGEX$promover)                          ~ "PROMOVER",
    TRUE                                                   ~ "REGULAR"
  ) |> factor(levels = CATEGORIAS)
}

eleitoral_dicionario <- function(ementa) str_detect(str_to_lower(ementa), REGEX$eleitoral)

# -----------------------------------------------------------------------------
# Métricas de acerto e concordância
# -----------------------------------------------------------------------------
kappa_cohen <- function(a, b) {
  ok <- !is.na(a) & !is.na(b)
  a <- factor(a[ok], levels = CATEGORIAS); b <- factor(b[ok], levels = CATEGORIAS)
  tab <- table(a, b)
  n <- sum(tab)
  po <- sum(diag(tab)) / n
  pe <- sum(rowSums(tab) * colSums(tab)) / n^2
  (po - pe) / (1 - pe)
}

# Alfa de Krippendorff (nominal) para k codificadores, aceita NA.
# `m` é uma matriz unidades × codificadores.
alfa_krippendorff <- function(m) {
  m <- as.matrix(m)
  valores <- sort(unique(na.omit(as.vector(m))))
  o <- matrix(0, length(valores), length(valores), dimnames = list(valores, valores))
  for (u in seq_len(nrow(m))) {
    v <- na.omit(m[u, ])
    mu <- length(v)
    if (mu < 2) next
    for (i in seq_len(mu)) for (j in seq_len(mu)) {
      if (i != j) o[v[i], v[j]] <- o[v[i], v[j]] + 1 / (mu - 1)
    }
  }
  nc <- rowSums(o); n <- sum(o)
  Do <- (n - sum(diag(o))) / n
  De <- (n^2 - sum(nc^2)) / (n * (n - 1))
  1 - Do / De
}

f1_macro <- function(verdade, pred) {
  map_dbl(CATEGORIAS, \(c) {
    tp <- sum(pred == c & verdade == c, na.rm = TRUE)
    fp <- sum(pred == c & verdade != c, na.rm = TRUE)
    fn <- sum(pred != c & verdade == c, na.rm = TRUE)
    if (tp == 0) return(0)
    2 * tp / (2 * tp + fp + fn)
  }) |> mean()
}

resumo_metricas <- function(verdade, pred) {
  tibble(
    n = sum(!is.na(verdade)),
    falhas_formato = mean(is.na(pred)),
    acuracia = mean(as.character(pred) == as.character(verdade), na.rm = TRUE),
    f1_macro = f1_macro(as.character(verdade), as.character(pred)),
    kappa = kappa_cohen(verdade, pred)
  )
}

# Intervalo bootstrap percentil para qualquer métrica de (verdade, pred)
boot_ic <- function(verdade, pred, fun = kappa_cohen, B = 2000, semente = 2026) {
  set.seed(semente)
  n <- length(verdade)
  est <- replicate(B, { i <- sample.int(n, n, replace = TRUE); fun(verdade[i], pred[i]) })
  quantile(est, c(.025, .975), na.rm = TRUE)
}

# -----------------------------------------------------------------------------
# Inferência com rótulos imperfeitos
#   y_n : rótulo humano (0/1) na amostra-ouro (n)
#   f_n : rótulo do LLM (0/1) na amostra-ouro
#   f_N : rótulo do LLM (0/1) nos documentos NÃO rotulados (N)
# -----------------------------------------------------------------------------
ic_normal <- function(est, ep, nivel = .95) {
  z <- qnorm(1 - (1 - nivel) / 2)
  tibble(estimativa = est, ep = ep, li = est - z * ep, ls = est + z * ep)
}

# (a) Só humanos: média da amostra-ouro (sem viés, mas com pouca precisão)
est_humano <- function(y_n) ic_normal(mean(y_n), sd(y_n) / sqrt(length(y_n)))

# (b) Ingênuo: trata o rótulo do LLM como verdade em TODO o corpus
est_ingenuo <- function(f_todos) ic_normal(mean(f_todos), sd(f_todos) / sqrt(length(f_todos)))

# (c) Prediction-Powered Inference (Angelopoulos et al., 2023, Science)
#     estimativa = média do LLM no não rotulado - viés do LLM medido na amostra-ouro
est_ppi <- function(y_n, f_n, f_N) {
  retificador <- f_n - y_n
  est <- mean(f_N) - mean(retificador)
  ep <- sqrt(var(f_N) / length(f_N) + var(retificador) / length(y_n))
  ic_normal(est, ep)
}

# (d) PPI++ (Angelopoulos, Duchi & Zrnic, 2023): ajusta o peso λ do LLM.
#     Se o LLM for ruim, λ → 0 e o estimador volta a ser o "só humanos".
est_ppi_plus <- function(y_n, f_n, f_N) {
  n <- length(y_n); N <- length(f_N)
  f_todos <- c(f_n, f_N)
  lambda <- cov(y_n, f_n) / ((1 + n / N) * var(f_todos))
  lambda <- min(max(lambda, 0), 1)
  est <- mean(y_n) + lambda * (mean(f_N) - mean(f_n))
  ep <- sqrt(var(y_n - lambda * f_n) / n + lambda^2 * var(f_N) / N)
  ic_normal(est, ep) |> mutate(lambda = lambda)
}

compara_estimadores <- function(y_n, f_n, f_N) {
  bind_rows(
    "Só humanos (amostra-ouro)" = est_humano(y_n),
    "Ingênuo (LLM = verdade)"   = est_ingenuo(c(f_n, f_N)),
    "PPI"                       = est_ppi(y_n, f_n, f_N),
    "PPI++"                     = est_ppi_plus(y_n, f_n, f_N),
    .id = "estimador"
  )
}
