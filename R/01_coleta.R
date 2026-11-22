# =============================================================================
# BLOCO 1 — Coleta de dados legislativos sobre Inteligência Artificial
# Câmara dos Deputados + Senado Federal, 2019–2026
#
# Pergunta de pesquisa do minicurso:
#   "Quando o Congresso legisla sobre IA, ele quer PUNIR, REGULAR ou PROMOVER?
#    Isso mudou com as eleições (2022, 2024, 2026) e difere entre campos políticos?"
#
# Saída: dados/processado/corpus.csv
# Tempo de execução: ~5–10 min (centenas de chamadas às APIs). Em sala usamos o
# arquivo já salvo; este script documenta COMO ele foi gerado (reprodutibilidade).
# =============================================================================

source("R/funcoes_coleta.R")
library(readr)
library(tidyr)

TERMOS <- c("inteligência artificial", "deepfake", "deep fake", "conteúdo sintético")
ANOS   <- 2019:2026
DATA_COLETA <- Sys.Date()

# --- 1. Câmara ---------------------------------------------------------------
camara <- expand_grid(termo = TERMOS, ano = ANOS) |>
  pmap(\(termo, ano) camara_proposicoes(termo, ano), .progress = "Câmara") |>
  list_rbind() |>
  distinct(id, .keep_all = TRUE)

autores  <- map(camara$id, camara_autor, .progress = "Autores") |> list_rbind()
situacao <- map(camara$id, camara_situacao, .progress = "Situação") |> list_rbind()

camara <- camara |>
  left_join(autores, by = "id") |>
  left_join(situacao, by = "id")

partidos <- map2(camara$uri_autor, camara$data_apresentacao,
                 camara_partido_na_data, .progress = "Partido na data") |>
  list_rbind()
camara <- bind_cols(camara, partidos)

write_csv(camara, "dados/bruto/camara_raw.csv")

# --- 2. Senado ---------------------------------------------------------------
senado <- expand_grid(termo = TERMOS, ano = ANOS) |>
  pmap(\(termo, ano) senado_processos(termo, ano), .progress = "Senado") |>
  list_rbind() |>
  distinct(id, .keep_all = TRUE)

write_csv(senado, "dados/bruto/senado_raw.csv")

# --- 3. Corpus unificado -----------------------------------------------------
camara_pad <- camara |>
  transmute(
    casa = "Câmara",
    identificacao = paste0(sigla, " ", numero, "/", ano),
    ano, data_apresentacao = substr(data_apresentacao, 1, 10),
    ementa, autor, tipo_autor, partido, uf, situacao
  )

senado_pad <- senado |>
  mutate(extrai_partido_senado(autoria)) |>
  transmute(
    casa = "Senado", identificacao,
    ano = as.integer(substr(data_apresentacao, 1, 4)),
    data_apresentacao, ementa,
    autor = str_remove(autoria, "\\s*\\(.*\\)$"),
    tipo_autor = if_else(str_detect(autoria, "^Senador"), "Senador(a)", "Outro"),
    partido, uf, situacao
  )

# Projetos do Senado remetidos à Câmara aparecem nas duas casas (ex.: PL 2338/2023).
# Mantemos o registro da casa de origem, que traz o partido do autor na data.
corpus <- bind_rows(senado_pad, camara_pad) |>
  distinct(identificacao, .keep_all = TRUE) |>
  mutate(
    ementa = limpa_ementa(ementa),
    partido = str_trim(str_to_upper(partido))
  ) |>
  filter(ano %in% ANOS, nchar(ementa) > 20) |>
  arrange(data_apresentacao) |>
  mutate(doc_id = sprintf("doc%04d", row_number()), .before = 1)

# Campo político: simplificação didática a partir de Bolognesi, Ribeiro & Codato (2023),
# "A New Ideological Classification of Brazilian Political Parties", Dados 66(2).
# É, ela própria, uma MEDIDA, com erro e escolhas; discutimos isso em sala.
ESQUERDA <- c("PSOL", "PT", "PCDOB", "PDT", "PSB", "REDE", "PV")
CENTRO   <- c("MDB", "PSDB", "CIDADANIA", "PSD", "SOLIDARIEDADE", "AVANTE", "PMB")
DIREITA  <- c("PL", "PP", "UNIÃO", "REPUBLICANOS", "NOVO", "PSC", "PTB", "PODE",
              "PODEMOS", "PATRIOTA", "PRD", "DEM", "PSL", "PROS", "PRTB", "AGIR",
              "DC", "PMN", "MOBILIZA")

corpus <- corpus |>
  mutate(
    campo = case_when(
      partido %in% ESQUERDA ~ "Esquerda",
      partido %in% CENTRO   ~ "Centro",
      partido %in% DIREITA  ~ "Direita",
      TRUE ~ "Sem partido/Outro"
    ),
    ano_eleitoral = ano %% 2 == 0,     # 2020, 2022, 2024, 2026
    data_coleta = DATA_COLETA
  )

write_csv(corpus, "dados/processado/corpus.csv")
message("Corpus: ", nrow(corpus), " proposições salvas em dados/processado/corpus.csv")
print(count(corpus, casa, ano))
