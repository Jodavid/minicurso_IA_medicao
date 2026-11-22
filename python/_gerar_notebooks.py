import sys
from pathlib import Path
import nbformat as nbf

DEST = Path(sys.argv[1])

SETUP = '''# === Configuração: funciona localmente e no Google Colab ===
import os, sys, subprocess
from pathlib import Path

# PROVISÓRIO: endereço do repositório público do minicurso (ajustar quando publicado)
REPO_URL = "https://github.com/jodavid/minicurso-ia-medicao"

EM_COLAB = "google.colab" in sys.modules
if EM_COLAB:
    if not Path("minicurso-ia-medicao").exists():
        subprocess.run(["git", "clone", "-q", REPO_URL], check=True)
    RAIZ = Path("minicurso-ia-medicao").resolve()
else:
    # localmente: a raiz é a pasta do minicurso (este notebook fica em python/)
    RAIZ = Path.cwd().parent if Path.cwd().name == "python" else Path.cwd()

os.chdir(RAIZ)
sys.path.insert(0, str(RAIZ / "python"))
SAIDA = RAIZ / "resultados" / "python"          # o R grava em resultados/; o Python, aqui
(SAIDA / "figuras").mkdir(parents=True, exist_ok=True)
(SAIDA / "tabelas").mkdir(parents=True, exist_ok=True)
print("Raiz do projeto:", RAIZ)'''


def nb(celulas):
    n = nbf.v4.new_notebook()
    n.metadata = {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                  "language_info": {"name": "python"}, "colab": {"provenance": []}}
    n.cells = [nbf.v4.new_markdown_cell(c[3:]) if c.startswith("md:") else nbf.v4.new_code_cell(c)
               for c in celulas]
    return n


def md(t):
    return "md:" + t.strip("\n")


# =============================================================================
coleta = [
md('''
# Bloco 1: Coleta de dados legislativos sobre Inteligência Artificial
**Minicurso "IA como Instrumento de Medição": II DataPOL (UFPE, 2026)**

Câmara dos Deputados + Senado Federal, 2019–2026, via APIs de dados abertos.

**Pergunta de pesquisa do minicurso:**
> *Quando o Congresso legisla sobre IA, ele quer PUNIR, REGULAR ou PROMOVER? Isso mudou com as eleições (2022, 2024, 2026) e difere entre campos políticos?*

Saída: `dados/processado/corpus.csv`. A coleta completa leva de 5 a 10 minutos (são centenas de chamadas às APIs). Em sala usamos o arquivo já salvo; este notebook documenta **como** ele foi gerado (reprodutibilidade).
'''),
SETUP,
'''import pandas as pd
from datetime import date
from medicao import (camara_proposicoes, camara_autor, camara_situacao, camara_partido_na_data,
                     senado_processos, extrai_partido_senado, limpa_ementa, campo_politico)''',
md('''
## Parâmetros

`MODO_TESTE = True` coleta só um termo e um ano (rápido, para ver o mecanismo funcionando) e salva em `resultados/python/`.
Com `MODO_TESTE = False`, a coleta é completa e **sobrescreve** `dados/processado/corpus.csv`.
'''),
'''MODO_TESTE = True

TERMOS = ["inteligência artificial", "deepfake", "deep fake", "conteúdo sintético"]
ANOS = list(range(2019, 2027))
if MODO_TESTE:
    TERMOS, ANOS = ["deepfake"], [2024]
DATA_COLETA = date.today().isoformat()''',
md('''
## 1. Câmara dos Deputados

A API limita intervalos de datas a 3 meses; por isso filtramos por `ano`, que não tem essa restrição.
'''),
'''camara = pd.concat([camara_proposicoes(t, a) for t in TERMOS for a in ANOS], ignore_index=True)
camara = camara.drop_duplicates("id")
print(len(camara), "proposições na Câmara")

autores = pd.DataFrame([camara_autor(i) for i in camara["id"]])
situacao = pd.DataFrame([camara_situacao(i) for i in camara["id"]])
camara = camara.merge(autores, on="id", how="left").merge(situacao, on="id", how="left")''',
md('''
### Partido **na data** da apresentação

Detalhe que muda a medida e costuma ser ignorado: o partido atual do deputado não é o partido que ele tinha quando apresentou o projeto. Além disso, o histórico da API traz registros "Partido no início da legislatura" com data de 2023-02-01 para **todas** as legislaturas anteriores (com `situacao` nula). Sem filtrá-los, um deputado do PL em 2023 aparece como PMDB ou PFL.
'''),
'''partidos = pd.DataFrame([camara_partido_na_data(u, d)
                         for u, d in zip(camara["uri_autor"], camara["data_apresentacao"])])
camara = pd.concat([camara.reset_index(drop=True), partidos], axis=1)
camara.head()''',
md('## 2. Senado Federal\n\nNo Senado, a autoria já vem com partido e UF na data ("Senador Fulano (PSD/MG)").'),
'''lst = [x for x in (senado_processos(t, a) for t in TERMOS for a in ANOS) if len(x)]
senado = pd.concat(lst, ignore_index=True).drop_duplicates("id") if lst else pd.DataFrame()
print(len(senado), "processos no Senado")''',
md('## 3. Corpus unificado'),
'''camara_pad = pd.DataFrame(dict(
    casa="Câmara",
    identificacao=camara["sigla"] + " " + camara["numero"].astype(str) + "/" + camara["ano"].astype(str),
    ano=camara["ano"], data_apresentacao=camara["data_apresentacao"].str[:10],
    ementa=camara["ementa"], autor=camara.get("autor"), tipo_autor=camara.get("tipo_autor"),
    partido=camara["partido"], uf=camara["uf"], situacao=camara["situacao"]))

if len(senado):
    ps = senado["autoria"].apply(extrai_partido_senado)
    senado_pad = pd.DataFrame(dict(
        casa="Senado", identificacao=senado["identificacao"],
        ano=senado["data_apresentacao"].str[:4].astype(int),
        data_apresentacao=senado["data_apresentacao"], ementa=senado["ementa"],
        autor=senado["autoria"].str.replace(r"\\s*\\(.*\\)$", "", regex=True),
        tipo_autor=senado["autoria"].fillna("").str.startswith("Senador").map({True: "Senador(a)", False: "Outro"}),
        partido=[p for p, _ in ps], uf=[u for _, u in ps], situacao=senado["situacao"]))
else:
    senado_pad = pd.DataFrame(columns=camara_pad.columns)

# Projetos do Senado remetidos à Câmara aparecem nas duas casas (ex.: PL 2338/2023).
# Mantemos o registro da casa de origem (Senado vem primeiro), que traz o partido na data.
corpus = (pd.concat([senado_pad, camara_pad], ignore_index=True)
          .drop_duplicates("identificacao")
          .assign(ementa=lambda d: d["ementa"].map(limpa_ementa),
                  partido=lambda d: d["partido"].str.strip().str.upper()))
corpus = corpus[corpus["ano"].isin(ANOS) & (corpus["ementa"].str.len() > 20)]
corpus = corpus.sort_values("data_apresentacao").reset_index(drop=True)
corpus.insert(0, "doc_id", [f"doc{i:04d}" for i in range(1, len(corpus) + 1)])''',
md('''
## 4. Campo político

Simplificação didática a partir de Bolognesi, Ribeiro & Codato (2023), *A New Ideological Classification of Brazilian Political Parties*, Dados 66(2). Ela própria é uma **medida**, com erro e escolhas; discutimos isso em sala.
'''),
'''corpus["campo"] = corpus["partido"].map(campo_politico)
corpus["ano_eleitoral"] = corpus["ano"] % 2 == 0      # 2020, 2022, 2024, 2026
corpus["data_coleta"] = DATA_COLETA

destino = (SAIDA / "corpus_teste.csv") if MODO_TESTE else (RAIZ / "dados/processado/corpus.csv")
corpus.to_csv(destino, index=False)
print(f"Corpus: {len(corpus)} proposições salvas em {destino}")
corpus.groupby(["casa", "ano"]).size()''',
'''corpus[["doc_id", "casa", "identificacao", "partido", "campo", "ementa"]].head(10)''',
]

