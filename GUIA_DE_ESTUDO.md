# Guia de estudo do ministrante

**Minicurso:** Inteligência Artificial como Instrumento de Medição · II DataPOL · 24 a 26/11/2026
**Objetivo deste guia:** em 5 dias de estudo, entender cada peça do material, saber executar tudo
na sua máquina e chegar à apresentação com as demonstrações ensaiadas.

> Tudo aqui foi testado em 18/11/2026 nesta pasta: pipeline R, notebooks Python 02/04/05,
> anotação ao vivo com o Ollama, livro (HTML e PDF) e slides.
> Os números das tabelas abaixo são os que você deve ver na sua tela.

---

## 0. O mapa em uma página

**Pergunta substantiva:** quando o Congresso legisla sobre IA, ele quer PUNIR, REGULAR ou PROMOVER?
**Pergunta metodológica (a que importa):** como sabemos se o rótulo que o LLM dá está certo, e
como fazer inferência com rótulos que têm erro?

```
APIs Câmara/Senado ──► corpus (304 ementas) ──► amostra-ouro (120; referência preliminar de outra IA)
                                   │                         │
                                   ▼                         ▼
              LLM (S5-nano, 3 prompts) ──► VALIDAÇÃO (kappa, viés, confiabilidade)
              baselines (dicionário, TF-IDF) ──┘             │
                                                             ▼
                              INFERÊNCIA: ingênuo × PPI × PPI++ (corrige o erro do LLM)
                                                             │
                              REPRODUTIBILIDADE (targets, cache, hashes) + ÉTICA
```

A ideia que amarra tudo: **um LLM é um instrumento de medição**, como um questionário ou um
codificador humano. Tem **validade** (mede o que diz medir?), **confiabilidade** (mede sempre
igual?) e **viés** (erra igual para todos?). E rótulos com erro, usados como se fossem verdade,
produzem intervalos de confiança **estreitos e errados**.

| Arquivo | Para que serve |
|---|---|
| `ROTEIRO.md` | Cronograma das 4h (tempo, bloco, material de cada parte) |
| `slides/*.qmd` | Slides (Quarto/reveal.js): `parte1_conceitos`, `completo_R`, `completo_python` |
| `livro/` → `docs/` | Livro completo; é o seu "texto de apoio" para estudar |
| `CODEBOOK.md` | Livro de códigos (PUNIR/REGULAR/PROMOVER/OUTRO + eleitoral) |
| `R/01…06_*.R` | Trilha R, um script por bloco |
| `python/01…05_*.ipynb` | Trilha Python equivalente (Colab) |
| `_targets.R` | Pipeline reprodutível que liga tudo |
| `CHECKLIST.md` | Checklist para usar LLM como instrumento (apêndice A do livro) |

---

## 1. Plano de estudo (5 dias)

| Dia | Estudar (livro) | Executar | Pronto quando… |
|---|---|---|---|
| **1 · qui 19/11** | Apresentação, cap. 1–3 | Seção 2 (ambiente) + `tar_make()` | O pipeline roda e você explica o livro de códigos com 3 exemplos |
| **2 · sex 20/11** | Cap. 4–5 | Blocos 3 e 4 (baselines, LLM ao vivo) | Você anota 5 ementas ao vivo e explica temperatura, semente, cache e hash do prompt |
| **3 · sáb 21/11** | Cap. 6 | Bloco 5 (validação) | Você interpreta kappa, matriz de confusão, viés diferencial e alfa sem olhar o livro |
| **4 · dom 22/11** | Cap. 7 (o mais difícil) | Bloco 6 (inferência) | Você explica PPI no quadro com a fórmula de 2 termos |
| **5 · seg 23/11** | Cap. 8–9 + apêndices | Ensaio geral (seção 5) + plano B | Você passou os slides inteiros cronometrando, com as demos |

