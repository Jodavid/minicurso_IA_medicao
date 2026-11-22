# =============================================================================
# BLOCO 2a — Amostra-ouro: o "padrão" contra o qual o LLM será medido
#
# Ideia central: um LLM só pode ser avaliado contra uma referência humana
# construída com um livro de códigos (CODEBOOK.md). Sorteamos uma amostra
# ALEATÓRIA (não a "mais fácil", não a "mais interessante") para que as
# estimativas de erro valham para o corpus todo.
# =============================================================================

library(dplyr)
library(readr)

N_OURO   <- 120     # ~40% do corpus: custo humano × precisão (ver Bloco 5)
N_EXERC  <- 20      # ementas para o exercício de codificação ao vivo
SEMENTE  <- 2026

corpus     <- read_csv("dados/processado/corpus.csv", show_col_types = FALSE)
referencia <- read_csv("dados/anotacoes/referencia_completa.csv", show_col_types = FALSE)

set.seed(SEMENTE)
ouro_ids <- sample(corpus$doc_id, N_OURO)

amostra_ouro <- referencia |>
  filter(doc_id %in% ouro_ids) |>
  arrange(doc_id)
write_csv(amostra_ouro, "dados/anotacoes/amostra_ouro.csv")

# Exercício em sala: participantes codificam às cegas (sem ver a referência)
set.seed(SEMENTE + 1)
exercicio <- corpus |>
  filter(doc_id %in% ouro_ids) |>
  slice_sample(n = N_EXERC) |>
  transmute(doc_id, ementa, categoria = "", eleitoral = "")
write_csv(exercicio, "material_apoio/exercicio_codificacao.csv")

message("Amostra-ouro: ", nrow(amostra_ouro), " ementas; exercício: ", nrow(exercicio))
print(count(amostra_ouro, categoria))
