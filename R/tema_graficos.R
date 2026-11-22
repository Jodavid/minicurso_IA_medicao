# Tema e paleta comuns às figuras do minicurso
library(ggplot2)

PALETA <- c("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948")
COR_CAT <- setNames(PALETA[1:4], c("PUNIR", "REGULAR", "PROMOVER", "OUTRO"))
TINTA  <- "#0b0b0b"; TINTA2 <- "#52514e"; GRADE <- "#e4e3df"
# Azuis (escala sequencial clara -> escura) e cinzas: o azul destaca o que a
# figura quer mostrar; o cinza é contexto.
AZUIS <- c("#7ba4de", "#3d7ccc", "#1c3f6e")
CINZA <- "#8f8d88"; CINZA_CLARO <- "#c9c7c2"; CINZA_ESCURO <- "#52514e"
# Estimadores: os que corrigem o erro do LLM em azul; os de referência em cinza
COR_EST <- c("Só humanos (amostra-ouro)" = "#a8a6a1", "Ingênuo (LLM = verdade)" = CINZA_ESCURO,
             "PPI" = AZUIS[1], "PPI++" = AZUIS[3])

tema_minicurso <- function(base = 13) {
  theme_minimal(base_size = base) +
    theme(
      text = element_text(colour = TINTA),
      axis.text = element_text(colour = TINTA2),
      plot.title = element_text(face = "bold", size = base + 2),
      plot.subtitle = element_text(colour = TINTA2),
      plot.caption = element_text(colour = TINTA2, size = base - 3, hjust = 0),
      panel.grid.major = element_line(colour = GRADE, linewidth = .3),
      panel.grid.minor = element_blank(),
      legend.position = "top", legend.justification = "left",
      plot.background = element_rect(fill = "#fcfcfb", colour = NA),
      plot.title.position = "plot"
    )
}

salva_fig <- function(g, nome, w = 9, h = 5.2) {
  ggsave(file.path("resultados/figuras", paste0(nome, ".png")), g,
         width = w, height = h, dpi = 200, bg = "#fcfcfb")
}