Dica: leia cada capítulo no livro (`docs/index.html`) **com o script correspondente aberto ao
lado**. O livro mostra trechos do próprio código (função `trecho()` em `livro/setup_livro.R`),
então o que você lê é exatamente o que roda.

---

## 2. Preparar o ambiente (dia 1, ~30 min)

Na raiz do projeto (`minicurso_IA_medicao_publico/`):

```r
# R (>= 4.3)
source("R/00_pacotes.R")     # instala httr2, dplyr, glmnet, targets, ... (uma vez)
targets::tar_make()          # refaz amostra-ouro, baselines, validação, inferência
targets::tar_visnetwork()    # grafo do pipeline (mostrar em sala no bloco 7)
```

**Esperado:** `✔ ended pipeline`, com o aviso *"A amostra-ouro ainda NÃO foi revisada por
humanos"* (é proposital até a referência ser revisada; ver seção 6).

```bash
# Python (3.11)
pip install -r requirements.txt
cd python && jupyter notebook          # abrir 01…05 na ordem
```

```bash
# LLM local (só para a demo ao vivo e para quem quiser refazer a anotação)
ollama --version                                   # material gerado com 0.40.15
ollama pull hf.co/maritaca-ai/S5-nano-GGUF:Q4_K_M  # ~3,5 GB
ollama create s5-nano-instruct -f modelos/Modelfile.s5-nano-instruct
ollama list                                        # deve listar s5-nano-instruct (ID 85ec77c8f04e)
```

```bash
# Livro e slides (Quarto + TinyTeX + Chrome)
quarto render slides/parte1_conceitos.qmd
quarto render slides/completo_R.qmd
quarto render slides/completo_python.qmd
cd livro && Rscript -e 'source("build.R")'                                   # HTML + slides + .zip em docs/
Rscript -e 'bookdown::render_book("index.Rmd", output_format = "bookdown::pdf_book")'   # PDF
```

Se o R reclamar do pandoc: `Sys.setenv(RSTUDIO_PANDOC = "/opt/quarto/bin/tools/x86_64")`
(mais detalhes em `COMO_COMPILAR.txt`).

---

## 3. Bloco a bloco: entender, executar, conferir

Para cada bloco: **o que você precisa entender**, **o que rodar**, **o que deve aparecer** e
**perguntas prováveis da plateia**.

### Bloco 0 · Abertura (0:00–0:20) · livro cap. 1

**Entender**
- Por que agora: explosão de PLs sobre IA e deepfakes em 2023–2026, eleições de 2026,
  Resolução do TSE, PL 2338/2023 (ver `material_apoio/contexto_regulatorio.md`).
- A virada do curso: a I DataPOL mostrou como **usar** IA; aqui vamos **medir** com ela.
- Estatística × ML × IA generativa: o LLM não substitui o desenho de pesquisa; ele é mais
  um instrumento, e instrumentos precisam ser calibrados.
- O slide "A fase atual da estatística", em uma frase cada (o slide seguinte traz a tabela):
  - **Breiman (2001)**: *modelar* (explicar como os dados são gerados, com incerteza) ×
    *prever* (acertar a resposta, mesmo sem entender o mecanismo).
  - **Double ML**: usa ML para "limpar" a influência de muitos controles e estima um efeito
    causal com IC válido.
  - **Predição conformal**: transforma qualquer previsão num intervalo (ou conjunto de rótulos)
    que acerta com a frequência prometida (p. ex. 95%).
  - **PPI**: muitas previsões + poucos rótulos verdadeiros; mede o viés das previsões nos
    rotulados e o desconta. **É o único dos quatro que usamos** (bloco 6).
  - **DSL** (Egami et al.): a mesma correção para regressões com rótulos de LLM.
  - **O fio comum**: previsões ajudam a inferência *se* o erro delas for medido e corrigido.

**Antes do dia:** confirme o status do PL 2338/2023 e notícias recentes sobre IA na eleição.

