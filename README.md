# Inteligência Artificial como Instrumento de Medição: Validação Estatística e Reprodutibilidade

**Minicurso (4h) · II DataPOL, Escola de Métodos Quantitativos em Ciência Política e RI**
24 a 26 de novembro de 2026 · Auditório do CCEN/UFPE, Recife
Prof. Dr. Jodavid Ferreira (Departamento de Estatística/UFPE)

> Modelos de linguagem de grande porte (LLMs) passaram a fazer parte da rotina de pesquisa, classificando discursos, extraindo informações e anotando grandes corpora. Mas um LLM é, antes de tudo, um **instrumento de medição**: tem erro, viés e confiabilidade que precisam ser avaliados. Este minicurso percorre, em R e Python, o caminho do dado bruto à inferência: **coleta de dados legislativos brasileiros**, *baselines* clássicos, anotação com LLMs abertos e comerciais, validação estatística (concordância, viés diferencial e correção do erro de medição) e boas práticas de MLOps. A discussão final trata dos limites e da ética do uso de IA na pesquisa e na política brasileira, considerando **as eleições de 2026** e o **debate regulatório sobre IA** no país.

## O estudo de caso

**Quando o Congresso legisla sobre IA, ele quer PUNIR, REGULAR ou PROMOVER?**

- **Corpus:** 304 projetos de lei sobre inteligência artificial, deepfakes e conteúdo sintético (Câmara + Senado, 2019–2026), coletados das APIs de dados abertos em 06/11/2026 (coleta anterior, de 08/10/2026, em `dados/processado/historico/`).
- **Instrumento:** um LLM aberto rodando localmente, o **S5-nano** (Maritaca AI). É um modelo brasileiro, derivado do **Qwen3.5-4B** (Alibaba) com pré-treinamento adicional em dados em português. Usamos o modo *instruct*, quantizado em 4 bits (Q4_K_M) e servido pelo Ollama com o nome `s5-nano-instruct` (`modelos/Modelfile.s5-nano-instruct`), com três versões de prompt.
- **Referência:** as 304 ementas codificadas com um livro de códigos (PUNIR 53 · REGULAR 150 · PROMOVER 56 · OUTRO 45). A codificação é **preliminar** e foi feita por **outra IA** (Claude Opus 5.5), ainda sem revisão humana; 120 dessas ementas, sorteadas, formam a amostra-ouro.
- **Inferência:** quanto da produção legislativa é punitiva, e se isso varia entre campos políticos, com intervalos de confiança que levam em conta o erro do LLM (*Prediction-Powered Inference*).

## Estrutura

```
minicurso_IA_medicao/
├── README.md                  ← este arquivo
├── ROTEIRO.md                 ← cronograma das 4h + preparação do ministrante
├── CODEBOOK.md                ← livro de códigos (PUNIR/REGULAR/PROMOVER/OUTRO + eleitoral)
├── CHECKLIST.md               ← checklist para usar LLM como instrumento de medição
├── _targets.R                 ← pipeline reprodutível (R/{targets})
├── requirements.txt           ← dependências Python
├── R/
│   ├── 00_pacotes.R           ← instala dependências
│   ├── funcoes_coleta.R       ← APIs da Câmara e do Senado
│   ├── funcoes_medicao.R      ← kappa, alfa de Krippendorff, F1, bootstrap, PPI, PPI++
│   ├── tema_graficos.R
│   ├── 01_coleta.R            ← Bloco 1: coleta
│   ├── 02_amostra_ouro.R      ← Bloco 2: amostra-ouro e exercício
│   ├── 03_baselines.R         ← Bloco 3: dicionário e TF-IDF + logística
│   ├── 04_anotacao_llm.R      ← Bloco 4: LLM via Ollama (e ellmer, opcional)
│   ├── 05_validacao.R         ← Bloco 5: validade, viés diferencial, confiabilidade
│   └── 06_inferencia.R        ← Bloco 6: ingênuo × PPI, simulação de cobertura
├── python/                    ← trilha equivalente em Python (notebooks para o Colab)
│   ├── anotar_llm.py          ← anotação com cache e versionamento (usado para gerar os dados)
│   ├── medicao.py
│   └── 01…05_*.ipynb
├── modelos/                   ← Modelfile do instrumento (s5-nano-instruct, Ollama)
├── prompts/                   ← prompts versionados (v1, v2, v3) + CHANGELOG
├── dados/
│   ├── bruto/                 ← respostas das APIs (congeladas)
│   ├── processado/corpus.csv  ← 304 proposições (historico/: coleta de 08/10/2026)
│   ├── anotacoes/             ← referência, amostra-ouro, baselines
│   ├── cache_llm/*.jsonl      ← TODAS as respostas do s5-nano-instruct (brutas + rótulo + metadados)
│   │   └── historico_gemma4-e2b/ ← respostas do instrumento anterior (não entram nas análises)
│   ├── comparacao_modelos/    ← piloto de escolha do modelo (gemma4, qwen3.5, lfm3)
│   └── repeticao/             ← repetição das execuções a t = 0 (teste de reprodutibilidade)
├── resultados/{figuras,tabelas}
├── slides/                    ← slides em Quarto (revealjs)
│   ├── parte1_conceitos.qmd   ← formato A, Parte 1: conceitos, sem resultados (2h)
│   ├── completo_R.qmd         ← formato B: minicurso inteiro com código R e saídas (4h)
│   ├── completo_python.qmd    ← formato B: o mesmo, com código Python
│   └── partes_R/              ← blocos incluídos em completo_R.qmd
├── livro/                     ← fontes do livro (bookdown) · compilar: setwd("livro"); source("build.R")
├── docs/                      ← livro compilado em HTML (pronto para o GitHub Pages)
└── material_apoio/            ← contexto regulatório, exercício de codificação
```