# =============================================================================
baselines = [
md('''
# Bloco 2: Baselines clássicos
**Antes de usar um LLM, quanto se acerta sem ele?**

1. **Dicionário**: regras explícitas (regex). Barato, transparente, auditável.
2. **TF-IDF + regressão logística multinomial** com penalização, avaliada por validação cruzada na amostra-ouro (n = 120).

Mensagem: um LLM só "vale a pena" se superar esses baselines de forma consistente, e isso é uma afirmação estatística, não uma impressão.
'''),
SETUP,
'''import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegressionCV
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from medicao import (CATEGORIAS, STOPWORDS_PT, carrega_corpus, carrega_ouro, classifica_dicionario,
                     eleitoral_dicionario, resumo_metricas)

corpus = carrega_corpus(RAIZ)
ouro = carrega_ouro(RAIZ).merge(corpus[["doc_id", "ementa"]], on="doc_id")
ouro["categoria"].value_counts()''',
md('''
## 1. Dicionário

**Atenção (ponto para discussão):** as regras foram escritas depois de **ler** as ementas do corpus. O dicionário "viu a prova", e seu desempenho aqui é otimista. Num estudo real, as regras são definidas antes ou validadas em dados novos (ex.: proposições apresentadas depois da data de coleta).
'''),
'''ouro["pred_dic"] = ouro["ementa"].map(classifica_dicionario)
print(resumo_metricas(ouro["categoria"], ouro["pred_dic"]))
pd.crosstab(ouro["categoria"], ouro["pred_dic"], rownames=["humano"], colnames=["dicionário"])''',
md('''
## 2. TF-IDF + regressão logística (validação cruzada 10-fold)

As previsões são *out-of-fold*: cada ementa é classificada por um modelo que **não** a viu no treino. O parâmetro de regularização é escolhido por uma validação cruzada interna (5-fold).
'''),
'''modelo = make_pipeline(
    TfidfVectorizer(lowercase=True, stop_words=STOPWORDS_PT, min_df=2,
                    token_pattern=r"(?u)\\b[^\\W\\d_]{2,}\\b"),
    LogisticRegressionCV(Cs=10, cv=5, max_iter=5000, scoring="accuracy"),
)
dobras = StratifiedKFold(n_splits=10, shuffle=True, random_state=2026)
ouro["pred_ml"] = cross_val_predict(modelo, ouro["ementa"], ouro["categoria"], cv=dobras)

maj = pd.Series(["REGULAR"] * len(ouro))
baselines = pd.DataFrame([
    {"metodo": "Dicionário (regex)", **resumo_metricas(ouro["categoria"], ouro["pred_dic"])},
    {"metodo": "TF-IDF + logística (CV 10)", **resumo_metricas(ouro["categoria"], ouro["pred_ml"])},
    {"metodo": "Classe majoritária (REGULAR)", **resumo_metricas(ouro["categoria"], maj)},
])
baselines.round(3)''',
'''baselines.to_csv(SAIDA / "tabelas/baselines.csv", index=False)
ouro[["doc_id", "categoria", "pred_dic", "pred_ml"]].to_csv(SAIDA / "tabelas/predicoes_baselines.csv", index=False)

# Dicionário aplicado a TODO o corpus (usado como "instrumento barato" no Bloco 5)
pd.DataFrame({"doc_id": corpus["doc_id"],
              "categoria_dic": corpus["ementa"].map(classifica_dicionario),
              "eleitoral_dic": corpus["ementa"].map(eleitoral_dicionario)}
             ).to_csv(SAIDA / "tabelas/dicionario_corpus.csv", index=False)''',
md('''
### Para discutir
* Por que o modelo supervisionado, com 120 exemplos, fica **abaixo** do dicionário?
* Quantos exemplos rotulados seriam necessários para ele superar as regras? Quanto custa produzi-los?
* Que erros do dicionário são **sistemáticos** (sempre na mesma direção)?
'''),
]