### Bloco 1 · Dados legislativos (0:20–0:45) · cap. 2 · `R/01_coleta.R`

**Entender**
- APIs de dados abertos da Câmara (`dadosabertos.camara.leg.br`) e do Senado; funções em
  `R/funcoes_coleta.R`.
- Três armadilhas reais (todas tratadas no código e boas para contar em sala):
  1. a API da Câmara limita o intervalo de datas a ~3 meses → a coleta é feita em janelas;
  2. "partido na data": a API devolve registros de "partido no início da legislatura" com data
     de 2023 para legislaturas antigas → o código filtra;
  3. a busca por palavra-chave traz **falsos positivos** → a coleta também é medição.
- Corpus congelado: 304 PLs (260 Câmara, 44 Senado), coletados em 06/11/2026.

**Executar ao vivo (1 chamada, opcional, precisa de internet):** a primeira célula de
`python/01_coleta.ipynb` ou um `httr2::request()` de `R/funcoes_coleta.R`.
**Não** rode `R/01_coleta.R` completo em sala (~5–10 min e muda o corpus).

**Pergunta provável:** *"E se a API mudar?"* → por isso guardamos as respostas brutas em
`dados/bruto/` (dado congelado = replicável).

### Bloco 2 · Codificar é medir (0:45–1:05) · cap. 3 · `CODEBOOK.md`

**Entender**
- Categorias mutuamente exclusivas: **PUNIR** (tipifica crime, aumenta pena),
  **REGULAR** (obrigações, transparência, rotulagem), **PROMOVER** (incentivo, fomento,
  educação), **OUTRO**; mais a variável **eleitoral** (sim/não).
- Regras de desempate do livro de códigos (leia com atenção: são o que a plateia vai discutir).
- Amostra-ouro: 120 ementas sorteadas (≈40% do corpus) = a "régua" contra a qual o LLM é
  comparado. **Neste material a régua não é humana:** a referência das 304 ementas é uma
  codificação **preliminar feita por outra IA (Claude Opus 5.5)**, aplicando o livro de
  códigos só à ementa (298 em 08/10/2026 + 6 em 06/11/2026), **sem revisão humana**
  (`codificador = "preliminar"`, `revisado = FALSE`). Consequência: o kappa do bloco 5 é
  concordância **entre duas IAs** (S5-nano × Claude), que infla se as duas erram igual.
- **Quantos de cada classe** (referência): PUNIR 53 (17,4%) · REGULAR 150 (49,3%) ·
  PROMOVER 56 (18,4%) · OUTRO 45 (14,8%). Amostra-ouro: 22 · 69 · 16 · 13.
  Eleitoral = 1: 13 no corpus, 8 na amostra-ouro.
- **OUTRO** (45, sendo 32 de 2026) = a busca trouxe, mas a ementa não fala de IA: temas
  digitais vizinhos (violência digital, crimes cibernéticos, LGPD), leis penais sem IA na
  ementa (arts. 216-B/218-C, estelionato, usura) e falsos positivos puros (nuclear,
  transplante, trânsito). Vieram porque a busca não olha só a ementa.

**Perguntas à turma neste bloco (só perguntas, sem atividade em grupo) e respostas:**
1. *"Por que não aceitar o rótulo do Claude como verdade?"* → porque seria medir uma IA com
   outra: erros em comum não aparecem, e não sabemos o teto humano.
2. *"PUNIR sobre 304 ou só sobre as que tratam de IA?"* → 17,4% sobre 304; 20,5% sobre 259.
   É uma decisão de medição (o material usa 304); o slide revela a resposta com um clique.
3. **Votação de mão levantada** em doc0185 (→ PUNIR: altera o Código Penal) e doc0233
   (→ REGULAR: "responsabilização" sem crime, regra 2). O clique seguinte mostra a referência.
   Se a sala se dividir, é exatamente o que o alfa entre codificadores mede.

