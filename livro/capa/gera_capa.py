"""
Gera a capa do livro (capa.svg -> capa.pdf e capa.png, via Inkscape).

A imagem ilustra a ideia do livro: ementas (linhas de texto, à esquerda)
passam por um instrumento de medição (a régua) e viram rótulos (PUNIR,
REGULAR, PROMOVER), que só viram conclusão com um intervalo de confiança.
As proporções e os intervalos do gráfico são decorativos.

Paleta minimalista em tons de azul e cinza/ardósia, alinhada aos gráficos
e aos slides do minicurso.

Uso (a partir da raiz do projeto):
    python livro/capa/gera_capa.py
Requer a fonte Lato e o Inkscape.
"""
import random
import subprocess
from pathlib import Path

AQUI = Path(__file__).resolve().parent
W, H = 1700, 2200                       # proporção de uma página carta (8,5 x 11 pol.)

# Paleta minimalista: azuis profundos, azul-aço e tons de cinza/prata
AZUL_NOITE  = "#0b192c"
AZUL_ESCURO = "#16325b"
AZUL_MEIO   = "#1c3f6e"
AZUL_DESTAQUE = "#5ea1f0"
AZUL_CLARO  = "#8fb8e8"
PRATA       = "#cbd5e1"
CINZA_TEXTO = "#94a3b8"

# PUNIR em azul luminoso (foco substantivo do minicurso), REGULAR em azul-claro, PROMOVER em cinza-prata
CORES = {
    "PUNIR":    "#5ea1f0",
    "REGULAR":  "#9cc0e8",
    "PROMOVER": "#94a3b8",
}
random.seed(2026)

s = []
add = s.append
add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
add(f'''<defs>
  <linearGradient id="fundo" x1="0" y1="0" x2="0.4" y2="1">
    <stop offset="0%" stop-color="{AZUL_MEIO}"/>
    <stop offset="55%" stop-color="{AZUL_ESCURO}"/>
    <stop offset="100%" stop-color="{AZUL_NOITE}"/>
  </linearGradient>
  <linearGradient id="regua" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#1e4477"/>
    <stop offset="100%" stop-color="#0f2440"/>
  </linearGradient>
</defs>
<rect width="{W}" height="{H}" fill="url(#fundo)"/>''')

