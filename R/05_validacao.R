# =============================================================================
# BLOCO 4 — Validação: o instrumento mede o que diz medir? Com que erro?
#
#   4.1 Validade: concordância com a amostra-ouro (acurácia, F1, kappa + IC)
#   4.2 Onde erra: matriz de confusão
#   4.3 Viés diferencial: o erro é igual entre campos políticos e casas?
#   4.4 Confiabilidade: teste-reteste (sementes) e sensibilidade ao prompt
#   4.5 Concordância humano × humano (exercício em sala)
# =============================================================================

source("R/funcoes_medicao.R")
source("R/tema_graficos.R")

corpus <- carrega_corpus()
ouro   <- carrega_ouro()
llm    <- carrega_llm()
base_l <- read_csv("dados/anotacoes/predicoes_baselines.csv", show_col_types = FALSE)

rotulo_run <- function(run_id) {
  p <- str_match(run_id, "__(v\\d)__t([0-9.]+)__s(\\d+)")
  # semente 42 com t = 0 é a configuração principal; qualquer outra aparece explícita
  ifelse(p[, 3] == "0.0" & p[, 4] == "42", paste0("LLM ", p[, 2], " (t=0)"),
         paste0("LLM ", p[, 2], " (t=", p[, 3], ", s=", p[, 4], ")"))
}
llm <- llm |> mutate(instrumento = rotulo_run(run_id))

# --- 4.1 Validade ------------------------------------------------------------
aval <- llm |>
  inner_join(select(ouro, doc_id, categoria), by = "doc_id")

metricas_llm <- aval |>
  group_by(instrumento) |>
  group_modify(\(d, ...) {
    ic <- boot_ic(d$categoria, d$categoria_llm)
    resumo_metricas(d$categoria, d$categoria_llm) |>
      mutate(kappa_li = ic[1], kappa_ls = ic[2])
  }) |>
  ungroup()

metricas_base <- bind_rows(
  "Dicionário (regex)"         = resumo_metricas(base_l$categoria, base_l$pred_dic) |>
    mutate(kappa_li = boot_ic(base_l$categoria, base_l$pred_dic)[1],
           kappa_ls = boot_ic(base_l$categoria, base_l$pred_dic)[2]),
  "TF-IDF + logística (CV 10)" = resumo_metricas(base_l$categoria, base_l$pred_ml) |>
    mutate(kappa_li = boot_ic(base_l$categoria, base_l$pred_ml)[1],
           kappa_ls = boot_ic(base_l$categoria, base_l$pred_ml)[2]),
  .id = "instrumento"
)

metricas <- bind_rows(metricas_base, metricas_llm) |> arrange(desc(kappa))
print(metricas, width = Inf)
write_csv(metricas, "resultados/tabelas/validade_instrumentos.csv")

g1 <- metricas |>
  mutate(instrumento = reorder(instrumento, kappa),
         tipo = if_else(str_detect(instrumento, "^LLM"), "LLM (S5-nano instruct, local)", "Baseline clássico")) |>
  ggplot(aes(kappa, instrumento, colour = tipo)) +
  geom_vline(xintercept = c(.4, .6, .8), colour = GRADE, linetype = 2) +
  geom_linerange(aes(xmin = kappa_li, xmax = kappa_ls), linewidth = 2) +
  geom_point(size = 3.5) +
  scale_colour_manual(values = c("Baseline clássico" = CINZA, "LLM (S5-nano instruct, local)" = AZUIS[3])) +
  scale_x_continuous(limits = c(0, 1)) +
  labs(title = "Validade: concordância de cada instrumento com a amostra-ouro",
       subtitle = "Kappa de Cohen com IC 95% bootstrap (n = 120 ementas)",
       x = "Kappa de Cohen", y = NULL, colour = NULL,
       caption = "Referências usuais (Landis & Koch): 0,4 moderada · 0,6 substancial · 0,8 quase perfeita.") +
  tema_minicurso()
salva_fig(g1, "01_validade_kappa")

# --- 4.2 Matriz de confusão do melhor instrumento LLM com t = 0 ---------------
melhor <- metricas_llm |> filter(str_detect(instrumento, "t=0\\)")) |>
  slice_max(kappa, n = 1) |> pull(instrumento)
conf <- aval |> filter(instrumento == melhor) |>
  mutate(categoria_llm = forcats::fct_na_value_to_level(categoria_llm, "(falha)")) |>
  count(humano = factor(categoria, levels = CATEGORIAS), llm = categoria_llm, .drop = FALSE) |>
  group_by(humano) |> mutate(prop = n / sum(n)) |> ungroup()

