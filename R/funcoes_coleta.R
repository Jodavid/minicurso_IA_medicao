# =============================================================================
# Funções de coleta: Câmara dos Deputados e Senado Federal (APIs de dados abertos)
# Minicurso "IA como Instrumento de Medição" — II DataPOL (UFPE, 2026)
# =============================================================================

library(httr2)
library(dplyr)
library(purrr)
library(stringr)
library(tibble)

URL_CAMARA <- "https://dadosabertos.camara.leg.br/api/v2"
URL_SENADO <- "https://legis.senado.leg.br/dadosabertos"

# Requisição genérica com retry e identificação (boa prática com APIs públicas)
req_json <- function(url, query = list()) {
  request(url) |>
    req_url_query(!!!query) |>
    req_headers(Accept = "application/json") |>
    req_user_agent("Minicurso DataPOL/UFPE (fins acadêmicos)") |>
    req_retry(max_tries = 6, backoff = ~ 2^.x,       # tenta de novo também em erros 5xx
              is_transient = \(resp) resp_status(resp) %in% c(429, 500, 502, 503, 504)) |>
    req_throttle(rate = 5) |>                # no máximo 5 requisições/segundo
    req_perform() |>
    resp_body_json(simplifyVector = FALSE)
}

# -----------------------------------------------------------------------------
# Câmara: proposições por palavra-chave e ano (a API limita intervalos de datas
# a 3 meses, por isso filtramos por `ano`, que não tem essa restrição)
# -----------------------------------------------------------------------------
camara_proposicoes <- function(termo, ano, tipos = "PL") {
  pagina <- 1
  saida <- list()
  repeat {
    res <- req_json(
      file.path(URL_CAMARA, "proposicoes"),
      list(keywords = termo, ano = ano, siglaTipo = paste(tipos, collapse = ","),
           itens = 100, pagina = pagina, ordem = "ASC", ordenarPor = "id")
    )
    saida <- c(saida, res$dados)
    if (length(res$dados) < 100) break
    pagina <- pagina + 1
  }
  map_dfr(saida, \(x) tibble(
    id = x$id, sigla = x$siglaTipo, numero = x$numero, ano = x$ano,
    ementa = x$ementa, data_apresentacao = x$dataApresentacao
  ))
}

# Primeiro autor (proponente) de uma proposição da Câmara
camara_autor <- function(id) {
  res <- req_json(file.path(URL_CAMARA, "proposicoes", id, "autores"))$dados
  if (length(res) == 0) return(tibble(id = id))
  a <- res[[which.min(map_int(res, \(x) x$ordemAssinatura %||% 99L))]]
  tibble(id = id, autor = a$nome, tipo_autor = a$tipo,
         uri_autor = a$uri %||% NA_character_, n_autores = length(res))
}

# Partido do deputado NA DATA da apresentação (não o partido atual!)
# Usa o histórico do parlamentar: um detalhe que muda a medida e costuma ser ignorado.
camara_partido_na_data <- function(uri_deputado, data_ref) {
  vazio <- tibble(partido = NA_character_, uf = NA_character_)
  if (is.na(uri_deputado) || !str_detect(uri_deputado, "/deputados/")) return(vazio)
  h <- req_json(paste0(uri_deputado, "/historico"))$dados
  h <- map_dfr(h, \(x) tibble(dia = substr(x$dataHora %||% NA, 1, 10),
                              partido = x$siglaPartido %||% NA_character_,
                              uf = x$siglaUf %||% NA_character_,
                              situacao = x$situacao %||% NA_character_))
  # Atenção: a API inclui registros "Nome/Partido no início da legislatura" com a
  # data de 2023-02-01 para TODAS as legislaturas anteriores (situacao = NULL).
  # Sem este filtro, um deputado do PL em 2023 aparece como PMDB ou PFL.
  h <- h |> filter(!is.na(partido), !is.na(dia), !is.na(situacao)) |> arrange(dia)
  if (nrow(h) == 0) return(vazio)
  antes <- h |> filter(dia <= substr(data_ref, 1, 10))
  linha <- if (nrow(antes) > 0) slice_tail(antes, n = 1) else slice_head(h, n = 1)
  select(linha, partido, uf)
}

# Situação atual de tramitação
camara_situacao <- function(id) {
  s <- req_json(file.path(URL_CAMARA, "proposicoes", id))$dados$statusProposicao
  tibble(id = id, situacao = s$descricaoSituacao %||% NA_character_,
         data_situacao = s$dataHora %||% NA_character_)
}

# -----------------------------------------------------------------------------
# Senado: a autoria já vem com partido/UF na data ("Senador Fulano (PSD/MG)")
# -----------------------------------------------------------------------------
senado_processos <- function(termo, ano, sigla = "PL") {
  res <- req_json(
    file.path(URL_SENADO, "processo"),
    list(sigla = sigla, termo = termo,
         dataInicioApresentacao = paste0(ano, "-01-01"),
         dataFimApresentacao = paste0(ano, "-12-31"))
  )
  if (length(res) == 0) return(tibble())
  map_dfr(res, \(x) tibble(
    id = x$id, identificacao = x$identificacao, ementa = x$ementa,
    data_apresentacao = x$dataApresentacao, autoria = x$autoria %||% NA_character_,
    situacao = x$situacaoAtual %||% NA_character_,
    casa_origem = x$casaIdentificadora %||% NA_character_
  ))
}

# Extrai partido e UF do texto de autoria do Senado
extrai_partido_senado <- function(autoria) {
  m <- str_match(autoria, "\\(([A-Za-zÀ-ú ]+)/([A-Z]{2})\\)")
  tibble(partido = m[, 2], uf = m[, 3])
}

# -----------------------------------------------------------------------------
# Limpeza de texto mínima e transparente
# -----------------------------------------------------------------------------
limpa_ementa <- function(x) {
  x |>
    str_replace_all("[\r\n]+", " ") |>
    str_replace("(?i)\\s*NOVA EMENTA:.*$", "") |>   # mantém a ementa original
    str_squish()
}