# Papel milimetrado discreto: a ideia de medida e precisão
for x in range(0, W + 1, 50):
    op = 0.055 if x % 250 == 0 else 0.02
    add(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="#ffffff" stroke-opacity="{op}" stroke-width="1.2"/>')
for y in range(0, H + 1, 50):
    op = 0.055 if y % 250 == 0 else 0.02
    add(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="#ffffff" stroke-opacity="{op}" stroke-width="1.2"/>')

# Moldura geométrica sutil no topo
M = 150
add(f'<line x1="{M}" y1="165" x2="{W - M}" y2="165" stroke="{AZUL_CLARO}" stroke-opacity="0.28" stroke-width="2"/>')
add(f'<rect x="{M}" y="162" width="90" height="6" fill="{AZUL_DESTAQUE}"/>')

FONTE = "font-family:Lato"
def texto(x, y, conteudo, tam, peso=400, cor="#ffffff", extra="", ancora="start", opac=1):
    add(f'<text x="{x}" y="{y}" style="{FONTE};font-size:{tam}px;font-weight:{peso};{extra}" '
        f'fill="{cor}" fill-opacity="{opac}" text-anchor="{ancora}">{conteudo}</text>')

# --- Cabeçalho e título ------------------------------------------------------
texto(M, 245, "II DATAPOL  ·  UFPE  ·  2026", 36, 700, AZUL_CLARO, "letter-spacing:7px")
for i, linha in enumerate(["Inteligência", "Artificial como", "Instrumento", "de Medição"]):
    texto(M - 6, 435 + i * 138, linha, 134, 900, "#ffffff", "letter-spacing:-2px")

# Barra divisória minimalista em dois tons (azul-aço + cinza-prata)
add(f'<rect x="{M}" y="998" width="110" height="8" rx="4" fill="{AZUL_DESTAQUE}"/>')
add(f'<rect x="{M + 126}" y="998" width="44" height="8" rx="4" fill="{PRATA}" fill-opacity="0.5"/>')

texto(M, 1088, "Validação Estatística e Reprodutibilidade", 58, 300, "#dbe7f5", "letter-spacing:0.5px")

# --- Painel da ilustração: ementas -> régua -> rótulos -> intervalos ---------
add(f'<rect x="{M - 30}" y="1175" width="{W - 2 * (M - 30)}" height="640" rx="16" '
    f'fill="#091526" fill-opacity="0.38" stroke="#ffffff" stroke-opacity="0.08" stroke-width="1.5"/>')

Y0, PASSO, N = 1255, 29, 18
cats = ["REGULAR"] * 9 + ["PROMOVER"] * 6 + ["PUNIR"] * 3
random.shuffle(cats)
X_REGUA = 760
alvo = {"PUNIR": 1310, "REGULAR": 1445, "PROMOVER": 1580}      # y de cada rótulo
X_ALVO = 1105

for i, cat in enumerate(cats):
    y = Y0 + i * PASSO
    # a ementa: segmentos de texto de comprimentos variados em cinza-azulado
    x = M + 10
    fim = X_REGUA - 46 - random.randint(0, 150)
    while x < fim:
        comp = min(random.randint(40, 145), fim - x)
        if comp > 12:
            op_barra = 0.48 if cat == "PUNIR" else 0.26
            cor_barra = AZUL_CLARO if cat == "PUNIR" else "#cbd5e1"
            add(f'<rect x="{x}" y="{y - 4.5}" width="{comp}" height="9" rx="4.5" '
                f'fill="{cor_barra}" fill-opacity="{op_barra}"/>')
        x += comp + 13
    # o rótulo: curva da régua até a categoria
    ya = alvo[cat]
    op_curva = 0.88 if cat == "PUNIR" else 0.55
    esp_curva = 3.8 if cat == "PUNIR" else 2.8
    add(f'<path d="M {X_REGUA + 38} {y} C {X_REGUA + 195} {y}, {X_ALVO - 165} {ya}, {X_ALVO} {ya}" '
        f'fill="none" stroke="{CORES[cat]}" stroke-opacity="{op_curva}" stroke-width="{esp_curva}"/>')
    add(f'<circle cx="{X_REGUA + 38}" cy="{y}" r="5.5" fill="{CORES[cat]}" fill-opacity="{op_curva}"/>')

# a régua (o instrumento de medição)
yt, yb = Y0 - 42, Y0 + (N - 1) * PASSO + 42
add(f'<rect x="{X_REGUA - 26}" y="{yt}" width="52" height="{yb - yt}" rx="7" fill="url(#regua)" '
    f'stroke="{AZUL_CLARO}" stroke-opacity="0.85" stroke-width="3"/>')
for j, y in enumerate(range(yt + 18, yb - 10, 15)):
    grande = (j % 5 == 0)
    comp = 26 if grande else 13
    cor_traco = "#ffffff" if grande else AZUL_CLARO
    op_traco = 0.85 if grande else 0.55
    add(f'<line x1="{X_REGUA - 26}" y1="{y}" x2="{X_REGUA - 26 + comp}" y2="{y}" '
        f'stroke="{cor_traco}" stroke-opacity="{op_traco}" stroke-width="{2.6 if grande else 2}"/>')

# os rótulos e seus intervalos de confiança (eixo de 0% a 60%)
EX0, EX1 = 1175, 1515
def px(p):
    return EX0 + (EX1 - EX0) * p / 0.60

for cat, (est, li, ls) in {"PUNIR": (0.17, 0.12, 0.23), "REGULAR": (0.50, 0.43, 0.57),
                           "PROMOVER": (0.30, 0.24, 0.37)}.items():
    y, cor = alvo[cat], CORES[cat]
    destaque = (cat == "PUNIR")
    add(f'<circle cx="{X_ALVO}" cy="{y}" r="10" fill="{cor}"/>')
    add(f'<line x1="{EX0}" y1="{y}" x2="{EX1}" y2="{y}" stroke="#ffffff" stroke-opacity="0.16" stroke-width="2"/>')
    add(f'<line x1="{px(li)}" y1="{y}" x2="{px(ls)}" y2="{y}" stroke="{cor}" stroke-width="7" stroke-linecap="round"/>')
    for xx in (px(li), px(ls)):
        add(f'<line x1="{xx}" y1="{y - 14}" x2="{xx}" y2="{y + 14}" stroke="{cor}" stroke-width="4.5" stroke-linecap="round"/>')
    add(f'<circle cx="{px(est)}" cy="{y}" r="12" fill="{AZUL_NOITE if not destaque else "#ffffff"}" '
        f'stroke="{cor}" stroke-width="5.5"/>')
    texto(EX0, y - 28, cat, 28, 700 if destaque else 600, "#ffffff" if destaque else cor, "letter-spacing:3.5px")

for p in (0, 0.2, 0.4, 0.6):
    add(f'<line x1="{px(p)}" y1="{alvo["PROMOVER"] + 42}" x2="{px(p)}" y2="{alvo["PROMOVER"] + 55}" '
        f'stroke="{PRATA}" stroke-opacity="0.45" stroke-width="2"/>')
    texto(px(p), alvo["PROMOVER"] + 88, f"{int(p * 100)}%", 25, 400, PRATA, ancora="middle", opac=0.65)

# --- Rodapé ------------------------------------------------------------------
add(f'<line x1="{M}" y1="1905" x2="{W - M}" y2="1905" stroke="{PRATA}" stroke-opacity="0.22" stroke-width="1.8"/>')
texto(M, 1980, "Jodavid Ferreira", 52, 700, "#ffffff")
texto(M, 2038, "Departamento de Estatística · UFPE", 34, 400, "#dbe7f5")
texto(M, 2088, "coautoria: Claude Opus 5.5 (IA)", 31, 400, CINZA_TEXTO)
texto(W - M, 1980, "Livro do minicurso", 38, 600, "#dbe7f5", ancora="end")
texto(W - M, 2038, "II DataPOL · CCEN/UFPE", 34, 400, CINZA_TEXTO, ancora="end")
texto(W - M, 2088, "Recife · novembro de 2026", 31, 400, CINZA_TEXTO, ancora="end")
add("</svg>")

svg = AQUI / "capa.svg"
svg.write_text("\n".join(s), encoding="utf-8")
for ext, extra in [("pdf", ["--export-text-to-path"]), ("png", ["--export-width=1700"])]:
    subprocess.run(["inkscape", str(svg), f"--export-filename={AQUI / ('capa.' + ext)}", *extra], check=True,
                   capture_output=True)
print("Capa gerada em", AQUI)