g2 <- ggplot(conf, aes(llm, humano, fill = prop)) +
  geom_tile(colour = "#fcfcfb", linewidth = 1.5) +
  geom_text(aes(label = n, colour = prop > .5), size = 5) +
  scale_colour_manual(values = c(`TRUE` = "white", `FALSE` = TINTA), guide = "none") +
  scale_fill_gradient(low = "#eef4fc", high = AZUIS[3], limits = c(0, 1), labels = scales::percent) +
  scale_y_discrete(limits = rev) +
  labs(title = paste("Onde o instrumento erra:", melhor),
       subtitle = "Linhas: codificação humana · Colunas: LLM · Cor: % da linha",
       x = "Rótulo do LLM", y = "Rótulo humano", fill = "% da linha") +
  tema_minicurso()
salva_fig(g2, "02_matriz_confusao", w = 8, h = 5.5)

# --- 4.3 Viés diferencial ----------------------------------------------------
# Pergunta: o LLM erra mais para um campo político? Se sim, comparações entre
# campos feitas com rótulos do LLM estarão enviesadas, mesmo com acurácia alta.
dif <- aval |>
  filter(instrumento == melhor) |>
  left_join(select(corpus, doc_id, campo, casa), by = "doc_id") |>
  mutate(punir_h = categoria == "PUNIR", punir_l = categoria_llm %in% "PUNIR",
         acerto = as.character(categoria) == as.character(categoria_llm))

vies_campo <- dif |>
  filter(campo != "Sem partido/Outro") |>
  group_by(campo) |>
  summarise(n = n(), acuracia = mean(acerto, na.rm = TRUE),
            prop_punir_humano = mean(punir_h), prop_punir_llm = mean(punir_l),
            vies_punir = prop_punir_llm - prop_punir_humano, .groups = "drop") |>
  mutate(ep = sqrt(acuracia * (1 - acuracia) / n), li = acuracia - 1.96 * ep, ls = acuracia + 1.96 * ep)
print(vies_campo)
write_csv(vies_campo, "resultados/tabelas/vies_diferencial_campo.csv")

# Teste formal: o acerto depende do campo? (regressão logística)
mod <- glm(acerto ~ campo, family = binomial, data = filter(dif, campo != "Sem partido/Outro"))
print(anova(mod, test = "Chisq"))

g3 <- ggplot(vies_campo, aes(acuracia, reorder(campo, acuracia))) +
  geom_linerange(aes(xmin = pmax(li, 0), xmax = pmin(ls, 1)), linewidth = 2, colour = AZUIS[3]) +
  geom_point(size = 3.5, colour = AZUIS[3]) +
  geom_text(aes(label = paste0("n = ", n)), nudge_y = .25, size = 3.5, colour = TINTA2) +
  scale_x_continuous(limits = c(0, 1), labels = scales::percent) +
  labs(title = "Viés diferencial: o acerto do LLM varia por campo político do autor?",
       subtitle = paste(melhor, "· acurácia na amostra-ouro com IC 95%"),
       x = "Acurácia", y = NULL,
       caption = "Campo: simplificação de Bolognesi, Ribeiro & Codato (2023). Amostras pequenas → intervalos largos.") +
  tema_minicurso()
salva_fig(g3, "03_vies_diferencial", h = 4.2)

# --- 4.4 Confiabilidade ------------------------------------------------------
# (a) Teste-reteste: mesmo prompt (v2), temperatura 0,8, três sementes. Não
#     precisa de rótulo humano: mede só a estabilidade do instrumento.
largo_seed <- llm |>
  filter(prompt_id == "v2", temperatura > 0) |>
  select(doc_id, semente, categoria_llm) |>
  mutate(categoria_llm = as.character(categoria_llm)) |>
  pivot_wider(names_from = semente, values_from = categoria_llm)
alfa_reteste <- alfa_krippendorff(select(largo_seed, -doc_id))
instavel <- mean(apply(select(largo_seed, -doc_id), 1, \(x) length(unique(na.omit(x))) > 1))

# (b) Sensibilidade ao prompt: v1, v2, v3 com temperatura 0
largo_prompt <- llm |>
  filter(temperatura == 0, semente == 42) |>
  select(doc_id, prompt_id, categoria_llm) |>
  mutate(categoria_llm = as.character(categoria_llm)) |>
  pivot_wider(names_from = prompt_id, values_from = categoria_llm)
