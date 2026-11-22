# =============================================================================
# BLOCO 3 — O LLM como instrumento: anotação com modelo aberto local (Ollama)
#           ou comercial (via ellmer), sempre com cache e versionamento
#
# Em sala NÃO precisamos rodar isto: as anotações já estão em dados/cache_llm/
# (geradas com python/anotar_llm.py, mesmo formato). Este script mostra como
# fazer o mesmo em R e serve para quem quiser testar outro modelo ou prompt.
#
# Instrumento: S5-nano (Maritaca AI) em modo instruct, quantizado em 4 bits (Q4_K_M),
# rodando localmente no Ollama com o nome `s5-nano-instruct`.
#
# Pré-requisitos (modelo local):
#   1. instalar o Ollama: https://ollama.com
#   2. no terminal (uma vez):
#        ollama pull hf.co/maritaca-ai/S5-nano-GGUF:Q4_K_M
#        ollama create s5-nano-instruct -f modelos/Modelfile.s5-nano-instruct
# =============================================================================

source("R/funcoes_medicao.R")
library(httr2)
library(digest)

OLLAMA <- Sys.getenv("OLLAMA_HOST", "http://localhost:11434")

ESQUEMA <- list(
  type = "object",
  properties = list(
    categoria = list(type = "string", enum = CATEGORIAS),
    eleitoral = list(type = "boolean")
  ),
  required = list("categoria", "eleitoral")
)

extrai_rotulo <- function(resposta) {
  js <- str_extract(resposta, "(?s)\\{.*?\\}")
  if (is.na(js)) return(list(categoria = NA, eleitoral = NA))
  d <- tryCatch(fromJSON(js), error = \(e) NULL)
  if (is.null(d)) return(list(categoria = NA, eleitoral = NA))
  cat <- str_to_upper(str_trim(d$categoria %||% d$classificacao %||% NA))
  list(categoria = if (cat %in% CATEGORIAS) cat else NA,
       eleitoral = as.logical(d$eleitoral %||% NA))
}

# Modo instruct: think = FALSE em toda chamada. O S5-nano tem também um modo que
# raciocina antes de responder; se vier raciocínio, a chamada é tratada como erro.
chama_ollama <- function(prompt, modelo, temperatura, semente) {
  msg <- request(file.path(OLLAMA, "api/chat")) |>
    req_body_json(list(
      model = modelo, stream = FALSE, think = FALSE, format = ESQUEMA,
      options = list(temperature = temperatura, seed = semente),
      messages = list(list(role = "user", content = prompt))
    )) |>
    req_timeout(120) |>
    req_perform() |>
    resp_body_json() |>
    pluck("message")
  if (nzchar(msg$thinking %||% "")) stop("o modelo devolveu raciocínio: o modo instruct não foi respeitado")
  msg$content
}

# Digest dos pesos no Ollama: o nome local pode apontar para pesos diferentes em
# máquinas diferentes; o digest, não.
digest_modelo <- function(modelo) {
  tryCatch({
    ms <- resp_body_json(req_perform(request(paste0(OLLAMA, "/api/tags"))))$models
    m <- keep(ms, \(x) x$name %in% c(modelo, paste0(modelo, ":latest")))
    if (length(m)) substr(m[[1]]$digest, 1, 12) else NA_character_
  }, error = \(e) NA_character_)
}

anota_corpus <- function(corpus, prompt_id = "v2", modelo = "s5-nano-instruct",
                         temperatura = 0, semente = 42) {
  arq_prompt <- list.files("prompts", paste0("^prompt_", prompt_id, "_"), full.names = TRUE)
  # leitura byte a byte: garante o mesmo hash SHA-256 que a versão em Python
  modelo_prompt <- readChar(arq_prompt, file.size(arq_prompt), useBytes = TRUE)
  Encoding(modelo_prompt) <- "UTF-8"
  prompt_sha <- substr(digest(modelo_prompt, algo = "sha256", serialize = FALSE), 1, 12)
  run_id <- sprintf("%s__%s__t%s__s%d", str_replace_all(modelo, "[:/]", "-"),
                    prompt_id, format(temperatura, nsmall = 1), semente)
  destino <- file.path("dados/cache_llm", paste0(run_id, ".jsonl"))
  # o software que executa o modelo também faz parte do instrumento
  versao <- tryCatch(resp_body_json(req_perform(request(paste0(OLLAMA, "/api/version"))))$version,
                     error = \(e) NA_character_)
  digest <- digest_modelo(modelo)

  feitos <- if (file.exists(destino)) stream_in(file(destino), verbose = FALSE)$doc_id else character()
  pendentes <- filter(corpus, !doc_id %in% feitos)
  message(run_id, ": ", length(feitos), " em cache, ", nrow(pendentes), " pendentes")

  con <- file(destino, open = "a", encoding = "UTF-8")
  on.exit(close(con))
  for (i in seq_len(nrow(pendentes))) {
    prompt <- str_replace(modelo_prompt, fixed("{{ementa}}"), pendentes$ementa[i])
    t0 <- Sys.time()
    bruto <- tryCatch(chama_ollama(prompt, modelo, temperatura, semente),
                      error = \(e) paste("ERRO:", conditionMessage(e)))
    r <- extrai_rotulo(bruto)
    registro <- list(
      doc_id = pendentes$doc_id[i], run_id = run_id, modelo = modelo, modelo_digest = digest, ollama_versao = versao,
      prompt_id = prompt_id, prompt_sha = prompt_sha,
      temperatura = temperatura, semente = semente,
      resposta_bruta = bruto, categoria_llm = r$categoria, eleitoral_llm = r$eleitoral,
      segundos = round(as.numeric(difftime(Sys.time(), t0, units = "secs")), 3),
      timestamp = format(Sys.time(), "%Y-%m-%dT%H:%M:%S%z")
    )
    writeLines(toJSON(registro, auto_unbox = TRUE, na = "null"), con)
  }
  invisible(destino)
}

# --- Exemplo: anotar 10 ementas com o prompt v2 ------------------------------
if (sys.nframe() == 0) {
  corpus <- carrega_corpus()
  anota_corpus(head(corpus, 10), prompt_id = "v2", modelo = "s5-nano-instruct",
               temperatura = 0, semente = 7)
}

# --- Alternativa comercial (opcional; requer chave em variável de ambiente) ---
# A chave NUNCA vai no código nem no GitHub: use ~/.Renviron (OPENAI_API_KEY=...)
#
# library(ellmer)
# tipo <- type_object(
#   categoria = type_enum(CATEGORIAS),
#   eleitoral = type_boolean()
# )
# chat <- chat_openai(model = "gpt-4.1-mini", params = params(temperature = 0, seed = 42))
# chat$chat_structured(str_replace(modelo_prompt, fixed("{{ementa}}"), ementa), type = tipo)
#
# Atenção: APIs comerciais trocam a versão do modelo sem aviso. Registre a data,
# o identificador exato do modelo e guarde as respostas brutas (o cache acima).
