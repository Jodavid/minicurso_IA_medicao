# =============================================================================
# BLOCO 6 — Pipeline reprodutível com {targets}
#
#   targets::tar_make()        # roda só o que mudou
#   targets::tar_visnetwork()  # desenha o grafo de dependências
#   targets::tar_outdated()    # o que ficou desatualizado?
#
# Se você editar um prompt, o livro de códigos (referência) ou uma função de
# medição, o {targets} sabe exatamente quais tabelas e figuras precisam ser
# refeitas e refaz apenas elas. Essa é a "memória" da pesquisa.
#
# A coleta (01) e a anotação com LLM (04) NÃO são refeitas automaticamente:
# dependem de APIs externas e são caras. Entram no pipeline como ARQUIVOS
# versionados (dados brutos congelados), que é o que garante a replicação.
# =============================================================================

library(targets)
tar_option_set(packages = c("dplyr", "readr", "stringr", "purrr", "tidyr", "jsonlite", "ggplot2"))

# Executa um script num ambiente isolado e devolve os arquivos que ele produz.
# Os argumentos em `...` só servem para declarar dependências ao {targets}.
roda_script <- function(script, saidas, ...) {
  source(script, local = new.env())
  saidas
}

list(
  # --- Entradas congeladas (dados e instrumentos) ---
  tar_target(arq_corpus, "dados/processado/corpus.csv", format = "file"),
  tar_target(arq_referencia, "dados/anotacoes/referencia_completa.csv", format = "file"),
  tar_target(arq_prompts, list.files("prompts", "\\.txt$", full.names = TRUE), format = "file",
             cue = tar_cue(mode = "always")),
  tar_target(arq_cache_llm, list.files("dados/cache_llm", "\\.jsonl$", full.names = TRUE), format = "file",
             cue = tar_cue(mode = "always")),
  tar_target(arq_funcoes, c("R/funcoes_medicao.R", "R/tema_graficos.R"), format = "file"),
  # Os próprios scripts das etapas: sem isto, editar um script não refaz nada
  tar_target(arq_scripts, list.files("R", "^0[2-6]_.*\\.R$", full.names = TRUE), format = "file"),

  # --- Etapas ---
  tar_target(
    amostra_ouro,
    roda_script("R/02_amostra_ouro.R",
                c("dados/anotacoes/amostra_ouro.csv", "material_apoio/exercicio_codificacao.csv"),
                arq_corpus, arq_referencia, arq_scripts),
    format = "file"
  ),
  tar_target(
    baselines,
    roda_script("R/03_baselines.R",
                c("resultados/tabelas/baselines.csv", "dados/anotacoes/predicoes_baselines.csv",
                  "dados/anotacoes/dicionario_corpus.csv"),
                amostra_ouro, arq_funcoes, arq_scripts),
    format = "file"
  ),
  tar_target(
    validacao,
    roda_script("R/05_validacao.R",
                c("resultados/tabelas/validade_instrumentos.csv",
                  "resultados/tabelas/confiabilidade.csv",
                  "resultados/tabelas/vies_diferencial_campo.csv"),
                baselines, arq_cache_llm, arq_prompts, arq_funcoes, arq_scripts),
    format = "file"
  ),
  tar_target(
    inferencia,
    roda_script("R/06_inferencia.R",
                c("resultados/tabelas/estimativas_punir.csv",
                  "resultados/tabelas/estimativas_punir_campo.csv",
                  "resultados/tabelas/simulacao_cobertura.csv"),
                validacao, arq_funcoes, arq_scripts),
    format = "file"
  ),
  tar_target(
    sessao,
    {
      inferencia
      writeLines(capture.output(sessionInfo()), "resultados/sessionInfo.txt")
      "resultados/sessionInfo.txt"
    },
    format = "file"
  )
)