O exercício de 20 ementas (`material_apoio/exercicio_codificacao.csv`) continua no material
como atividade **opcional, fora da sala**; não há mais slide de intervalo nem coleta de
respostas durante o curso.

### Bloco 3 · Baselines (1:05–1:25) · cap. 4 · `R/03_baselines.R`

**Entender**
- Antes de usar LLM, pergunte: **quanto se acerta sem ele?**
- Classe majoritária (sempre REGULAR): acurácia 57,5%, kappa 0 → por isso acurácia engana.
- Dicionário (regex em `REGEX`, `R/funcoes_medicao.R`): kappa 0,70. **Mas** foi escrito depois
  de ler as ementas → *data leakage*, desempenho otimista ("o dicionário viu a prova").
- TF-IDF + logística com validação cruzada (10 folds): kappa 0,41 em R (`glmnet`) e 0,51 em
  Python (`scikit-learn`). Mesmo nome de método, implementações diferentes, números diferentes.

**Rodar:** `Rscript R/03_baselines.R` ou `python/02_baselines.ipynb`.

### Bloco 4 · O LLM como instrumento (1:25–1:50) · cap. 5 · `python/anotar_llm.py`

**Entender**
- **S5-nano** (Maritaca AI): brasileiro, derivado do Qwen3.5-4B com pré-treino adicional em
  português, Apache-2.0, ~4B parâmetros, quantizado em 4 bits (Q4_K_M), roda em notebook.
- Modo *instruct*: o código envia `"think": false` e **rejeita** respostas com raciocínio.
- **Saída estruturada** (JSON Schema): `{"categoria": ..., "eleitoral": ...}`.
- O **prompt é parte do instrumento**: v1 (simples), v2 (livro de códigos), v3 (few-shot),
  em `prompts/` com `CHANGELOG.md`. O hash SHA-256 do prompt vai para o cache.
- Temperatura e semente: t = 0 é a configuração principal; t = 0,8 com 3 sementes é o
  teste-reteste.
- **Cache é dado, não lixo**: `dados/cache_llm/<modelo>__<prompt>__t<temp>__s<semente>.jsonl`,
  uma linha por ementa, com modelo, digest dos pesos, versão do Ollama, hash do prompt,
  resposta bruta, rótulo e tempo. Abra um arquivo e mostre uma linha em sala.

**Demo ao vivo (testada em 18/11: 5 ementas, ~0,4 s cada, rótulos iguais ao cache):**

```bash
ollama list                                   # mostrar o modelo e o digest
python python/anotar_llm.py --prompt v2 --temperatura 0 --semente 42 --n 5 --pasta /tmp/demo
```

Use **sempre** `--pasta` fora de `dados/cache_llm/` na demo, para não misturar o seu teste com o
cache oficial. Mostre que os 5 rótulos coincidem com os do cache (reprodutibilidade a t = 0).
Depois, troque `--prompt v1` e mostre um rótulo que muda (sensibilidade ao prompt).

**Perguntas prováveis**
- *"Por que não o ChatGPT?"* → APIs comerciais mudam o modelo sem aviso (*drift*); modelo local
  com versão fixa é auditável e gratuito. O código R tem a alternativa com `ellmer` (comentada
  em `R/04_anotacao_llm.R`).
- *"Precisa de GPU?"* → não para a sala: tudo roda do cache. Para anotar 304 ementas × 6
  execuções: ~15 min numa RTX 4050 de notebook.

### Bloco 5 · Validação (2:05–2:50) · cap. 6 · `R/05_validacao.R`

**Entender (o coração técnico do curso)**
- **Kappa de Cohen** = (pₒ − pₑ)/(1 − pₑ): acerto além do acaso. Landis & Koch: >0,4 moderado,
  >0,6 substancial, >0,8 quase perfeito. IC por **bootstrap percentil**.
