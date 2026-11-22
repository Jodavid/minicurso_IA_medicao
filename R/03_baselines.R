# =============================================================================
# BLOCO 2b — Baselines clássicos: antes de usar um LLM, quanto se acerta sem ele?
#
#   (1) Dicionário: regras explícitas (regex). Barato, transparente, auditável.
#   (2) TF-IDF + regressão logística multinomial com penalização (glmnet),
#       avaliada com validação cruzada na amostra-ouro (n = 120).
#
# Mensagem: um LLM só "vale a pena" se superar esses baselines de forma
# consistente, e isso é uma afirmação estatística, não uma impressão.
# =============================================================================

source("R/funcoes_medicao.R")
library(tm)
library(glmnet)

corpus <- carrega_corpus()
ouro   <- carrega_ouro() |> left_join(select(corpus, doc_id, ementa), by = "doc_id")

# --- (1) Dicionário ----------------------------------------------------------
# ATENÇÃO (ponto para discussão): as regras de REGEX foram escritas depois de LER
# as ementas do corpus. O dicionário "viu a prova" e seu desempenho aqui é
# otimista. Num estudo real, as regras são definidas antes, ou validadas em
# dados novos (ex.: proposições apresentadas depois da data de coleta).
ouro <- ouro |> mutate(pred_dic = classifica_dicionario(ementa))
met_dic <- resumo_metricas(ouro$categoria, ouro$pred_dic)
print(met_dic)
print(table(humano = ouro$categoria, dicionario = ouro$pred_dic))

# --- (2) TF-IDF + logística multinomial (validação cruzada 10-fold) ----------
prepara_dtm <- function(textos) {
  vc <- VCorpus(VectorSource(str_to_lower(textos)))
  vc <- tm_map(vc, removePunctuation)
  vc <- tm_map(vc, removeNumbers)
  vc <- tm_map(vc, removeWords, stopwords("portuguese"))
  vc <- tm_map(vc, stemDocument, language = "portuguese")
  vc <- tm_map(vc, stripWhitespace)
  DocumentTermMatrix(vc, control = list(weighting = weightTfIdf, bounds = list(global = c(2, Inf))))
}

dtm <- prepara_dtm(ouro$ementa)
X <- as.matrix(dtm)
y <- factor(ouro$categoria, levels = CATEGORIAS)

set.seed(2026)
dobras <- sample(rep(1:10, length.out = nrow(X)))
pred_ml <- factor(rep(NA, nrow(X)), levels = CATEGORIAS)
for (k in 1:10) {
  treino <- dobras != k
  fit <- cv.glmnet(X[treino, ], y[treino], family = "multinomial", alpha = 0.5,
                   nfolds = 5, type.measure = "class")
  pred_ml[!treino] <- predict(fit, X[!treino, , drop = FALSE], s = "lambda.min", type = "class")
}
ouro$pred_ml <- pred_ml
met_ml <- resumo_metricas(ouro$categoria, ouro$pred_ml)

baselines <- bind_rows(
  "Dicionário (regex)"           = met_dic,
  "TF-IDF + logística (CV 10)"   = met_ml,
  "Classe majoritária (REGULAR)" = resumo_metricas(ouro$categoria, factor(rep("REGULAR", nrow(ouro)), levels = CATEGORIAS)),
  .id = "metodo"
)
print(baselines)

write_csv(baselines, "resultados/tabelas/baselines.csv")
write_csv(select(ouro, doc_id, categoria, pred_dic, pred_ml), "dados/anotacoes/predicoes_baselines.csv")

# Dicionário aplicado a TODO o corpus (usado como "instrumento barato" no Bloco 5)
corpus |>
  transmute(doc_id, categoria_dic = classifica_dicionario(ementa),
            eleitoral_dic = eleitoral_dicionario(ementa)) |>
  write_csv("dados/anotacoes/dicionario_corpus.csv")
