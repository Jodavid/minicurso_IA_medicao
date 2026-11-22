# =============================================================================
# BLOCO 5 — Inferência com rótulos imperfeitos
#
# Pergunta substantiva: que proporção dos projetos sobre IA quer PUNIR?
# E essa proporção difere entre campos políticos?
#
# Quatro estimadores:
#   (a) Só humanos: usa apenas a amostra-ouro (sem viés, IC largo)
#   (b) Ingênuo: trata o LLM como verdade no corpus todo (IC estreito... e errado?)
#   (c) PPI: LLM no corpus todo, corrigido pelo erro medido na amostra-ouro
#   (d) PPI++: como (c), mas pondera o LLM conforme sua qualidade
#
# Como este é um corpus didático com referência completa (298 ementas), sabemos
# a "verdade" e podemos checar quem acerta, e com que frequência (simulação).
# =============================================================================

source("R/funcoes_medicao.R")
source("R/tema_graficos.R")

corpus <- carrega_corpus()
ouro   <- carrega_ouro()
ref    <- read_csv("dados/anotacoes/referencia_completa.csv", show_col_types = FALSE)
llm    <- carrega_llm()

# Instrumento escolhido no Bloco 4 (melhor kappa com temperatura 0)
validade <- read_csv("resultados/tabelas/validade_instrumentos.csv", show_col_types = FALSE)
PROMPT <- validade |> filter(str_detect(instrumento, "^LLM v\\d \\(t=0\\)")) |>
  slice_max(kappa, n = 1) |> pull(instrumento) |> str_extract("v\\d")
message("Instrumento usado: s5-nano-instruct, prompt ", PROMPT, ", temperatura 0")

dados <- corpus |>
  select(doc_id, ano, campo, casa) |>
  left_join(llm |> filter(prompt_id == PROMPT, temperatura == 0, semente == 42) |>
              select(doc_id, categoria_llm), by = "doc_id") |>
  left_join(select(ref, doc_id, categoria_ref = categoria), by = "doc_id") |>
  mutate(
    na_ouro = doc_id %in% ouro$doc_id,
    f = as.integer(categoria_llm %in% "PUNIR"),    # falha de formato conta como "não PUNIR"
    y = if_else(na_ouro, as.integer(categoria_ref == "PUNIR"), NA_integer_)
  )

verdade <- mean(ref$categoria == "PUNIR")

# --- 5.1 Proporção de projetos punitivos --------------------------------------
lab <- filter(dados, na_ouro); unl <- filter(dados, !na_ouro)
est <- compara_estimadores(lab$y, lab$f, unl$f) |> mutate(verdade = verdade)
print(est)
write_csv(est, "resultados/tabelas/estimativas_punir.csv")

g5 <- est |>
  mutate(estimador = factor(estimador, levels = rev(unique(estimador)))) |>
  ggplot(aes(estimativa, estimador)) +
  geom_vline(xintercept = verdade, colour = CINZA_ESCURO, linewidth = .8, linetype = 2) +
  geom_linerange(aes(xmin = li, xmax = ls, colour = estimador), linewidth = 2) +
  geom_point(aes(colour = estimador), size = 3.5) +
  scale_colour_manual(values = COR_EST, guide = "none") +
  ggplot2::annotate("text", x = verdade, y = 4.45, label = "valor na referência completa",
                    colour = TINTA2, hjust = -0.05, size = 3.6) +
  scale_x_continuous(labels = scales::percent) +
  labs(title = "Que proporção dos projetos sobre IA quer PUNIR?",
       subtitle = sprintf("Estimativas com IC 95%% · amostra-ouro n = %d · não rotulados N = %d",
                          nrow(lab), nrow(unl)),
       x = "Proporção de projetos PUNIR", y = NULL) +
  tema_minicurso()
salva_fig(g5, "05_estimadores_punir", h = 4.2)

# --- 5.2 Diferença entre campos políticos (Direita − Esquerda) ----------------
por_campo <- dados |>
  filter(campo %in% c("Esquerda", "Centro", "Direita")) |>
  group_by(campo) |>
  group_modify(\(d, ...) {
    l <- filter(d, na_ouro); u <- filter(d, !na_ouro)
    compara_estimadores(l$y, l$f, u$f) |>
      mutate(n_ouro = nrow(l), verdade = mean(d$categoria_ref == "PUNIR"))
  }) |> ungroup()
print(por_campo, n = Inf)
write_csv(por_campo, "resultados/tabelas/estimativas_punir_campo.csv")