# =============================================================================
anotacao = [
md('''
# Bloco 3: O LLM como instrumento de medição
**Anotação com modelo aberto local (Ollama) ou comercial, sempre com cache e versionamento.**

Em sala **não** precisamos rodar a anotação completa: as anotações já estão em `dados/cache_llm/` (geradas com `python/anotar_llm.py`). Este notebook mostra o mecanismo e permite testar outro modelo ou prompt.

Cada chamada fica registrada com modelo, prompt, hash do prompt, temperatura, semente, resposta bruta e tempo. Se o processo for interrompido, ele continua de onde parou.
'''),
SETUP,
md('''
## 1. (Só no Colab) Instalar e iniciar o Ollama

Use um ambiente com **GPU** (Ambiente de execução → Alterar o tipo → T4 GPU). O instrumento é o **S5-nano** (Maritaca AI) em modo *instruct*, quantizado em 4 bits: o download tem ~3,5 GB e leva alguns minutos. O `ollama create` dá a ele o nome local `s5-nano-instruct` (ver `modelos/Modelfile.s5-nano-instruct`). (Por que este modelo? É um modelo brasileiro, derivado do Qwen3.5-4B e treinado com dados em português; veja o capítulo 5 do livro.)
'''),
'''if EM_COLAB:
    subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True, check=True)
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import time; time.sleep(5)
    subprocess.run(["ollama", "pull", "hf.co/maritaca-ai/S5-nano-GGUF:Q4_K_M"], check=True)
    subprocess.run(["ollama", "create", "s5-nano-instruct", "-f", "modelos/Modelfile.s5-nano-instruct"], check=True)''',
md('## 2. O Ollama está respondendo?'),
'''import requests
OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
try:
    modelos = [m["name"] for m in requests.get(f"{OLLAMA}/api/tags", timeout=5).json()["models"]]
    print("Modelos disponíveis:", modelos)
except Exception as e:
    print("Ollama indisponível:", e)''',
md('''
## 3. Os prompts são parte do instrumento

Mudar uma vírgula pode mudar a medida. Por isso os prompts estão versionados em `prompts/` e cada anotação guarda o hash SHA-256 do texto.
'''),
'''import anotar_llm as al
for pid, arq in al.PROMPTS.items():
    texto = arq.read_text(encoding="utf-8")
    print(f"{pid}: {arq.name}  sha={al.sha(texto)}  ({len(texto)} caracteres)")
print()
print(al.PROMPTS["v2"].read_text(encoding="utf-8"))''',
md('''
## 4. Anotar algumas ementas

Usamos uma **semente diferente** da usada no material (42), para não misturar o seu experimento com o cache oficial. Troque `MODELO`, `PROMPT`, `TEMPERATURA` e observe como os rótulos mudam.
'''),
'''import pandas as pd
from medicao import carrega_corpus

MODELO, PROMPT, TEMPERATURA, SEMENTE, N_TESTE = "s5-nano-instruct", "v2", 0.0, 7, 5

corpus = carrega_corpus(RAIZ)
arq = al.anota(corpus.head(N_TESTE), MODELO, PROMPT, TEMPERATURA, SEMENTE)
res = pd.read_json(arq, lines=True)
res.merge(corpus[["doc_id", "ementa"]], on="doc_id")[["doc_id", "categoria_llm", "eleitoral_llm", "segundos", "ementa"]]''',
md('''
Note a coluna `resposta_bruta`: modelos pequenos às vezes devolvem o JSON entre crases (```` ```json ````) ou com texto extra. Respostas fora do formato viram `None`, e a **taxa de falhas de formato** também é uma propriedade do instrumento.
'''),
'''res[["doc_id", "resposta_bruta"]].head()''',
md('''
## 5. O plano de experimentos do material

O cache oficial foi gerado com `python python/anotar_llm.py --todas`:

| Execução | Prompt | Temperatura | Semente | Para quê |
|---|---|---|---|---|
| 1 | v1 (só nomes das categorias) | 0 | 42 | linha de base do LLM |
| 2 | v2 (livro de códigos) | 0 | 42 | validade |
| 3 | v3 (livro de códigos + exemplos) | 0 | 42 | efeito do *few-shot* |
| 4–6 | v2 | 0,8 | 1, 2, 3 | teste-reteste (confiabilidade) |
'''),
'''from medicao import carrega_llm
llm = carrega_llm(RAIZ)
llm.groupby("run_id").agg(n=("doc_id", "size"), falhas=("categoria_llm", lambda s: s.isna().mean()),
                          seg_mediano=("segundos", "median"))''',
md('''
## 6. (Opcional) API comercial

A chave **nunca** vai no código nem no GitHub: use variável de ambiente (no Colab, em *Secrets*). APIs comerciais trocam a versão do modelo sem aviso: registre a data, o identificador exato do modelo e guarde as respostas brutas.
'''),
'''if os.environ.get("OPENAI_API_KEY"):
    from openai import OpenAI
    cliente = OpenAI()
    prompt = al.PROMPTS["v2"].read_text(encoding="utf-8").replace("{{ementa}}", corpus["ementa"][0])
    r = cliente.chat.completions.create(
        model="gpt-4.1-mini", temperature=0, seed=42,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}])
    print(r.model, r.choices[0].message.content)
else:
    print("OPENAI_API_KEY não definida: célula ignorada.")''',
]

