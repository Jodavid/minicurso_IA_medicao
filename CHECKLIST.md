# Checklist: usar um LLM como instrumento de medição

Use antes de submeter um artigo (ou de confiar num resultado) que dependa de rótulos produzidos por IA.

## A. Antes de anotar
- [ ] A **pergunta de pesquisa** e o **conceito** a medir estão definidos sem depender do LLM?
- [ ] Existe um **livro de códigos** escrito, com definições, regras de decisão e exemplos?
- [ ] O livro de códigos foi testado com **codificadores humanos** e a concordância entre eles foi medida (alfa de Krippendorff)? Se humanos não concordam, o LLM não tem um alvo.
- [ ] A **amostra-ouro** é **aleatória** e de tamanho justificado (custo × precisão)?
- [ ] Há um **baseline barato** (dicionário, modelo clássico) para comparar?

## B. Durante a anotação
- [ ] **Modelo** identificado exatamente (nome, versão, *tag*/*hash*, data de acesso) e **software que o executa** (ex.: versão do Ollama).
- [ ] A **escolha do modelo** está documentada (candidatos, critério, dados usados)? Se a amostra-ouro foi usada para escolher, o kappa do vencedor é otimista.
- [ ] **Prompt** versionado como código (arquivo + hash), incluindo os exemplos *few-shot*.
- [ ] **Parâmetros** registrados: temperatura, semente, formato de saída.
- [ ] **Respostas brutas** guardadas (não só o rótulo extraído).
- [ ] **Falhas de formato** contadas e tratadas de forma explícita (não descartadas em silêncio).
- [ ] Dados sensíveis? Preferir **modelo local**; checar termos de uso da API.

## C. Validação
- [ ] **Validade**: acurácia, F1 macro e kappa contra a amostra-ouro, **com intervalo de confiança**.
- [ ] **Matriz de confusão** inspecionada: em quais categorias o modelo erra?
- [ ] **Viés diferencial**: o erro é parecido entre os grupos que serão comparados (partidos, regiões, períodos)?
- [ ] **Confiabilidade**: teste-reteste (sementes/temperatura) e sensibilidade ao prompt.
- [ ] O LLM supera os baselines **de forma estatisticamente consistente**?

## D. Inferência
- [ ] As estimativas finais **corrigem o erro de medição** (PPI, DSL ou similar), em vez de tratar o rótulo do LLM como verdade?
- [ ] Os ICs relatados incorporam a incerteza da amostra-ouro?
- [ ] Resultados por subgrupo relatam o **tamanho da amostra-ouro em cada grupo**?

## E. Reprodutibilidade (MLOps)
- [ ] Ambiente congelado (`renv.lock` / `requirements.txt` / Docker).
- [ ] Pipeline declarativo (`targets`, Makefile, DVC) que refaz só o que mudou.
- [ ] Dados brutos **congelados** com data de coleta (APIs públicas mudam).
- [ ] Cache das respostas do LLM incluído no pacote de replicação.
- [ ] README explica como reproduzir **sem** acesso ao LLM (a partir do cache) e **com** ele.

## F. Quando NÃO usar um LLM
- O conceito não tem definição operacional clara (o LLM vai inventar uma).
- Não há como montar uma amostra-ouro (então não há como validar).
- O erro do modelo é correlacionado com a variável explicativa de interesse e não pode ser corrigido.
- Poucos documentos: codificar à mão é mais barato e mais confiável.
- Os dados não podem sair da instituição e não há modelo local adequado.
