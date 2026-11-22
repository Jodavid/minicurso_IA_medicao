"""
Funções de coleta, medição, validação e inferência (espelho de R/funcoes_*.R).
Minicurso "IA como Instrumento de Medição" — II DataPOL (UFPE, 2026)

As métricas são implementadas "na mão" de propósito: são poucas linhas e mostram
que não há mágica. Em pesquisa, compare com pacotes (krippendorff, ppi_py).
"""
import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

CATEGORIAS = ["PUNIR", "REGULAR", "PROMOVER", "OUTRO"]
# Instrumento oficial do minicurso: só os caches dele entram nas análises
# (caches de outros modelos, se existirem na pasta, são ignorados)
INSTRUMENTO = "s5-nano-instruct"
PALETA = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
COR_CAT = dict(zip(CATEGORIAS, PALETA[:4]))
# Azuis (escala sequencial clara -> escura) e cinzas: o azul destaca, o cinza é contexto
AZUIS = ["#7ba4de", "#3d7ccc", "#1c3f6e"]
CINZA, CINZA_CLARO, CINZA_ESCURO = "#8f8d88", "#c9c7c2", "#52514e"
# Estimadores: os que corrigem o erro do LLM em azul; os de referência em cinza
COR_EST = {"Só humanos (amostra-ouro)": "#a8a6a1", "Ingênuo (LLM = verdade)": CINZA_ESCURO,
           "PPI": AZUIS[0], "PPI++": AZUIS[2]}
FUNDO, TINTA, TINTA2, GRADE = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"

URL_CAMARA = "https://dadosabertos.camara.leg.br/api/v2"
URL_SENADO = "https://legis.senado.leg.br/dadosabertos"
SESSAO = requests.Session()
SESSAO.headers.update({"Accept": "application/json",
                       "User-Agent": "Minicurso DataPOL/UFPE (fins acadêmicos)"})


# =============================================================================
# Coleta
# =============================================================================
def req_json(url, params=None, tentativas=4):
    """Requisição com retry e pausa (no máximo ~5 requisições/segundo)."""
    for t in range(tentativas):
        try:
            time.sleep(0.2)
            r = SESSAO.get(url, params=params, timeout=60)
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            if t == tentativas - 1:
                raise
            time.sleep(2 ** (t + 1))


def camara_proposicoes(termo, ano, tipos=("PL",)):
    """A API limita intervalos de datas a 3 meses; filtrar por `ano` evita isso."""
    saida, pagina = [], 1
    while True:
        res = req_json(f"{URL_CAMARA}/proposicoes",
                       dict(keywords=termo, ano=ano, siglaTipo=",".join(tipos), itens=100,
                            pagina=pagina, ordem="ASC", ordenarPor="id"))
        saida += res["dados"]
        if len(res["dados"]) < 100:
            break
        pagina += 1
    return pd.DataFrame([dict(id=x["id"], sigla=x["siglaTipo"], numero=x["numero"], ano=x["ano"],
                              ementa=x["ementa"], data_apresentacao=x["dataApresentacao"])
                         for x in saida])


def camara_autor(id_):
    """Primeiro autor (proponente) de uma proposição da Câmara."""
    res = req_json(f"{URL_CAMARA}/proposicoes/{id_}/autores")["dados"]
    if not res:
        return dict(id=id_)
    a = min(res, key=lambda x: x.get("ordemAssinatura") or 99)
    return dict(id=id_, autor=a["nome"], tipo_autor=a["tipo"], uri_autor=a.get("uri"),
                n_autores=len(res))


def camara_partido_na_data(uri_deputado, data_ref):
    """Partido do deputado NA DATA da apresentação (não o partido atual!)."""
    vazio = dict(partido=None, uf=None)
    if not isinstance(uri_deputado, str) or "/deputados/" not in uri_deputado:
        return vazio
    h = req_json(f"{uri_deputado}/historico")["dados"]
    # Atenção: a API inclui registros "Nome/Partido no início da legislatura" com a
    # data de 2023-02-01 para TODAS as legislaturas anteriores (situacao = None).
    # Sem este filtro, um deputado do PL em 2023 aparece como PMDB ou PFL.
    h = sorted([dict(dia=(x.get("dataHora") or "")[:10], partido=x.get("siglaPartido"),
                     uf=x.get("siglaUf"))
                for x in h if x.get("siglaPartido") and x.get("dataHora") and x.get("situacao")],
               key=lambda x: x["dia"])
    if not h:
        return vazio
    antes = [x for x in h if x["dia"] <= str(data_ref)[:10]]
    linha = antes[-1] if antes else h[0]
    return dict(partido=linha["partido"], uf=linha["uf"])