## Principais resultados (corpus coletado e anotado em 06/11/2026; referência preliminar)

| | |
|---|---|
| Melhor LLM (s5-nano-instruct, prompt v2, t = 0) | kappa 0,75 [0,64; 0,85] · acurácia 85% |
| Dicionário (regex, otimista) | kappa 0,70 [0,59; 0,81] |
| Teste-reteste (3 sementes, t = 0,8) | alfa = 1,00 (nenhuma das 304 ementas muda) |
| Sensibilidade ao prompt (v1, v2, v3) | alfa = 0,75 (23% das ementas mudam) |
| Proporção PUNIR: ingênuo | 23,0% [18,3; 27,8] → não cobre a referência (17,4%) |
| Proporção PUNIR: PPI | 20,6% [13,6; 27,6] → cobre (cobertura de 99,1% na simulação) |
| Proporção PUNIR: PPI++ | 19,4% [14,4; 24,5] |
| Cobertura do IC ingênuo na simulação | 0% |

## Como reproduzir

**Sem LLM e sem internet (como em sala):** tudo parte dos dados congelados.

```r
source("R/00_pacotes.R")   # uma vez
targets::tar_make()        # refaz amostra-ouro, baselines, validação, inferência, figuras
```

ou, passo a passo: `Rscript R/02_amostra_ouro.R`, `R/03_baselines.R`, `R/05_validacao.R`, `R/06_inferencia.R`.

**Refazendo a coleta e a anotação:**

```bash
Rscript R/01_coleta.R                       # ~5 min, APIs públicas
ollama pull hf.co/maritaca-ai/S5-nano-GGUF:Q4_K_M                     # S5-nano em 4 bits (~3,5 GB)
ollama create s5-nano-instruct -f modelos/Modelfile.s5-nano-instruct  # nome local, modo instruct
python python/anotar_llm.py --todas         # ~15 min numa GPU de notebook (RTX 4050); Ollama 0.40.15
```

**Python/Colab:** abra os notebooks em `python/`. A primeira célula configura o ambiente.

**Slides:** dentro de `slides/`, `quarto render <deck>.qmd` para cada deck (`slides`, `parte1_conceitos`, `completo_R`, `completo_python`). Os decks completos executam o código a partir dos dados congelados (não chamam as APIs nem o Ollama) e não gravam nada em `dados/` nem em `resultados/`.

## Dois formatos de minicurso

- **A · Conceitos + prática:** 2h com `slides/parte1_conceitos.html` (ideias e desenho, sem resultados) e 2h executando os scripts de `R/` ou os notebooks de `python/`.
- **B · Tudo por slides (4h):** `slides/completo_R.html` ou `slides/completo_python.html`, com o código, o que está sendo executado e as saídas.

O livro também traz, em cada capítulo, uma seção "Mão na massa" com o código em R e em Python (abas no HTML), as saídas e como executar cada bloco.