- **F1 macro**: média do F1 por categoria (dá peso às categorias raras, como PROMOVER).
- **Matriz de confusão**: *onde* o LLM erra. No v2 ele acerta os 22 PUNIR, mas vê PUNIR em
  4 ementas que o humano codificou como REGULAR (daí superestimar PUNIR); as outras confusões
  são OUTRO → REGULAR (5) e REGULAR → PROMOVER (4).
- **Viés diferencial**: o erro é igual entre Esquerda, Centro e Direita? Se o LLM superestima
  PUNIR mais num campo, comparações entre campos ficam enviesadas.
- **Confiabilidade**: alfa de Krippendorff em (a) teste-reteste (mesmo prompt, 3 sementes) e
  (b) sensibilidade ao prompt (v1, v2, v3).

**Números esperados (amostra-ouro, n = 120)**

| Instrumento | Acurácia | Kappa [IC 95%] |
|---|---|---|
| LLM v2 (t = 0) — **o melhor** | 85,0% | 0,75 [0,64; 0,85] |
| LLM v3 (t = 0) | 84,2% | 0,75 [0,65; 0,85] |
| LLM v1 (t = 0) | 72,5% | 0,52 [0,38; 0,65] |
| Dicionário (otimista) | 80,8% | 0,70 [0,59; 0,81] |
| TF-IDF + logística | 68,3% | 0,41 [0,26; 0,54] |

| Confiabilidade | Alfa | Ementas que mudam |
|---|---|---|
| Teste-reteste (v2, t = 0,8, 3 sementes) | 1,00 | 0% |
| Sensibilidade ao prompt (v1, v2, v3) | 0,75 | 23% |

**Mensagem:** o modelo é estável em relação à semente, mas **muito sensível ao prompt**: um
quarto das ementas muda de rótulo só porque mudamos a pergunta. O prompt é o questionário.

**Viés por campo** (proporção PUNIR, humano → LLM): Centro 16% → 19%, Direita 15% → 19%,
Esquerda 18% → 21%. O LLM superestima PUNIR nos três campos, em magnitude parecida (+3 a +4 p.p.).

### Bloco 6 · Inferência com rótulos imperfeitos (2:50–3:20) · cap. 7 · `R/06_inferencia.R`

**Entender (estude com calma; é o conceito mais novo para a plateia)**

Queremos θ = proporção de PLs que querem PUNIR. Temos:
- N = 304 rótulos do LLM (baratos, com erro);
- n = 120 rótulos humanos (caros, "verdade"), num subconjunto.

Três estimadores:
1. **Só humanos**: média dos 120. Sem viés, mas IC largo.
2. **Ingênuo**: média dos 304 rótulos do LLM, como se fossem verdade. IC estreito… **e errado**,
   porque herda o viés do LLM.
3. **PPI** (*Prediction-Powered Inference*, Angelopoulos et al., 2023, *Science*):

   θ̂_PPI = (média do LLM nos N) − (média de [LLM − humano] nos n)

   O segundo termo é o **retificador**: estima o viés do LLM na amostra-ouro e o desconta.
   O IC soma as duas variâncias. **PPI++** pondera o primeiro termo por λ ∈ [0, 1], escolhido
   para minimizar a variância (λ = 0 → só humanos; λ = 1 → PPI). Aqui λ ≈ 0,49.

**Números esperados (proporção PUNIR; referência completa = 17,4%)**

| Estimador | Estimativa [IC 95%] | Cobre 17,4%? |
|---|---|---|
| Só humanos (n = 120) | 18,3% [11,4; 25,3] | sim |
| Ingênuo (LLM = verdade) | 23,0% [18,3; 27,8] | **não** |
| PPI | 20,6% [13,6; 27,6] | sim |
| PPI++ | 19,4% [14,4; 24,5] | sim (e mais estreito que só humanos) |

**Simulação de cobertura** (1000 reamostragens da amostra-ouro; cobertura nominal = 95%):

