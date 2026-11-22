"""
BLOCO 3: o LLM como instrumento de medição (anotação com cache e versionamento).

Instrumento: S5-nano (Maritaca AI) em modo instruct, quantizado em 4 bits e rodando
localmente no Ollama com o nome `s5-nano-instruct` (ver modelos/Modelfile.s5-nano-instruct).

Cada chamada fica registrada em dados/cache_llm/<run_id>.jsonl com:
modelo, digest dos pesos, versão do Ollama, prompt_id, hash do prompt, temperatura, semente,
resposta bruta, rótulo extraído e tempo de execução. Se o script for interrompido, ele
continua de onde parou (as anotações já feitas não são refeitas).

Preparação (uma vez):
    ollama pull hf.co/maritaca-ai/S5-nano-GGUF:Q4_K_M
    ollama create s5-nano-instruct -f modelos/Modelfile.s5-nano-instruct

Uso:
    python python/anotar_llm.py --prompt v2 --temperatura 0 --semente 42
    python python/anotar_llm.py --todas      # roda o plano de experimentos do minicurso
    python python/anotar_llm.py --todas-t0 --pasta dados/repeticao   # repete as execuções a t = 0

Requer o Ollama rodando localmente (https://ollama.com) ou em OLLAMA_HOST.
"""
import argparse
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

RAIZ = Path(__file__).resolve().parents[1]
OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
CATEGORIAS = ["PUNIR", "REGULAR", "PROMOVER", "OUTRO"]
PROMPTS = {
    "v1": RAIZ / "prompts" / "prompt_v1_simples.txt",
    "v2": RAIZ / "prompts" / "prompt_v2_codebook.txt",
    "v3": RAIZ / "prompts" / "prompt_v3_fewshot.txt",
}
ESQUEMA = {
    "type": "object",
    "properties": {
        "categoria": {"type": "string", "enum": CATEGORIAS},
        "eleitoral": {"type": "boolean"},
    },
    "required": ["categoria", "eleitoral"],
}

# Plano de experimentos usado para gerar os dados do minicurso
PLANO = [
    dict(prompt="v1", temperatura=0.0, semente=42),
    dict(prompt="v2", temperatura=0.0, semente=42),
    dict(prompt="v3", temperatura=0.0, semente=42),
    # teste-reteste: mesmo prompt, temperatura > 0, sementes diferentes
    dict(prompt="v2", temperatura=0.8, semente=1),
    dict(prompt="v2", temperatura=0.8, semente=2),
    dict(prompt="v2", temperatura=0.8, semente=3),
]


def sha(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]


def extrai_rotulo(resposta: str):
    """Extrai o JSON da resposta. Modelos pequenos às vezes devolvem ```json ... ```
    ou texto extra; contar essas falhas também faz parte da avaliação do instrumento."""
    m = re.search(r"\{.*?\}", resposta, flags=re.S)
    if not m:
        return None, None
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None, None
    cat = str(d.get("categoria", d.get("classificacao", ""))).strip().upper()
    ele = d.get("eleitoral")
    if isinstance(ele, str):
        ele = ele.strip().lower() in ("true", "sim", "1")
    return (cat if cat in CATEGORIAS else None), (bool(ele) if ele is not None else None)


def versao_ollama():
    """O software que executa o modelo também faz parte do instrumento."""
    try:
        return requests.get(f"{OLLAMA}/api/version", timeout=5).json().get("version")
    except Exception:
        return None


def digest_modelo(modelo):
    """Digest dos pesos no Ollama: o nome local (s5-nano-instruct) pode apontar para
    pesos diferentes em máquinas diferentes; o digest, não."""
    try:
        for m in requests.get(f"{OLLAMA}/api/tags", timeout=5).json().get("models", []):
            if m["name"] in (modelo, f"{modelo}:latest"):
                return m.get("digest", "")[:12]
    except Exception:
        pass
    return None