g6 <- por_campo |>
  filter(estimador != "PPI++") |>
  mutate(estimador = factor(estimador, levels = c("Só humanos (amostra-ouro)", "Ingênuo (LLM = verdade)", "PPI"))) |>
  ggplot(aes(estimativa, estimador, colour = estimador)) +
  geom_vline(aes(xintercept = verdade), colour = CINZA_ESCURO, linewidth = .7, linetype = 2) +
  geom_linerange(aes(xmin = pmax(li, 0), xmax = ls), linewidth = 2) +
  geom_point(size = 3) +
  facet_wrap(~ campo, ncol = 1) +
  scale_colour_manual(values = COR_EST, guide = "none") +
  scale_x_continuous(labels = scales::percent) +
  scale_y_discrete(limits = rev) +
  labs(title = "Proporção de projetos PUNIR por campo político do autor",
       subtitle = "Linha tracejada: valor na referência completa · IC 95%",
       x = NULL, y = NULL) +
  tema_minicurso()
salva_fig(g6, "06_punir_por_campo", h = 6.5)

# --- 5.3 Simulação: cobertura e largura dos ICs --------------------------------
# Repetimos o sorteio da amostra-ouro muitas vezes. Um bom IC de 95% deve
# conter a verdade em ~95% das repetições.
simula <- function(n_ouro, B = 1000, semente = 1) {
  set.seed(semente)
  map(seq_len(B), \(b) {
    idx <- sample(nrow(dados), n_ouro)
    y_n <- as.integer(dados$categoria_ref[idx] == "PUNIR")
    compara_estimadores(y_n, dados$f[idx], dados$f[-idx])
  }) |>
    list_rbind() |>
    group_by(estimador) |>
    summarise(cobertura = mean(li <= verdade & verdade <= ls),
              largura_media = mean(ls - li),
              vies = mean(estimativa) - verdade, .groups = "drop") |>
    mutate(n_ouro = n_ouro)
}
sim <- map(c(30, 60, 120), simula) |> list_rbind()
print(sim, n = Inf)
write_csv(sim, "resultados/tabelas/simulacao_cobertura.csv")

g7 <- sim |>
  mutate(estimador = factor(estimador, levels = unique(est$estimador))) |>
  ggplot(aes(factor(n_ouro), cobertura, colour = estimador, group = estimador)) +
  geom_hline(yintercept = .95, colour = TINTA2, linetype = 2) +
  geom_line(linewidth = 1) + geom_point(size = 3) +
  scale_colour_manual(values = COR_EST) +
  scale_y_continuous(labels = scales::percent, limits = c(0, 1)) +
  labs(title = "Com que frequência o IC de 95% contém a verdade?",
       subtitle = "1.000 sorteios da amostra-ouro para cada tamanho · linha tracejada = 95%",
       x = "Tamanho da amostra-ouro (ementas codificadas por humanos)", y = "Cobertura", colour = NULL) +
  guides(colour = guide_legend(nrow = 2)) +
  tema_minicurso()
salva_fig(g7, "07_cobertura_simulacao", h = 5)

g8 <- sim |>
  mutate(estimador = factor(estimador, levels = unique(est$estimador))) |>
  ggplot(aes(factor(n_ouro), largura_media, colour = estimador, group = estimador)) +
  geom_line(linewidth = 1) + geom_point(size = 3) +
  scale_colour_manual(values = COR_EST) +
  scale_y_continuous(labels = scales::percent) +
  labs(title = "Preço da honestidade: largura média do IC de 95%",
       subtitle = "O ingênuo é estreito porque ignora o erro do LLM; PPI aproveita o LLM sem esconder o erro",
       x = "Tamanho da amostra-ouro", y = "Largura média do IC", colour = NULL) +
  guides(colour = guide_legend(nrow = 2)) +
  tema_minicurso()
salva_fig(g8, "08_largura_simulacao", h = 5)

# --- 5.4 Retrato descritivo: a explosão legislativa sobre IA ------------------
g9 <- corpus |>
  left_join(select(ref, doc_id, categoria), by = "doc_id") |>
  filter(ano >= 2023) |>
  count(ano, categoria = factor(categoria, levels = CATEGORIAS)) |>
  # Um painel por categoria; PUNIR (a pergunta do minicurso) em azul, o resto em cinza
  ggplot(aes(factor(ano), n, fill = categoria == "PUNIR")) +
  geom_col(width = .7) +
  facet_wrap(~categoria, nrow = 1) +
  scale_fill_manual(values = c(`TRUE` = AZUIS[3], `FALSE` = CINZA_CLARO), guide = "none") +
  scale_y_continuous(expand = expansion(mult = c(0, .05))) +
  labs(title = "Projetos de lei sobre IA no Congresso (Câmara + Senado)",
       subtitle = sprintf("Por ano de apresentação e categoria (referência) · 2019–2022: %d projetos · 2026 até a coleta",
                          sum(corpus$ano < 2023)),
       x = NULL, y = "Projetos", fill = NULL,
       caption = "Fonte: APIs de Dados Abertos da Câmara dos Deputados e do Senado Federal.") +
  tema_minicurso() +
  theme(panel.grid.major.x = element_blank(), strip.text = element_text(face = "bold", hjust = 0))
salva_fig(g9, "00_projetos_por_ano", h = 4.8)