| n da amostra-ouro | Ingênuo | PPI | PPI++ | Só humanos |
|---|---|---|---|---|
| 30 | 0% | 84% | 87% | 90% |
| 60 | 0% | 97% | 96% | 97% |
| 120 | 0% | 99% | 100% | 99% |

**Mensagens:** (1) o IC ingênuo **nunca** cobre a verdade: precisão sem validade; (2) PPI/PPI++
devolvem a honestidade ao preço de um IC mais largo; (3) com amostra-ouro muito pequena (30), a
cobertura fica abaixo de 95% (aproximação normal); por isso ~60+ ementas humanas.

**Pergunta provável:** *"Então não preciso de humanos?"* → precisa, sim: o PPI **depende** da
amostra-ouro; o LLM só reduz quantas ementas humanas são necessárias para uma dada precisão.

### Bloco 7 · Reprodutibilidade (3:20–3:40) · cap. 8 · `_targets.R`

**Entender**
- O que versionar: dados brutos, prompts (com hash), modelo (digest dos pesos), versão do
  Ollama, temperatura, semente, respostas brutas (cache), código, ambiente (`renv`,
  `requirements.txt`, `resultados/sessionInfo.txt`).
- `targets`: grafo de dependências; edite um prompt e só o que depende dele é refeito.
- **História real para contar** (está na tabela de verificações do cap. 8): na revisão de
  18/11, o `tar_make()` falhou porque caches antigos de outro modelo (`gemma4-e2b`) estavam na
  mesma pasta do cache oficial e eram lidos junto. Correção: a leitura agora filtra pelo
  instrumento (`INSTRUMENTO` em `R/funcoes_medicao.R` e `python/medicao.py`). Moral:
  ferramentas de reprodutibilidade também precisam ser testadas.
- *Drift*: repetimos as anotações a t = 0 em 12/11 (`dados/repeticao/`): 5 de 912 rótulos mudaram.
  Nem "temperatura 0" é garantia absoluta de determinismo.

**Demo ao vivo (testada):**

```r
targets::tar_visnetwork()   # mostrar o grafo
targets::tar_outdated()     # tudo atualizado (o cache e os prompts sempre aparecem: cue "always")
# edite uma vírgula em prompts/prompt_v2_codebook.txt e rode de novo:
targets::tar_outdated()     # agora validacao e inferencia aparecem
# DESFAÇA a edição depois (Ctrl+Z) e rode tar_make() de novo
```

### Bloco 8 · Ética e debate (3:40–4:00) · cap. 9

- IA nas eleições de 2026 (Res. TSE), PL 2338/2023, viés político dos LLMs (Motoki et al., 2024).
- **Quando não usar LLM:** conceitos sem livro de códigos, poucos textos (codifique à mão),
  sem orçamento para amostra-ouro, dados sensíveis enviados a APIs externas.
- Feche com a coerência do material: a própria autoria com IA está declarada (apêndice D).

---

## 4. Trilha Python (Colab)

- Notebooks `python/01…05` espelham os scripts R; `python/medicao.py` tem as mesmas funções
  (kappa, alfa, F1, bootstrap, PPI, PPI++).
- R e Python dão os mesmos números, a menos de: ICs bootstrap e simulação (até 0,01 de
  diferença, geradores aleatórios diferentes) e TF-IDF (0,41 × 0,51).
- **No Colab**, a primeira célula clona `REPO_URL = "https://github.com/jodavid/minicurso-ia-medicao"`.
  Esse repositório precisa existir e ser público com esse nome (ver seção 6).
- Antes de publicar notebooks executados localmente, limpe caminhos locais das saídas
  (a célula 1 imprime a "Raiz do projeto"): `jupyter nbconvert --clear-output --inplace python/*.ipynb`
  ou confira com `grep -n "/home/" python/*.ipynb`.

---

## 5. Ensaio geral (dia 5)