def camara_situacao(id_):
    s = req_json(f"{URL_CAMARA}/proposicoes/{id_}")["dados"]["statusProposicao"]
    return dict(id=id_, situacao=s.get("descricaoSituacao"), data_situacao=s.get("dataHora"))


def senado_processos(termo, ano, sigla="PL"):
    """No Senado, a autoria já vem com partido/UF na data ("Senador Fulano (PSD/MG)")."""
    res = req_json(f"{URL_SENADO}/processo",
                   dict(sigla=sigla, termo=termo, dataInicioApresentacao=f"{ano}-01-01",
                        dataFimApresentacao=f"{ano}-12-31"))
    return pd.DataFrame([dict(id=x["id"], identificacao=x["identificacao"], ementa=x["ementa"],
                              data_apresentacao=x["dataApresentacao"], autoria=x.get("autoria"),
                              situacao=x.get("situacaoAtual"),
                              casa_origem=x.get("casaIdentificadora")) for x in res or []])


def extrai_partido_senado(autoria):
    m = re.search(r"\(([A-Za-zÀ-ú ]+)/([A-Z]{2})\)", autoria or "")
    return (m.group(1), m.group(2)) if m else (None, None)


def limpa_ementa(x):
    x = re.sub(r"[\r\n]+", " ", x)
    x = re.sub(r"(?i)\s*NOVA EMENTA:.*$", "", x)    # mantém a ementa original
    return re.sub(r"\s+", " ", x).strip()


# Campo político: simplificação didática de Bolognesi, Ribeiro & Codato (2023), Dados 66(2).
ESQUERDA = {"PSOL", "PT", "PCDOB", "PDT", "PSB", "REDE", "PV"}
CENTRO = {"MDB", "PSDB", "CIDADANIA", "PSD", "SOLIDARIEDADE", "AVANTE", "PMB"}
DIREITA = {"PL", "PP", "UNIÃO", "REPUBLICANOS", "NOVO", "PSC", "PTB", "PODE", "PODEMOS",
           "PATRIOTA", "PRD", "DEM", "PSL", "PROS", "PRTB", "AGIR", "DC", "PMN", "MOBILIZA"}


def campo_politico(partido):
    if partido in ESQUERDA:
        return "Esquerda"
    if partido in CENTRO:
        return "Centro"
    if partido in DIREITA:
        return "Direita"
    return "Sem partido/Outro"


# =============================================================================
# Leitura dos dados
# =============================================================================
def carrega_corpus(raiz):
    return pd.read_csv(Path(raiz) / "dados/processado/corpus.csv")


def carrega_ouro(raiz):
    ouro = pd.read_csv(Path(raiz) / "dados/anotacoes/amostra_ouro.csv")
    if not ouro["revisado"].any():
        print("AVISO: a amostra-ouro ainda NÃO foi revisada por humanos (coluna `revisado`). "
              "Os resultados são ilustrativos.")
    return ouro


def carrega_llm(raiz, modelo=INSTRUMENTO):
    linhas = []
    for arq in sorted((Path(raiz) / "dados/cache_llm").glob(f"{modelo}__*.jsonl")):
        with arq.open(encoding="utf-8") as f:
            linhas += [json.loads(l) for l in f if l.strip()]
    return pd.DataFrame(linhas)


def rotulo_run(run_id):
    m = re.search(r"__(v\d)__t([0-9.]+)__s(\d+)", run_id)
    p, t, s = m.groups()
    if t == "0.0":
        return f"LLM {p} (t=0)" if s == "42" else f"LLM {p} (t=0, s={s})"
    return f"LLM {p} (t={t}, s={s})"