alfa_prompt <- alfa_krippendorff(select(largo_prompt, -doc_id))
muda_prompt <- mean(apply(select(largo_prompt, -doc_id), 1, \(x) length(unique(na.omit(x))) > 1))

confiab <- tibble(
  comparacao = c("Teste-reteste (v2, t=0,8, 3 sementes)", "Sensibilidade ao prompt (v1, v2, v3; t=0)"),
  alfa_krippendorff = c(alfa_reteste, alfa_prompt),
  prop_ementas_que_mudam = c(instavel, muda_prompt)
)
print(confiab)
write_csv(confiab, "resultados/tabelas/confiabilidade.csv")

# Distribuição das categorias por prompt: a MEDIDA AGREGADA muda com o prompt?
dist_prompt <- llm |>
  filter(temperatura == 0, semente == 42) |>
  count(prompt_id, categoria = forcats::fct_na_value_to_level(categoria_llm, "(falha)")) |>
  group_by(prompt_id) |> mutate(prop = n / sum(n)) |> ungroup()
ref_dist <- read_csv("dados/anotacoes/referencia_completa.csv", show_col_types = FALSE) |>
  count(categoria) |> mutate(prop = n / sum(n), prompt_id = "Referência\nhumana")
dist_all <- bind_rows(dist_prompt, ref_dist) |>
  mutate(categoria = factor(categoria, levels = c(CATEGORIAS, "(falha)")))

# Um painel por categoria: compara cada prompt (azuis, do v1 claro ao v3 escuro)
# com a referência humana (cinza), em vez de barras empilhadas.
dist_all <- dist_all |>
  filter(categoria != "(falha)" | n > 0) |>
  mutate(fonte = factor(prompt_id, levels = c("v1", "v2", "v3", "Referência\nhumana")))
g4 <- ggplot(dist_all, aes(prop, fonte, fill = fonte)) +
  geom_col(width = .7) +
  facet_wrap(~categoria, nrow = 1) +
  scale_fill_manual(values = c(v1 = AZUIS[1], v2 = AZUIS[2], v3 = AZUIS[3], "Referência\nhumana" = CINZA),
                    guide = "none") +
  scale_x_continuous(labels = scales::percent, breaks = c(0, .3, .6), expand = expansion(mult = c(0, .08))) +
  scale_y_discrete(limits = rev) +
  labs(title = "Mesmo modelo, mesmos textos, prompts diferentes: medidas diferentes",
       subtitle = sprintf("Distribuição das categorias nas %d ementas (S5-nano instruct, temperatura 0)", nrow(corpus)),
       x = NULL, y = NULL) +
  tema_minicurso() +
  theme(panel.grid.major.y = element_blank(), strip.text = element_text(face = "bold", hjust = 0),
        panel.spacing.x = unit(1.2, "lines"))
salva_fig(g4, "04_sensibilidade_prompt", h = 4.5)

# --- Variável eleitoral ------------------------------------------------------
ele <- llm |> filter(temperatura == 0, semente == 42) |>
  inner_join(select(ouro, doc_id, eleitoral), by = "doc_id") |>
  group_by(prompt_id) |>
  summarise(n_eleitoral_humano = sum(eleitoral), n_eleitoral_llm = sum(eleitoral_llm, na.rm = TRUE),
            sensibilidade = mean(eleitoral_llm[eleitoral == 1], na.rm = TRUE),
            especificidade = mean(!eleitoral_llm[eleitoral == 0], na.rm = TRUE), .groups = "drop")
print(ele)
write_csv(ele, "resultados/tabelas/validade_eleitoral.csv")

# --- 4.5 Humano × humano (exercício em sala) ----------------------------------
# Cada participante preenche material_apoio/exercicio_codificacao.csv e salva como
# material_apoio/respostas/<nome>.csv. Aqui calculamos o alfa entre os humanos
# e comparamos com o alfa LLM × referência nas mesmas 20 ementas.
arqs <- list.files("material_apoio/respostas", "\\.csv$", full.names = TRUE)
if (length(arqs) >= 2) {
  resp <- map(arqs, \(a) read_csv(a, show_col_types = FALSE) |>
                mutate(codificador = tools::file_path_sans_ext(basename(a)))) |>
    list_rbind() |>
    mutate(categoria = str_to_upper(str_trim(categoria)))
  m <- resp |> select(doc_id, codificador, categoria) |>
    pivot_wider(names_from = codificador, values_from = categoria)
  message("Alfa de Krippendorff entre os ", length(arqs), " codificadores humanos: ",
          round(alfa_krippendorff(select(m, -doc_id)), 3))
}