## Livro do minicurso

O livro (`docs/index.html`) reúne todo o conteúdo do minicurso em HTML, com as tabelas e figuras lidas diretamente dos resultados do pipeline. Para recompilar:

```r
setwd("livro"); source("build.R")   # gera docs/ com o livro, os slides e um .zip do material
```

Para publicar online: suba esta pasta para um repositório no GitHub e ative o GitHub Pages em *Settings → Pages → Deploy from a branch → main /docs*.

## Autoria e uso de inteligência artificial

Este material e o livro foram elaborados por Jodavid Ferreira em **coautoria com o Claude Opus 5.5** (Anthropic, `claude-opus-5-5`), usado via Claude Code como **auxiliar** na escrita e revisão de código, na redação do texto, na verificação da reprodutibilidade e na compilação do livro. As decisões de pesquisa e a revisão final são do autor, que assume **integral responsabilidade** pelo conteúdo. Declaração completa: apêndice "Declaração de uso de inteligência artificial e responsabilidade" do livro.

## Licenças

- **Código** (`R/`, `python/`, `_targets.R`, scripts do livro): [MIT](LICENSE).
- **Texto e demais conteúdos** (livro, slides, livro de códigos, prompts, figuras, dados derivados): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.pt-br).
- Dados brutos das APIs da Câmara e do Senado seguem os termos dessas fontes. Detalhes em [LICENSE.md](LICENSE.md).

## Avisos importantes

1. **A codificação de referência é preliminar e foi feita por outra IA.** `dados/anotacoes/referencia_completa.csv` foi produzida pelo Claude Opus 5.5, aplicando o livro de códigos às ementas, para que o pipeline funcione de ponta a ponta. Enquanto não for revisada, o kappa do S5-nano mede a concordância entre duas IAs. Antes do minicurso ela deve ser **revisada por codificadores humanos** (coluna `revisado`). Até lá, os scripts emitem um aviso e os números são ilustrativos.
2. **O dicionário foi escrito depois de ler as ementas**, então seu desempenho é otimista. Isso é discutido em sala como exemplo de *data leakage*.
3. **Partido "na data":** a API da Câmara traz registros de "partido no início da legislatura" com data de 2023 para legislaturas antigas. O código filtra esses registros (ver `funcoes_coleta.R`).
4. **R e Python dão os mesmos números**, a menos das diferenças do gerador aleatório (ICs bootstrap e simulação de cobertura, diferenças de até 0,01) e do baseline TF-IDF: kappa de 0,41 com `glmnet` (elastic-net + *stemming*) e de 0,51 com `scikit-learn` (L2, sem *stemming*). Bom exemplo, para discussão, de como o "mesmo" método depende da implementação.
5. Chaves de API nunca entram no código: use `~/.Renviron` ou variáveis de ambiente.

## Referências principais

- Angelopoulos, A. N.; Bates, S.; Fannjiang, C.; Jordan, M. I.; Zrnic, T. (2023). Prediction-powered inference. *Science*, 382(6671), 669–674.
- Angelopoulos, A. N.; Duchi, J. C.; Zrnic, T. (2023). PPI++: Efficient prediction-powered inference. *arXiv:2311.01453*.
- Egami, N.; Hinck, M.; Stewart, B. M.; Wei, H. (2023). Using imperfect surrogates for downstream inference: Design-based supervised learning for social science applications of large language models. *NeurIPS*.
- Gilardi, F.; Alizadeh, M.; Kubli, M. (2023). ChatGPT outperforms crowd workers for text-annotation tasks. *PNAS*, 120(30).
- Grimmer, J.; Roberts, M. E.; Stewart, B. M. (2022). *Text as Data*. Princeton University Press.
- Krippendorff, K. (2018). *Content Analysis: An Introduction to Its Methodology* (4ª ed.). SAGE.
- Argyle, L. P. et al. (2023). Out of one, many: Using language models to simulate human samples. *Political Analysis*, 31(3).
- Bolognesi, B.; Ribeiro, E.; Codato, A. (2023). A new ideological classification of Brazilian political parties. *Dados*, 66(2).
- Motoki, F.; Pinho Neto, V.; Rodrigues, V. (2024). More human than human: measuring ChatGPT political bias. *Public Choice*, 198.
- Landau, W. M. (2021). The targets R package. *Journal of Open Source Software*, 6(57), 2959.