1. Abra o deck do formato escolhido (`slides/parte1_conceitos.html`, `slides/completo_R.html`
   ou `slides/completo_python.html`) no navegador da máquina da apresentação, tecla **F** (tela cheia),
   **S** (notas do apresentador), **O** (visão geral).
2. Cronometre bloco a bloco com o `ROTEIRO.md` (soma exata: 240 min, com intervalo de 15).
3. Faça as 2 demos: anotação de 5 ementas (bloco 4) e `tar_visnetwork()` / `tar_outdated()`
   (bloco 7).
4. **Plano B sem internet:** tudo roda de `dados/` e `dados/cache_llm/`. Leve o projeto num
   pendrive e o PDF do deck (em `docs/slides/`).
5. **Plano B sem Ollama:** mostre uma linha do cache (`head -n 1 dados/cache_llm/s5-nano-instruct__v2__t0.0__s42.jsonl`)
   no lugar da demo ao vivo.

---

## 6. Pendências antes de 24/11

- [ ] **Revisar a referência** (`dados/anotacoes/referencia_completa.csv`, coluna `revisado`):
      hoje é preliminar e os números são ilustrativos. Depois de revisar: `revisado = TRUE`,
      `targets::tar_make()`, recompilar livro e slides. Os números se atualizam sozinhos, **exceto**
      alguns fixos no texto dos slides ("metade regula", "5 de 912", "304 ementas"): confira-os.
- [ ] Definir o **dia e horário** exatos do minicurso (o material diz só "24 a 26/11") e colocar
      no README e nos slides.
- [ ] **Publicar online** (seção 7) e testar o Colab com o repositório público.
- [ ] Na máquina da apresentação: `ollama pull …` e `ollama create …` (seção 2).

---

## 7. Publicar online (GitHub Pages)

1. Crie o repositório **público** `minicurso-ia-medicao` na sua conta do GitHub (o nome precisa
   bater com `REPO_URL` nos notebooks e com `url:` em `livro/index.Rmd`).
2. **Não** suba: `backup_originais/`, `livro/backup_template/`, `slides/backup_template/`,
   `_targets/`, `__pycache__/` (todas já estão no `.gitignore`).
3. Suba o restante, incluindo `docs/`.
4. *Settings → Pages → Deploy from a branch → main → /docs*.
5. Endereço final: `https://jodavid.github.io/minicurso-ia-medicao/`. Teste: menu, busca, botões
   "Slides", "Livro em PDF" e "Material completo (.zip)" na página inicial, e a abertura no celular.
6. Se usar outro nome de repositório, ajuste `url:` em `livro/index.Rmd` e `REPO_URL` em
   `python/_gerar_notebooks.py` e nos notebooks, e recompile.

---

## 8. Cola rápida (números para ter na ponta da língua)

- Corpus: **304** PLs (260 Câmara, 44 Senado), 2019–2026, coletados em 06/11/2026.
- Amostra-ouro: **120** ementas. Referência preliminar feita por **outra IA** (Claude Opus 5.5).
- Classes (referência): PUNIR **53** · REGULAR **150** · PROMOVER **56** · OUTRO **45** · eleitoral **13**.
- Melhor LLM: **v2, t = 0**: kappa **0,75** [0,64; 0,85], acurácia **85%**.
- Dicionário: kappa 0,70 (otimista). TF-IDF: 0,41 (R) / 0,51 (Python). Classe majoritária: 57,5%.
- Teste-reteste: alfa **1,00**. Sensibilidade ao prompt: alfa **0,75**, **23%** mudam.
- PUNIR: referência **17,4%** · ingênuo **23,0%** (não cobre) · PPI **20,6%** · PPI++ **19,4%**.
- Cobertura simulada (n = 120): ingênuo **0%**, PPI **99%**, PPI++ **100%**.
- Repetição a t = 0 (12/11): **5 de 912** rótulos mudaram.
- Modelo: S5-nano instruct, Q4_K_M, ~3,5 GB, Ollama 0.40.15, digest `85ec77c8f04e`.