def chama_ollama(modelo, prompt, temperatura, semente, timeout=120):
    """Modo instruct: "think": False em toda chamada. O S5-nano tem também um modo
    que raciocina antes de responder; se vier raciocínio, a chamada é tratada como erro."""
    r = requests.post(
        f"{OLLAMA}/api/chat",
        json={
            "model": modelo,
            "stream": False,
            "think": False,
            "format": ESQUEMA,
            "options": {"temperature": temperatura, "seed": semente},
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=timeout,
    )
    r.raise_for_status()
    msg = r.json()["message"]
    if msg.get("thinking"):
        raise RuntimeError("o modelo devolveu raciocínio: o modo instruct não foi respeitado")
    return msg["content"]


def anota(corpus, modelo, prompt_id, temperatura, semente, pasta="dados/cache_llm"):
    modelo_tag = modelo.replace(":", "-").replace("/", "-")
    run_id = f"{modelo_tag}__{prompt_id}__t{temperatura}__s{semente}"
    destino = RAIZ / pasta / f"{run_id}.jsonl"
    destino.parent.mkdir(parents=True, exist_ok=True)
    feitos = set()
    if destino.exists():
        feitos = {json.loads(l)["doc_id"] for l in destino.open(encoding="utf-8")}
    modelo_prompt = PROMPTS[prompt_id].read_text(encoding="utf-8")
    prompt_sha = sha(modelo_prompt)
    versao = versao_ollama()
    digest = digest_modelo(modelo)
    pendentes = corpus[~corpus.doc_id.isin(feitos)]
    print(f"[{run_id}] {len(feitos)} em cache, {len(pendentes)} pendentes")
    with destino.open("a", encoding="utf-8") as f:
        for i, row in enumerate(pendentes.itertuples(), 1):
            prompt = modelo_prompt.replace("{{ementa}}", row.ementa)
            t0 = time.time()
            try:
                bruto = chama_ollama(modelo, prompt, temperatura, semente)
            except Exception as e:  # registra a falha em vez de parar tudo
                bruto = f"ERRO: {e}"
            cat, ele = extrai_rotulo(bruto)
            f.write(json.dumps({
                "doc_id": row.doc_id, "run_id": run_id, "modelo": modelo, "modelo_digest": digest, "ollama_versao": versao,
                "prompt_id": prompt_id, "prompt_sha": prompt_sha,
                "temperatura": temperatura, "semente": semente,
                "resposta_bruta": bruto, "categoria_llm": cat, "eleitoral_llm": ele,
                "segundos": round(time.time() - t0, 3),
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }, ensure_ascii=False) + "\n")
            f.flush()
            if i % 25 == 0:
                print(f"  {i}/{len(pendentes)}")
    return destino


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default="s5-nano-instruct")
    ap.add_argument("--prompt", choices=list(PROMPTS), default="v2")
    ap.add_argument("--temperatura", type=float, default=0.0)
    ap.add_argument("--semente", type=int, default=42)
    ap.add_argument("--todas", action="store_true", help="roda o PLANO completo")
    ap.add_argument("--todas-t0", action="store_true", help="só as execuções do PLANO com temperatura 0")
    ap.add_argument("--pasta", default="dados/cache_llm",
                    help="pasta de destino; use outra (ex.: dados/repeticao) para repetir uma execução sem misturá-la ao cache")
    ap.add_argument("--n", type=int, default=None, help="só as n primeiras ementas (teste)")
    a = ap.parse_args()

    corpus = pd.read_csv(RAIZ / "dados" / "processado" / "corpus.csv")
    if a.n:
        corpus = corpus.head(a.n)
    if a.todas:
        plano = PLANO
    elif a.todas_t0:
        plano = [p for p in PLANO if p["temperatura"] == 0]
    else:
        plano = [dict(prompt=a.prompt, temperatura=a.temperatura, semente=a.semente)]
    for p in plano:
        anota(corpus, a.modelo, p["prompt"], p["temperatura"], p["semente"], a.pasta)


if __name__ == "__main__":
    main()