# =============================================================================
validacao = [
md('''
# Bloco 4: Validação
**O instrumento mede o que diz medir? Com que erro?**

* 4.1 **Validade**: concordância com a amostra-ouro (acurácia, F1, kappa + IC)
* 4.2 **Onde erra**: matriz de confusão
* 4.3 **Viés diferencial**: o erro é igual entre campos políticos?
* 4.4 **Confiabilidade**: teste-reteste (sementes) e sensibilidade ao prompt
* 4.5 Concordância **humano × humano** (exercício em sala)
'''),
SETUP,
'''import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency
from medicao import (CATEGORIAS, PALETA, COR_CAT, AZUIS, CINZA, CINZA_CLARO, CINZA_ESCURO, COR_EST, TINTA, TINTA2, GRADE, carrega_corpus, carrega_ouro,
                     carrega_llm, rotulo_run, resumo_metricas, boot_ic, alfa_krippendorff, estilo_graficos)
estilo_graficos()

corpus = carrega_corpus(RAIZ)
ouro = carrega_ouro(RAIZ)
llm = carrega_llm(RAIZ)
# Execuções oficiais do material: semente 42 (t=0) e 1–3 (t=0,8). Execuções extras
# (ex.: seu teste no notebook 03 com semente 7) aparecem como instrumentos à parte.
llm["instrumento"] = llm["run_id"].map(rotulo_run)

arq_base = SAIDA / "tabelas/predicoes_baselines.csv"      # gerado no notebook 02
if not arq_base.exists():
    arq_base = RAIZ / "dados/anotacoes/predicoes_baselines.csv"   # versão gerada pelo R
base_l = pd.read_csv(arq_base)''',
md('## 4.1 Validade'),
'''aval = llm.merge(ouro[["doc_id", "categoria"]], on="doc_id")

linhas = []
for nome, v, p in [("Dicionário (regex)", base_l["categoria"], base_l["pred_dic"]),
                   ("TF-IDF + logística (CV 10)", base_l["categoria"], base_l["pred_ml"])]:
    li, ls = boot_ic(v, p)
    linhas.append({"instrumento": nome, **resumo_metricas(v, p), "kappa_li": li, "kappa_ls": ls})
for nome, d in aval.groupby("instrumento"):
    li, ls = boot_ic(d["categoria"], d["categoria_llm"])
    linhas.append({"instrumento": nome, **resumo_metricas(d["categoria"], d["categoria_llm"]),
                   "kappa_li": li, "kappa_ls": ls})
metricas = pd.DataFrame(linhas).sort_values("kappa", ascending=False).reset_index(drop=True)
metricas.to_csv(SAIDA / "tabelas/validade_instrumentos.csv", index=False)
metricas.round(3)''',
'''m = metricas.sort_values("kappa")
cores = [AZUIS[2] if i.startswith("LLM") else CINZA for i in m["instrumento"]]
fig, ax = plt.subplots(figsize=(9, 0.45 * len(m) + 1.6))
for x in (.4, .6, .8):
    ax.axvline(x, color=GRADE, ls="--", lw=1)
ax.hlines(m["instrumento"], m["kappa_li"], m["kappa_ls"], colors=cores, lw=3)
ax.scatter(m["kappa"], m["instrumento"], color=cores, s=60, zorder=3)
ax.set_xlim(0, 1); ax.set_xlabel("Kappa de Cohen")
ax.set_title("Validade: concordância de cada instrumento com a amostra-ouro")
ax.text(0, -0.13, "Kappa com IC 95% bootstrap (n = 120). Azul: LLM (S5-nano instruct, local) · Laranja: baseline clássico.",
        transform=ax.transAxes, color=TINTA2, fontsize=9)
fig.tight_layout(); fig.savefig(SAIDA / "figuras/01_validade_kappa.png", dpi=200)''',
md('## 4.2 Matriz de confusão do melhor LLM com temperatura 0'),
'''llm_t0 = metricas[metricas["instrumento"].str.contains(r"t=0\\)")]
melhor = llm_t0.iloc[0]["instrumento"]
d = aval[aval["instrumento"] == melhor].copy()
d["categoria_llm"] = d["categoria_llm"].fillna("(falha)")
colunas = CATEGORIAS + (["(falha)"] if (d["categoria_llm"] == "(falha)").any() else [])
conf = pd.crosstab(pd.Categorical(d["categoria"], CATEGORIAS), pd.Categorical(d["categoria_llm"], colunas),
                   rownames=["humano"], colnames=["llm"], dropna=False)
prop = conf.div(conf.sum(axis=1), axis=0)

fig, ax = plt.subplots(figsize=(7.5, 5))
ax.imshow(prop.values, cmap=plt.matplotlib.colors.LinearSegmentedColormap.from_list("azul", ["#eef4fc", AZUIS[2]]), vmin=0, vmax=1)
for i in range(conf.shape[0]):
    for j in range(conf.shape[1]):
        ax.text(j, i, conf.values[i, j], ha="center", va="center",
                color="white" if prop.values[i, j] > .5 else TINTA, fontsize=12)
ax.set_xticks(range(len(colunas)), colunas); ax.set_yticks(range(len(CATEGORIAS)), CATEGORIAS)
ax.set_xlabel("Rótulo do LLM"); ax.set_ylabel("Rótulo humano"); ax.grid(False)
ax.set_title(f"Onde o instrumento erra: {melhor}")
fig.tight_layout(); fig.savefig(SAIDA / "figuras/02_matriz_confusao.png", dpi=200)
conf''',
md('''
## 4.3 Viés diferencial

Pergunta: o LLM erra mais para um campo político? Se sim, comparações entre campos feitas com rótulos do LLM estarão enviesadas, **mesmo com acurácia alta**.
'''),
'''dif = d.merge(corpus[["doc_id", "campo", "casa"]], on="doc_id")
dif["acerto"] = dif["categoria"] == dif["categoria_llm"]
dif["punir_h"] = dif["categoria"] == "PUNIR"
dif["punir_l"] = dif["categoria_llm"] == "PUNIR"
dif = dif[dif["campo"] != "Sem partido/Outro"]

vies = dif.groupby("campo").agg(n=("acerto", "size"), acuracia=("acerto", "mean"),
                                prop_punir_humano=("punir_h", "mean"), prop_punir_llm=("punir_l", "mean"))
vies["vies_punir"] = vies["prop_punir_llm"] - vies["prop_punir_humano"]
vies["ep"] = np.sqrt(vies["acuracia"] * (1 - vies["acuracia"]) / vies["n"])
vies["li"], vies["ls"] = vies["acuracia"] - 1.96 * vies["ep"], vies["acuracia"] + 1.96 * vies["ep"]
vies.to_csv(SAIDA / "tabelas/vies_diferencial_campo.csv")

# Teste formal: o acerto depende do campo? (qui-quadrado; no R usamos regressão logística)
qui = chi2_contingency(pd.crosstab(dif["campo"], dif["acerto"]))
print(f"Qui-quadrado = {qui.statistic:.2f}, gl = {qui.dof}, p = {qui.pvalue:.3f}")
vies.round(3)''',
'''v = vies.sort_values("acuracia")
fig, ax = plt.subplots(figsize=(9, 3.6))
ax.hlines(v.index, v["li"].clip(0), v["ls"].clip(upper=1), color=AZUIS[2], lw=3)
ax.scatter(v["acuracia"], v.index, color=AZUIS[2], s=60, zorder=3)
for campo, r in v.iterrows():
    ax.annotate(f"n = {int(r.n)}", (r.acuracia, campo), xytext=(0, 9), textcoords="offset points",
                ha="center", color=TINTA2, fontsize=9)
ax.set_xlim(0, 1); ax.xaxis.set_major_formatter(plt.matplotlib.ticker.PercentFormatter(1))
ax.set_title("Viés diferencial: o acerto do LLM varia por campo político do autor?")
ax.set_xlabel(f"Acurácia na amostra-ouro com IC 95% ({melhor})")
fig.tight_layout(); fig.savefig(SAIDA / "figuras/03_vies_diferencial.png", dpi=200)''',
md('''
## 4.4 Confiabilidade

**(a) Teste-reteste:** mesmo prompt (v2), temperatura 0,8, três sementes. Não precisa de rótulo humano: mede só a estabilidade do instrumento.

**(b) Sensibilidade ao prompt:** v1, v2 e v3 com temperatura 0.

Confiabilidade não é validade: um instrumento pode ser perfeitamente estável e sistematicamente errado.
'''),
'''def instabilidade(largo):
    return np.mean([len(set(x.dropna())) > 1 for _, x in largo.iterrows()])

largo_seed = (llm[(llm["prompt_id"] == "v2") & (llm["temperatura"] > 0)]
              .pivot(index="doc_id", columns="semente", values="categoria_llm"))
largo_prompt = (llm[(llm["temperatura"] == 0) & (llm["semente"] == 42)]
                .pivot(index="doc_id", columns="prompt_id", values="categoria_llm"))

linhas = []
if largo_seed.shape[1] >= 2:
    linhas.append(dict(comparacao="Teste-reteste (v2, t=0,8, sementes)", n_execucoes=largo_seed.shape[1],
                       alfa_krippendorff=alfa_krippendorff(largo_seed),
                       prop_ementas_que_mudam=instabilidade(largo_seed)))
if largo_prompt.shape[1] >= 2:
    linhas.append(dict(comparacao="Sensibilidade ao prompt (t=0)", n_execucoes=largo_prompt.shape[1],
                       alfa_krippendorff=alfa_krippendorff(largo_prompt),
                       prop_ementas_que_mudam=instabilidade(largo_prompt)))
confiab = pd.DataFrame(linhas)
confiab.to_csv(SAIDA / "tabelas/confiabilidade.csv", index=False)
confiab.round(3)''',
'''ref = pd.read_csv(RAIZ / "dados/anotacoes/referencia_completa.csv")
dist = (llm[(llm["temperatura"] == 0) & (llm["semente"] == 42)].assign(cat=lambda x: x["categoria_llm"].fillna("(falha)"))
        .groupby("prompt_id")["cat"].value_counts(normalize=True).unstack(fill_value=0))
dist.loc["Referência\\nhumana"] = ref["categoria"].value_counts(normalize=True)
dist = dist.fillna(0)[[c for c in CATEGORIAS + ["(falha)"] if c in dist.columns]]

# Um painel por categoria: cada prompt (azuis, do v1 claro ao v3 escuro) contra a referência humana (cinza)
dist = dist.loc[:, (dist > 0).any()]
cores_fonte = [AZUIS[0], AZUIS[1], AZUIS[2], CINZA]
fig, axs = plt.subplots(1, dist.shape[1], figsize=(9, 3.8), sharey=True, sharex=True)
for ax, c in zip(axs, dist.columns):
    ax.barh(dist.index[::-1], dist[c].values[::-1], color=cores_fonte[::-1], height=.7)
    ax.set_title(c, loc="left", fontsize=10, fontweight="bold")
    ax.set_xticks([0, .3, .6]); ax.set_xlim(0, .65)
    ax.xaxis.set_major_formatter(plt.matplotlib.ticker.PercentFormatter(1, decimals=0))
    ax.grid(axis="y", visible=False)
    for lado in ("top", "right", "left"): ax.spines[lado].set_visible(False)
    ax.set_axisbelow(True); ax.tick_params(length=0)
fig.suptitle("Mesmo modelo, mesmos textos, prompts diferentes: medidas diferentes", x=.01, ha="left", fontweight="bold")
fig.tight_layout(); fig.savefig(SAIDA / "figuras/04_sensibilidade_prompt.png", dpi=200)
dist.round(3)''',
md('### Variável eleitoral'),
'''ele = llm[(llm["temperatura"] == 0) & (llm["semente"] == 42)].merge(ouro[["doc_id", "eleitoral"]], on="doc_id")
ele["eleitoral_llm"] = ele["eleitoral_llm"].astype("boolean")
tab = ele.groupby("prompt_id").apply(lambda g: pd.Series(dict(
    n_eleitoral_humano=int(g["eleitoral"].sum()),
    n_eleitoral_llm=int(g["eleitoral_llm"].fillna(False).sum()),
    sensibilidade=g.loc[g["eleitoral"] == 1, "eleitoral_llm"].mean(),
    especificidade=(~g.loc[g["eleitoral"] == 0, "eleitoral_llm"]).mean())))
tab.to_csv(SAIDA / "tabelas/validade_eleitoral.csv")
tab''',
md('''
## 4.5 Humano × humano (exercício em sala)

Cada participante preenche `material_apoio/exercicio_codificacao.csv` e salva como `material_apoio/respostas/<nome>.csv`. Aqui calculamos o alfa entre os humanos, para comparar com o alfa LLM × referência nas mesmas 20 ementas.
'''),
'''arqs = sorted((RAIZ / "material_apoio/respostas").glob("*.csv"))
if len(arqs) >= 2:
    resp = pd.concat([pd.read_csv(a).assign(codificador=a.stem) for a in arqs])
    resp["categoria"] = resp["categoria"].str.strip().str.upper()
    m = resp.pivot(index="doc_id", columns="codificador", values="categoria")
    print(f"Alfa de Krippendorff entre {len(arqs)} codificadores humanos: {alfa_krippendorff(m):.3f}")
else:
    print("Ainda não há respostas suficientes em material_apoio/respostas/ (mínimo: 2).")''',
]

