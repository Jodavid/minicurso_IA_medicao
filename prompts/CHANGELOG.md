# Histórico de versões dos prompts

Prompts são **parte do instrumento de medição**: mudar uma vírgula pode mudar a medida.
Por isso eles são versionados como código, e cada anotação salva registra o `prompt_id` e o hash SHA-256 do texto.

| Versão | Arquivo | Mudança | Motivação |
|---|---|---|---|
| v1 | `prompt_v1_simples.txt` | Só os nomes das categorias, sem definições | Linha de base: o que o modelo "entende" sozinho por PUNIR/REGULAR/PROMOVER? |
| v2 | `prompt_v2_codebook.txt` | Inclui as definições e as regras do livro de códigos | Aproximar o LLM do codificador humano treinado |
| v3 | `prompt_v3_fewshot.txt` | v2 + 6 exemplos fictícios | Testar se exemplos (few-shot) melhoram as categorias ambíguas |

Os exemplos do v3 são **fictícios** de propósito, para não vazar casos da amostra-ouro para o modelo.
