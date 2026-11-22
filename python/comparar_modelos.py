"""
Escolha do instrumento: compara modelos abertos candidatos na amostra-ouro.

Etapa 1 (validade): cada modelo anota as 120 ementas da amostra-ouro com os
três prompts (t = 0, semente 42) -> resultados/tabelas/comparacao_modelos.csv.

Etapa 2 (confiabilidade): prompt v2 com t = 0,8 e sementes 1, 2, 3 (teste-reteste)
e uma repetição idêntica do v3 com t = 0 -> comparacao_modelos_confiabilidade.csv.
A sensibilidade ao prompt usa as execuções v1, v2, v3 da etapa 1.

As respostas brutas ficam em dados/comparacao_modelos/.

Escolher o modelo olhando a amostra-ouro é uma decisão de pesquisa que precisa
ser registrada: a amostra-ouro passa a ter sido usada para *selecionar* o
instrumento, e não só para validá-lo (ver o capítulo de validação do livro).

Uso (com o Ollama rodando e os modelos baixados):
    python python/comparar_modelos.py
    python python/comparar_modelos.py --modelos qwen3.5:4b gemma4:e2b
    python python/comparar_modelos.py --etapa confiabilidade   # só a etapa 2

Comparação feita em 06/11/2026 (Ollama 0.40.15, RTX 4050 Laptop 6 GB), com a amostra-ouro
sorteada do corpus de 08/10/2026 (guardada em dados/comparacao_modelos/amostra_ouro_selecao.csv).
Rodar o script de novo usa a amostra-ouro atual (dados/anotacoes/amostra_ouro.csv).
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "python"))
import anotar_llm as A  # noqa: E402
import medicao as M  # noqa: E402

CANDIDATOS = ["gemma4:e2b", "qwen3.5:2b", "qwen3.5:4b", "lfm3:1.7b"]


def memoria_ollama(modelo):
    """Tamanho do modelo carregado e onde ele roda (GPU/CPU), segundo `ollama ps`."""
    try:
        saida = subprocess.run(["ollama", "ps"], capture_output=True, text=True).stdout
    except FileNotFoundError:
        return "", ""
    for linha in saida.splitlines()[1:]:
        partes = linha.split()
        if partes and partes[0] == modelo:
            return " ".join(partes[2:4]), " ".join(partes[4:6])
    return "", ""


def anota_ouro(docs, modelo, prompt_id, temperatura, semente):
    modelo_prompt = A.PROMPTS[prompt_id].read_text(encoding="utf-8")
    regs = []
    for row in docs.itertuples():
        t0 = time.time()
        try:
            bruto = A.chama_ollama(modelo, modelo_prompt.replace("{{ementa}}", row.ementa), temperatura, semente)
        except Exception as e:
            bruto = f"ERRO: {e}"
        cat, ele = A.extrai_rotulo(bruto)
        regs.append(dict(doc_id=row.doc_id, modelo=modelo, prompt_id=prompt_id,
                         prompt_sha=A.sha(modelo_prompt), temperatura=temperatura, semente=semente,
                         resposta_bruta=bruto, categoria_llm=cat, eleitoral_llm=ele,
                         segundos=round(time.time() - t0, 3)))
    return pd.DataFrame(regs)


def le(destino, tag, sufixo):
    return pd.read_json(destino / f"{tag}__{sufixo}.jsonl", lines=True).set_index("doc_id").categoria_llm


def confiabilidade(modelos, docs, destino):
    linhas = []
    for modelo in modelos:
        tag = modelo.replace(":", "-").replace("/", "-")
        A.chama_ollama(modelo, 'Responda {"categoria": "OUTRO", "eleitoral": false}', 0.0, 42)
        for p, t, s, suf in [("v2", 0.8, 1, "v2__t0.8__s1"), ("v2", 0.8, 2, "v2__t0.8__s2"),
                             ("v2", 0.8, 3, "v2__t0.8__s3"), ("v3", 0.0, 42, "v3__repeticao")]:
            anota_ouro(docs, modelo, p, t, s).to_json(destino / f"{tag}__{suf}.jsonl", orient="records",
                                                       lines=True, force_ascii=False)
        reteste = pd.concat([le(destino, tag, f"v2__t0.8__s{s}") for s in (1, 2, 3)], axis=1)
        repeticao = pd.concat([le(destino, tag, "v3"), le(destino, tag, "v3__repeticao")], axis=1)
        prompts = pd.concat([le(destino, tag, p) for p in ("v1", "v2", "v3")], axis=1)
        linhas.append(dict(
            modelo=modelo,
            alfa_reteste=M.alfa_krippendorff(reteste), muda_reteste=(reteste.nunique(axis=1) > 1).mean(),
            alfa_repeticao_t0=M.alfa_krippendorff(repeticao), muda_repeticao_t0=(repeticao.nunique(axis=1) > 1).mean(),
            alfa_prompts=M.alfa_krippendorff(prompts), muda_prompts=(prompts.nunique(axis=1) > 1).mean()))
        print(pd.DataFrame(linhas).tail(1).round(3).to_string(index=False, header=len(linhas) == 1))
    res = pd.DataFrame(linhas)
    res.to_csv(RAIZ / "resultados" / "tabelas" / "comparacao_modelos_confiabilidade.csv", index=False)
    print("\n", res.round(3).to_string(index=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelos", nargs="+", default=CANDIDATOS)
    ap.add_argument("--etapa", choices=["todas", "validade", "confiabilidade"], default="todas")
    a = ap.parse_args()

    corpus = M.carrega_corpus(RAIZ)
    ouro = M.carrega_ouro(RAIZ)
    docs = corpus[corpus.doc_id.isin(ouro.doc_id)]
    destino = RAIZ / "dados" / "comparacao_modelos"
    destino.mkdir(exist_ok=True)
    if a.etapa in ("todas", "validade"):
        validade(a.modelos, docs, ouro, destino)
    if a.etapa in ("todas", "confiabilidade"):
        confiabilidade(a.modelos, docs, destino)


def validade(modelos, docs, ouro, destino):
    linhas = []
    for modelo in modelos:
        A.chama_ollama(modelo, 'Responda {"categoria": "OUTRO", "eleitoral": false}', 0.0, 42)  # carrega
        memoria, processador = memoria_ollama(modelo)
        for p in ["v1", "v2", "v3"]:
            r = anota_ouro(docs, modelo, p, 0.0, 42)
            tag = modelo.replace(":", "-").replace("/", "-")
            r.to_json(destino / f"{tag}__{p}.jsonl", orient="records", lines=True, force_ascii=False)

            m = ouro.merge(r, on="doc_id")
            verd, pred = m.categoria.tolist(), m.categoria_llm.tolist()
            li, ls = M.boot_ic(verd, pred)
            ok = m.eleitoral_llm.notna()
            linhas.append(dict(
                modelo=modelo, prompt=p, n=len(m), falhas_formato=int(m.categoria_llm.isna().sum()),
                acuracia=(m.categoria == m.categoria_llm).mean(), f1_macro=M.f1_macro(verd, pred),
                kappa=M.kappa_cohen(verd, pred), kappa_li=li, kappa_ls=ls,
                acuracia_eleitoral=(m.eleitoral[ok].astype(bool) == m.eleitoral_llm[ok].astype(bool)).mean(),
                seg_mediano=r.segundos.median(), memoria=memoria, processador=processador))
            print(pd.DataFrame(linhas).tail(1).round(3).to_string(index=False, header=len(linhas) == 1))

    res = pd.DataFrame(linhas)
    res.to_csv(RAIZ / "resultados" / "tabelas" / "comparacao_modelos.csv", index=False)
    print("\n", res.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