# =============================================================================
inferencia = [
md('''
# Bloco 5: Inferência com rótulos imperfeitos

**Pergunta substantiva:** que proporção dos projetos sobre IA quer **PUNIR**? E essa proporção difere entre campos políticos?

Quatro estimadores:

| Estimador | Ideia |
|---|---|
| **Só humanos** | usa apenas a amostra-ouro: sem viés, IC largo |
| **Ingênuo** | trata o LLM como verdade no corpus todo: IC estreito... e errado? |
| **PPI** | LLM no corpus todo, corrigido pelo erro medido na amostra-ouro (Angelopoulos et al., 2023, *Science*) |
| **PPI++** | como o PPI, mas pondera o LLM conforme sua qualidade (λ) |

Com $y$ = rótulo humano, $f$ = rótulo do LLM, $n$ = amostra-ouro e $N$ = não rotulados:

$$\\hat\\theta_{PPI} = \\underbrace{\\bar f_N}_{\\text{LLM no não rotulado}} - \\underbrace{(\\bar f_n - \\bar y_n)}_{\\text{viés medido no ouro}}, \\qquad \\widehat{\\mathrm{EP}} = \\sqrt{\\tfrac{s^2_{f_N}}{N} + \\tfrac{s^2_{f-y}}{n}}$$

Como este é um corpus didático com referência completa (304 ementas), sabemos a "verdade" e podemos checar quem acerta, e com que frequência (simulação).
'''),
SETUP,
'''import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from medicao import (CATEGORIAS, PALETA, COR_CAT, AZUIS, CINZA, CINZA_CLARO, CINZA_ESCURO, COR_EST, TINTA2, carrega_corpus, carrega_ouro, carrega_llm,
                     compara_estimadores, resumo_metricas, estilo_graficos)
estilo_graficos()
pct = plt.matplotlib.ticker.PercentFormatter(1)

corpus = carrega_corpus(RAIZ)
ouro = carrega_ouro(RAIZ)
ref = pd.read_csv(RAIZ / "dados/anotacoes/referencia_completa.csv")
llm = carrega_llm(RAIZ)
llm = llm[(llm["temperatura"] > 0) | (llm["semente"] == 42)]   # só as execuções oficiais do material''',
md('''
## Instrumento escolhido

O de melhor kappa com temperatura 0 no Bloco 4 (lido da tabela do notebook 04; se ela não existir, recalculado aqui), considerando só execuções que cobrem o corpus inteiro.
'''),
'''n_corpus = len(corpus)
cobertura = llm[llm["temperatura"] == 0].groupby("prompt_id")["doc_id"].nunique()
completos = cobertura[cobertura == n_corpus].index.tolist()
aval = llm[(llm["temperatura"] == 0) & llm["prompt_id"].isin(completos)].merge(ouro[["doc_id", "categoria"]], on="doc_id")
kappas = {p: resumo_metricas(g["categoria"], g["categoria_llm"])["kappa"] for p, g in aval.groupby("prompt_id")}
PROMPT = max(kappas, key=kappas.get)
print("Execuções completas:", completos, "| kappas:", {k: round(v, 3) for k, v in kappas.items()})
print(f"Instrumento usado: s5-nano-instruct, prompt {PROMPT}, temperatura 0")

dados = (corpus[["doc_id", "ano", "campo", "casa"]]
         .merge(llm[(llm["prompt_id"] == PROMPT) & (llm["temperatura"] == 0)][["doc_id", "categoria_llm"]],
                on="doc_id", how="left")
         .merge(ref[["doc_id", "categoria"]].rename(columns={"categoria": "categoria_ref"}), on="doc_id"))
dados["na_ouro"] = dados["doc_id"].isin(ouro["doc_id"])
dados["f"] = (dados["categoria_llm"] == "PUNIR").astype(int)   # falha de formato conta como "não PUNIR"
dados["y"] = np.where(dados["na_ouro"], (dados["categoria_ref"] == "PUNIR").astype(int), np.nan)
verdade = (ref["categoria"] == "PUNIR").mean()
print(f"Proporção PUNIR na referência completa: {verdade:.3f}")''',
md('## 5.1 Proporção de projetos punitivos'),
'''lab, unl = dados[dados["na_ouro"]], dados[~dados["na_ouro"]]
est = compara_estimadores(lab["y"].values, lab["f"].values, unl["f"].values).assign(verdade=verdade)
est.to_csv(SAIDA / "tabelas/estimativas_punir.csv", index=False)
est.round(3)''',
'''e = est.iloc[::-1]
fig, ax = plt.subplots(figsize=(9, 3.6))
ax.axvline(verdade, color=CINZA_ESCURO, lw=1.5, ls="--")
ax.text(verdade, 0.45, " valor na referência completa", color=TINTA2, fontsize=9)
ax.hlines(e["estimador"], e["li"], e["ls"], color=e["estimador"].map(COR_EST), lw=3)
ax.scatter(e["estimativa"], e["estimador"], color=e["estimador"].map(COR_EST), s=60, zorder=3)
ax.xaxis.set_major_formatter(pct)
ax.set_title("Que proporção dos projetos sobre IA quer PUNIR?")
ax.set_xlabel(f"Estimativas com IC 95% · amostra-ouro n = {len(lab)} · não rotulados N = {len(unl)}")
fig.tight_layout(); fig.savefig(SAIDA / "figuras/05_estimadores_punir.png", dpi=200)''',
md('## 5.2 Por campo político do autor'),
'''linhas = []
for campo, d in dados[dados["campo"].isin(["Esquerda", "Centro", "Direita"])].groupby("campo"):
    l, u = d[d["na_ouro"]], d[~d["na_ouro"]]
    linhas.append(compara_estimadores(l["y"].values, l["f"].values, u["f"].values)
                  .assign(campo=campo, n_ouro=len(l), verdade=(d["categoria_ref"] == "PUNIR").mean()))
por_campo = pd.concat(linhas, ignore_index=True)
por_campo.to_csv(SAIDA / "tabelas/estimativas_punir_campo.csv", index=False)
por_campo.round(3)''',
'''ests = ["Só humanos (amostra-ouro)", "Ingênuo (LLM = verdade)", "PPI"]
cores = COR_EST
fig, axs = plt.subplots(3, 1, figsize=(9, 6.5), sharex=True)
for ax, campo in zip(axs, ["Centro", "Direita", "Esquerda"]):
    d = por_campo[(por_campo["campo"] == campo) & por_campo["estimador"].isin(ests)].iloc[::-1]
    ax.axvline(d["verdade"].iloc[0], color=CINZA_ESCURO, lw=1.2, ls="--")
    for _, r in d.iterrows():
        ax.hlines(r.estimador, max(r.li, 0), r.ls, color=cores[r.estimador], lw=3)
        ax.scatter(r.estimativa, r.estimador, color=cores[r.estimador], s=50, zorder=3)
    ax.set_title(f"{campo} (amostra-ouro n = {d['n_ouro'].iloc[0]})", fontsize=10)
axs[-1].xaxis.set_major_formatter(pct)
fig.suptitle("Proporção de projetos PUNIR por campo político do autor (linha tracejada: referência)",
             x=0.01, ha="left", fontweight="bold")
fig.tight_layout(); fig.savefig(SAIDA / "figuras/06_punir_por_campo.png", dpi=200)''',
md('''
## 5.3 Simulação: cobertura e largura dos ICs

Repetimos o sorteio da amostra-ouro muitas vezes. Um bom IC de 95% deve conter a verdade em ~95% das repetições.
'''),
'''def simula(n_ouro, B=1000, semente=1):
    rng = np.random.default_rng(semente)
    y_todos = (dados["categoria_ref"] == "PUNIR").astype(int).values
    f_todos = dados["f"].values
    res = []
    for _ in range(B):
        idx = rng.choice(len(dados), n_ouro, replace=False)
        mask = np.zeros(len(dados), bool); mask[idx] = True
        res.append(compara_estimadores(y_todos[mask], f_todos[mask], f_todos[~mask]))
    r = pd.concat(res)
    r["cobre"] = (r["li"] <= verdade) & (verdade <= r["ls"])
    r["largura"] = r["ls"] - r["li"]
    return (r.groupby("estimador", sort=False)
             .agg(cobertura=("cobre", "mean"), largura_media=("largura", "mean"), media=("estimativa", "mean"))
             .assign(vies=lambda x: x["media"] - verdade, n_ouro=n_ouro).drop(columns="media").reset_index())

sim = pd.concat([simula(n) for n in (30, 60, 120)], ignore_index=True)
sim.to_csv(SAIDA / "tabelas/simulacao_cobertura.csv", index=False)
sim.round(3)''',
'''cores = COR_EST
fig, axs = plt.subplots(1, 2, figsize=(12, 4.6))
for nome, d in sim.groupby("estimador", sort=False):
    axs[0].plot(d["n_ouro"].astype(str), d["cobertura"], "o-", color=cores[nome], lw=2, label=nome)
    axs[1].plot(d["n_ouro"].astype(str), d["largura_media"], "o-", color=cores[nome], lw=2, label=nome)
axs[0].axhline(.95, color=TINTA2, ls="--"); axs[0].set_ylim(0, 1.02)
axs[0].set_title("Com que frequência o IC de 95% contém a verdade?")
axs[1].set_title("Preço da honestidade: largura média do IC")
for ax in axs:
    ax.yaxis.set_major_formatter(pct); ax.set_xlabel("Tamanho da amostra-ouro")
axs[0].legend(frameon=False, fontsize=9, loc="lower right")
fig.tight_layout(); fig.savefig(SAIDA / "figuras/07_08_simulacao.png", dpi=200)''',
md('''
### Para discutir
* O estimador ingênuo tem o IC mais estreito. Por que isso **não** é uma virtude?
* Quando o PPI++ se aproxima do "só humanos"? (dica: olhe o `lambda`)
* Se o LLM tivesse viés diferencial por campo, qual estimador protegeria a comparação entre campos?
'''),
'''# Retrato descritivo: a explosão legislativa sobre IA
tab = (corpus.merge(ref[["doc_id", "categoria"]], on="doc_id").query("ano >= 2023")
       .pivot_table(index="ano", columns="categoria", values="doc_id", aggfunc="count", fill_value=0)[CATEGORIAS])
# Um painel por categoria; PUNIR (a pergunta do minicurso) em azul, o resto em cinza
fig, axs = plt.subplots(1, 4, figsize=(9, 4.4), sharey=True)
for ax, c in zip(axs, CATEGORIAS):
    ax.bar(tab.index.astype(str), tab[c], color=AZUIS[2] if c == "PUNIR" else CINZA_CLARO, width=.7)
    ax.set_title(c, loc="left", fontsize=10, fontweight="bold")
    ax.grid(axis="x", visible=False)
    for lado in ("top", "right", "left"): ax.spines[lado].set_visible(False)
    ax.set_axisbelow(True); ax.tick_params(length=0)
axs[0].set_ylabel("Projetos")
fig.suptitle("Projetos de lei sobre IA no Congresso (Câmara + Senado), por categoria", x=.01, ha="left", fontweight="bold")
fig.tight_layout(); fig.savefig(SAIDA / "figuras/00_projetos_por_ano.png", dpi=200)
tab''',
]

for nome, cel in [("01_coleta", coleta), ("02_baselines", baselines), ("03_anotacao_llm", anotacao),
                  ("04_validacao", validacao), ("05_inferencia", inferencia)]:
    nbf.write(nb(cel), DEST / f"{nome}.ipynb")
    print("escrito", nome)
