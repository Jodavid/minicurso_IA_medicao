# Roteiro do minicurso (4h)

**Inteligência Artificial como Instrumento de Medição: Validação Estatística e Reprodutibilidade**
II DataPOL · 24 a 26/11/2026 · Auditório do CCEN/UFPE · Prof. Dr. Jodavid Ferreira (DEst/UFPE)

## Dois formatos para as 4 horas

| Formato | Como funciona | Slides |
|---|---|---|
| **A · Conceitos + prática** | 2h só com slides (ideias, desenho, fórmulas; **sem resultados**) e 2h executando os scripts/notebooks com a turma | `slides/parte1_conceitos.qmd` (Parte 1) + `R/0X_*.R` ou `python/0X_*.ipynb` (Parte 2) |
| **B · Tudo por slides** | 4h seguindo só os slides, que trazem o código, o que está sendo executado e as saídas reais | `slides/completo_R.qmd` **ou** `slides/completo_python.qmd` |
| Versão resumida | ~45 slides com os resultados principais (a versão original) | `slides/slides.qmd` |

Os blocos e os horários abaixo valem para os dois formatos. No formato A, a Parte 1 percorre todos os blocos em cerca de 2h e a Parte 2 refaz os blocos 1 a 7 no código. Os slides não trazem horários: o ritmo fica a critério do ministrante.

**Pergunta que atravessa o curso:** *quando o Congresso legisla sobre IA, ele quer PUNIR, REGULAR ou PROMOVER? E como sabemos se a resposta que um LLM nos dá está certa?*

| Tempo | Bloco | O que acontece | Material |
|---|---|---|---|
| 0:00–0:20 | **0. Abertura** | Gancho: eleições de 2026, regras do TSE, Marco Legal da IA parado na Câmara. Ponte com a I edição: "vocês já viram como **usar** IA; hoje vamos **medir** com ela". Estatística × ML × IA generativa; LLM = instrumento. | Slides 1–8 (resumida) · blocos 0 dos decks completos |
| 0:20–0:45 | **1. Dados legislativos** | APIs da Câmara e do Senado ao vivo (uma chamada). Armadilhas reais: limite de 3 meses na data, partido "na data", falsos positivos da busca. Corpus de 304 PLs. | `R/01_coleta.R` · `python/01_coleta.ipynb` |
| 0:45–1:05 | **2. Codificar é medir** | Livro de códigos. **De onde vem a referência** (codificação preliminar feita por outra IA, o Claude Opus 5.5, sem revisão humana). **Quantos de cada classe** (PUNIR 53 · REGULAR 150 · PROMOVER 56 · OUTRO 45) e o que foi para OUTRO. **Pergunta à turma:** votação de mão levantada em duas ementas difíceis (doc0185, doc0233). | `CODEBOOK.md` · `dados/anotacoes/referencia_completa.csv` |
| 1:05–1:25 | **3. Baselines** | Dicionário (regex) e TF-IDF + logística com validação cruzada. "Quanto se acerta sem LLM?" Discussão: o dicionário "viu a prova". | `R/03_baselines.R` · `python/02_baselines.ipynb` |
| 1:25–1:50 | **4. LLM como instrumento** | Ollama local (S5-nano instruct, Maritaca AI, 4 bits), **por que o S5-nano** (modelo brasileiro, treinado em português, derivado do Qwen3.5-4B), saída estruturada, três prompts versionados, temperatura e semente, cache. Demonstração ao vivo com 5 ementas; o resto vem do cache. | `prompts/` · `python/anotar_llm.py` · `R/04_anotacao_llm.R` |
| 1:50–2:05 | *Intervalo* | (sem slide próprio) | |
| 2:05–2:50 | **5. Validação** | Kappa com IC bootstrap, matriz de confusão, viés diferencial por campo político, teste-reteste, sensibilidade ao prompt. Lembrar que, com a referência feita por outra IA, o kappa é uma concordância **entre duas IAs** e o teto humano ainda é desconhecido. | `R/05_validacao.R` · `python/04_validacao.ipynb` |
| 2:50–3:20 | **6. Inferência** | Só humanos × ingênuo × PPI × PPI++. Simulação de cobertura: o IC "ingênuo" é estreito e erra. Resposta à pergunta substantiva, com incerteza honesta. | `R/06_inferencia.R` · `python/05_inferencia.ipynb` |
| 3:20–3:40 | **7. Reprodutibilidade** | `targets` (grafo, `tar_outdated()` ao editar um prompt), cache como dado, hash do prompt, `renv`/`requirements.txt`, pacote de replicação. Auditar código gerado por agentes. | `_targets.R` · `CHECKLIST.md` |
| 3:40–4:00 | **8. Ética, limites e debate** | IA nas eleições de 2026 (Res. TSE 23.755/2026), PL 2338/2023, viés político dos LLMs, quando **não** usar LLM. | `material_apoio/contexto_regulatorio.md` |

## Preparação (checklist do ministrante)

- [ ] **Revisar a codificação de referência** (`dados/anotacoes/referencia_completa.csv`): hoje ela é preliminar. Idealmente com um segundo codificador e cálculo do alfa entre os dois. Depois, marcar `revisado = TRUE` e rodar `targets::tar_make()`. Todos os números dos slides se atualizam.
- [ ] Atualizar a coleta perto da data (`Rscript R/01_coleta.R`) e reanotar (`python python/anotar_llm.py --todas`), **ou** manter o corpus congelado de 06/11/2026 (recomendado para estabilidade em sala). A coleta foi refeita em 06/11/2026: 6 PLs novos, amostra-ouro sorteada de novo.
- [ ] Conferir o status do PL 2338/2023 e as notícias sobre IA nas eleições de 2026.
- [ ] Testar o Colab com GPU T4 + Ollama (célula de instalação em `python/03_anotacao_llm.ipynb`). O material foi gerado com o Ollama 0.40.15 (o script de instalação do Colab baixa a versão atual).
- [x] 11/11/2026: corpus anotado com o `s5-nano-instruct` (S5-nano, modo instruct, Q4_K_M); 12/11/2026: repetição das execuções a t = 0 em `dados/repeticao/`.
- [ ] Na máquina da apresentação: `ollama pull hf.co/maritaca-ai/S5-nano-GGUF:Q4_K_M` e `ollama create s5-nano-instruct -f modelos/Modelfile.s5-nano-instruct`.
- [ ] Publicar o repositório no GitHub e os slides no GitHub Pages.
- [ ] Plano B sem internet: tudo roda a partir de `dados/` e `dados/cache_llm/`.

## Pré-requisitos para participantes
Noções de R **ou** Python e de estatística básica (proporção, intervalo de confiança). Conta Google (Colab). Não é preciso GPU nem chave de API.