# Stopwords em português (mesma lista de tm::stopwords("portuguese") no R)
STOPWORDS_PT = sorted(set("""
de a o que e do da em um para com não uma os no se na por mais as dos como mas ao ele
das à seu sua ou quando muito nos já eu também só pelo pela até isso ela entre depois
sem mesmo aos seus quem nas me esse eles você essa num nem suas meu às minha numa pelos
elas qual nós lhe deles essas esses pelas este dele tu te vocês vos lhes meus minhas teu
tua teus tuas nosso nossa nossos nossas dela delas esta estes estas aquele aquela
aqueles aquelas isto aquilo estou está estamos estão estive esteve estivemos estiveram
estava estávamos estavam estivera estivéramos esteja estejamos estejam estivesse
estivéssemos estivessem estiver estivermos estiverem hei há havemos hão houve houvemos
houveram houvera houvéramos haja hajamos hajam houvesse houvéssemos houvessem houver
houvermos houverem houverei houverá houveremos houverão houveria houveríamos houveriam
sou somos são era éramos eram fui foi fomos foram fora fôramos seja sejamos sejam fosse
fôssemos fossem for formos forem serei será seremos serão seria seríamos seriam tenho
tem temos tém tinha tínhamos tinham tive teve tivemos tiveram tivera tivéramos tenha
tenhamos tenham tivesse tivéssemos tivessem tiver tivermos tiverem terei terá teremos
terão teria teríamos teriam
""".split()))


# =============================================================================
# Baseline de dicionário (regras explícitas, totalmente auditáveis)
# =============================================================================
REGEX = dict(
    punir=r"c[oó]digo penal|\bpenas?\b|\bcrimes?\b|criminaliz|tipific|hediond",
    ia=(r"intelig[eê]ncia artificial|\bia\b|algor[ií]tm|automatiz|automa[cç][aã]o|"
        r"sint[eé]tic|deep ?fake|deepvoice|manipula|chatbot|reconhecimento facial|"
        r"aut[oô]nom|\binteligente|réplicas? digit|simul"),
    promover=(r"incentiv|fomento|\bfundo\b|curr[ií]cul|ensino|educa[cç]|capacita|"
              r"forma[cç][aã]o|pesquisa|desenvolvimento da|programa nacional|institui o sistema|"
              r"obrigatoriedade d[eo] uso|utiliza[cç][aã]o de (ferramentas|tecnologias|sistemas)"),
    eleitoral=r"elei[cç]|eleitora|campanhas? eleitora|candidat|propaganda pol|democr|violência política",
)


def classifica_dicionario(ementa):
    x = ementa.lower()
    tem_ia = re.search(REGEX["ia"], x)
    if re.search(REGEX["punir"], x) and tem_ia:
        return "PUNIR"
    if not tem_ia:
        return "OUTRO"
    if re.search(REGEX["promover"], x):
        return "PROMOVER"
    return "REGULAR"


def eleitoral_dicionario(ementa):
    return bool(re.search(REGEX["eleitoral"], ementa.lower()))


# =============================================================================
# Métricas de acerto e concordância
# =============================================================================
def _validos(a, b):
    a, b = pd.Series(a).reset_index(drop=True), pd.Series(b).reset_index(drop=True)
    ok = a.notna() & b.notna()
    return a[ok].astype(str).values, b[ok].astype(str).values


def kappa_cohen(a, b):
    a, b = _validos(a, b)
    n = len(a)
    po = np.mean(a == b)
    pe = sum(np.sum(a == c) * np.sum(b == c) for c in CATEGORIAS) / n ** 2
    if n == 0 or pe == 1:   # kappa indefinido (ex.: amostra com uma só categoria)
        return float("nan")
    return (po - pe) / (1 - pe)


def alfa_krippendorff(m):
    """Alfa de Krippendorff (nominal) para k codificadores; aceita NA.
    `m`: matriz (DataFrame ou array) unidades × codificadores."""
    m = pd.DataFrame(m)
    valores = sorted({v for v in m.values.ravel() if pd.notna(v)})
    idx = {v: i for i, v in enumerate(valores)}
    o = np.zeros((len(valores), len(valores)))
    for _, linha in m.iterrows():
        v = [x for x in linha if pd.notna(x)]
        mu = len(v)
        if mu < 2:
            continue
        for i in range(mu):
            for j in range(mu):
                if i != j:
                    o[idx[v[i]], idx[v[j]]] += 1 / (mu - 1)
    nc = o.sum(axis=1)
    n = o.sum()
    Do = (n - np.trace(o)) / n
    De = (n ** 2 - np.sum(nc ** 2)) / (n * (n - 1))
    return 1 - Do / De


def f1_macro(verdade, pred):
    v, p = np.asarray(verdade, dtype=object), np.asarray(pred, dtype=object)
    f1s = []
    for c in CATEGORIAS:
        tp = np.sum((p == c) & (v == c))
        fp = np.sum((p == c) & (v != c))
        fn = np.sum((p != c) & (v == c))
        f1s.append(0 if tp == 0 else 2 * tp / (2 * tp + fp + fn))
    return float(np.mean(f1s))


