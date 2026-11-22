# Instala os pacotes R usados no minicurso (rode uma vez)
pacotes <- c("httr2", "jsonlite", "dplyr", "tidyr", "purrr", "readr", "stringr", "tibble",
             "forcats", "ggplot2", "scales", "tm", "SnowballC", "glmnet", "digest",
             "targets", "visNetwork", "ellmer")
faltam <- setdiff(pacotes, rownames(installed.packages()))
if (length(faltam)) install.packages(faltam)
# Para congelar as versões no seu projeto: renv::init() e depois renv::snapshot()