def resumo_metricas(verdade, pred):
    v = pd.Series(verdade).reset_index(drop=True)
    p = pd.Series(pred).reset_index(drop=True)
    ok = p.notna()
    return dict(n=int(v.notna().sum()),
                falhas_formato=float(p.isna().mean()),
                acuracia=float((v[ok].astype(str) == p[ok].astype(str)).mean()),
                f1_macro=f1_macro(v.astype(str), p.astype(str)),
                kappa=float(kappa_cohen(v, p)))


def boot_ic(verdade, pred, fun=kappa_cohen, B=2000, semente=2026):
    """Intervalo bootstrap percentil para qualquer métrica de (verdade, pred)."""
    rng = np.random.default_rng(semente)
    v, p = np.asarray(verdade, dtype=object), np.asarray(pred, dtype=object)
    n = len(v)
    est = []
    for _ in range(B):
        i = rng.integers(0, n, n)
        est.append(fun(v[i], p[i]))
    return np.nanquantile(est, [0.025, 0.975])


# =============================================================================
# Inferência com rótulos imperfeitos
#   y_n : rótulo humano (0/1) na amostra-ouro (n)
#   f_n : rótulo do LLM (0/1) na amostra-ouro
#   f_N : rótulo do LLM (0/1) nos documentos NÃO rotulados (N)
# =============================================================================
Z = 1.959963984540054


def ic_normal(est, ep):
    return dict(estimativa=est, ep=ep, li=est - Z * ep, ls=est + Z * ep)


def est_humano(y_n):
    """(a) Só humanos: sem viés, mas com pouca precisão."""
    y_n = np.asarray(y_n, float)
    return ic_normal(y_n.mean(), y_n.std(ddof=1) / np.sqrt(len(y_n)))


def est_ingenuo(f_todos):
    """(b) Ingênuo: trata o rótulo do LLM como verdade em TODO o corpus."""
    f = np.asarray(f_todos, float)
    return ic_normal(f.mean(), f.std(ddof=1) / np.sqrt(len(f)))


def est_ppi(y_n, f_n, f_N):
    """(c) Prediction-Powered Inference (Angelopoulos et al., 2023, Science)."""
    y_n, f_n, f_N = (np.asarray(x, float) for x in (y_n, f_n, f_N))
    ret = f_n - y_n
    est = f_N.mean() - ret.mean()
    ep = np.sqrt(f_N.var(ddof=1) / len(f_N) + ret.var(ddof=1) / len(y_n))
    return ic_normal(est, ep)


def est_ppi_plus(y_n, f_n, f_N):
    """(d) PPI++ (Angelopoulos, Duchi & Zrnic, 2023): ajusta o peso λ do LLM."""
    y_n, f_n, f_N = (np.asarray(x, float) for x in (y_n, f_n, f_N))
    n, N = len(y_n), len(f_N)
    f_todos = np.concatenate([f_n, f_N])
    lam = np.cov(y_n, f_n, ddof=1)[0, 1] / ((1 + n / N) * f_todos.var(ddof=1))
    lam = float(min(max(lam, 0), 1))
    est = y_n.mean() + lam * (f_N.mean() - f_n.mean())
    ep = np.sqrt((y_n - lam * f_n).var(ddof=1) / n + lam ** 2 * f_N.var(ddof=1) / N)
    return {**ic_normal(est, ep), "lambda": lam}


def compara_estimadores(y_n, f_n, f_N):
    linhas = [
        {"estimador": "Só humanos (amostra-ouro)", **est_humano(y_n)},
        {"estimador": "Ingênuo (LLM = verdade)", **est_ingenuo(np.concatenate([f_n, f_N]))},
        {"estimador": "PPI", **est_ppi(y_n, f_n, f_N)},
        {"estimador": "PPI++", **est_ppi_plus(y_n, f_n, f_N)},
    ]
    return pd.DataFrame(linhas)


# =============================================================================
# Gráficos
# =============================================================================
def estilo_graficos():
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.facecolor": FUNDO, "axes.facecolor": FUNDO, "savefig.facecolor": FUNDO,
        "axes.edgecolor": GRADE, "axes.grid": True, "grid.color": GRADE, "grid.linewidth": .5,
        "axes.spines.top": False, "axes.spines.right": False,
        "text.color": TINTA, "axes.labelcolor": TINTA, "xtick.color": TINTA2, "ytick.color": TINTA2,
        "font.size": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "figure.dpi": 110,
    })
