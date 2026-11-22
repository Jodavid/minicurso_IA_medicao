# Livro de códigos: enquadramento de proposições legislativas sobre IA

**Unidade de análise:** a **ementa** de uma proposição (PL) da Câmara ou do Senado (2019–2026).
**Pergunta:** *quando o Congresso legisla sobre IA, o que ele quer fazer com ela?*

Codifique **apenas com base na ementa**. Não pesquise o inteiro teor nem o autor (isso evita que o codificador "adivinhe" a partir do partido).

---

## Variável 1: `categoria` (uma única categoria por ementa)

| Código | Definição | Indicadores típicos na ementa |
|---|---|---|
| **PUNIR** | O instrumento central é **penal**: cria crime, tipifica conduta, criminaliza, aumenta ou qualifica pena, altera o Código Penal, a parte penal do ECA ou cria crime eleitoral. | "tipifica", "criminaliza", "crime", "aumento de pena", "Código Penal", "hediondo" |
| **REGULAR** | Estabelece **regras não penais** para o uso da IA: princípios, deveres, obrigações, proibições/vedações administrativas, direitos, transparência, rotulagem, auditoria, responsabilidade civil ou administrativa, proteção de dados, direitos autorais, proteção do consumidor e do trabalhador, campanhas de prevenção. | "dispõe sobre o uso", "obrigatoriedade de identificação", "veda", "proíbe", "diretrizes", "governança", "transparência", "responsabilidade civil" |
| **PROMOVER** | **Fomenta ou adota** a IA: incentivos, fundos, pesquisa e desenvolvimento, ensino de IA nos currículos, capacitação, ou uso de IA pelo Estado em políticas públicas (saúde, segurança, meio ambiente etc.). | "incentivo", "fomento", "fundo", "currículo", "ensino", "institui sistema com IA", "obrigatoriedade do uso de IA" |
| **OUTRO** | A ementa **não trata** de IA, algoritmos, automação ou conteúdo sintético ou manipulado digitalmente. São os **falsos positivos** da busca por palavra-chave. | ementa sem nenhuma menção a esses objetos |

### Regras de decisão

1. **Precedência:** se a ementa combina instrumentos, aplique **PUNIR > REGULAR > PROMOVER**. Ex.: "estabelece deveres de transparência *e cria tipos penais*" → PUNIR.
2. **"Responsabilização" ou "penalidades" sem menção a crime, pena ou Código Penal** → REGULAR (pode ser responsabilidade civil ou administrativa).
3. **Marcos gerais** ("princípios, direitos e deveres para o uso de IA") → REGULAR, mesmo que mencionem fomento ou responsabilidade penal de passagem.
4. **Proteção de trabalhadores** diante da automação (vedação de demissão, fundos de transição, requalificação) → REGULAR.
5. **Obrigar o Estado ou empresas a usar IA** (câmeras com IA, triagem no SUS) → PROMOVER.
6. **Manipulação digital de imagem** (deepfake, montagem, nudez falsa) conta como "conteúdo sintético", mesmo sem as palavras "inteligência artificial".
7. Na dúvida entre OUTRO e outra categoria, pergunte: *a ementa, sozinha, deixa claro que o objeto é IA, algoritmo, automação ou conteúdo sintético?* Se não, é OUTRO.

## Variável 2: `eleitoral` (0/1)

**1** se a ementa trata de eleições, campanhas, propaganda eleitoral, candidatos, Código Eleitoral, Lei das Eleições, período eleitoral, violência política ou dano ao processo democrático. **0** caso contrário. É independente da categoria (um OUTRO pode ser eleitoral).

---

## Exemplos comentados

| Ementa (resumida) | Categoria | Por quê |
|---|---|---|
| "Altera o Código Penal para criar o crime de adulteração maliciosa de vídeos ou áudios." | PUNIR | Cria crime |
| "Altera a Lei das Eleições para dispor sobre o uso de IA em propaganda eleitoral." | REGULAR (eleitoral = 1) | Regra eleitoral, sem crime explícito |
| "Dispõe sobre a regulação de deepfakes, estabelece penalidades e incentiva o desenvolvimento ético." | REGULAR | "Penalidades" sem crime → regra 2 |
| "Institui a obrigatoriedade de câmeras corporais com IA pelas polícias." | PROMOVER | Adoção de IA pelo Estado → regra 5 |
| "Inclui a IA como componente curricular do ensino médio." | PROMOVER | Ensino de IA |
| "Altera o Código Penal para aumentar a pena dos crimes dos arts. 216-B e 218-C." | OUTRO | A ementa sozinha não menciona IA nem conteúdo sintético → regra 7 |
| "Institui a Lei Geral das Atividades Nucleares." | OUTRO | Falso positivo da busca |

---

## Sobre os rótulos de referência deste repositório

O arquivo `dados/anotacoes/referencia_completa.csv` traz uma **codificação preliminar** das 304 ementas, feita apenas para que todo o pipeline rode.

- **Quem codificou:** outra IA, o **Claude Opus 5.5** (Anthropic), coautor do material. Não foi o S5-nano, o instrumento avaliado no minicurso.
- **Como:** aplicando este livro de códigos ementa por ementa, com base apenas na ementa (sem inteiro teor e sem o autor).
- **Quando:** as 298 ementas da coleta de 08/10/2026 e, em 06/11/2026, as 6 novas (doc0299 a doc0304).
- **Status:** **sem revisão humana** (`codificador = "preliminar"`, `revisado = FALSE`). Enquanto for assim, o kappa do S5-nano mede a concordância entre duas IAs, não a validade contra humanos.

**Distribuição na referência preliminar:**

| Categoria | Câmara | Senado | Corpus | % | Amostra-ouro (n = 120) |
|---|---:|---:|---:|---:|---:|
| PUNIR | 40 | 13 | 53 | 17,4% | 22 |
| REGULAR | 136 | 14 | 150 | 49,3% | 69 |
| PROMOVER | 47 | 9 | 56 | 18,4% | 16 |
| OUTRO | 37 | 8 | 45 | 14,8% | 13 |
| **Total** | 260 | 44 | 304 | 100% | 120 |

`eleitoral = 1`: 13 ementas no corpus (4,3%), 8 na amostra-ouro.

**O que foi para OUTRO (45 ementas, 32 delas de 2026):** projetos que a busca por palavra-chave devolveu, mas cuja ementa não trata de IA nem de conteúdo sintético. São de três tipos: (1) temas digitais vizinhos (violência contra a mulher em ambiente digital, crimes cibernéticos, LGPD, soberania e inclusão digital); (2) leis penais que não citam IA nem conteúdo sintético (aumento de pena dos arts. 216-B e 218-C, estelionato, usura); (3) falsos positivos puros (atividades nucleares, transplante de órgãos, trânsito, processo administrativo).

Esses rótulos **precisam ser revisados por codificadores humanos** (idealmente dois, de forma independente, com cálculo de concordância entre eles). As colunas `codificador` e `revisado` existem para registrar essa revisão. Os casos marcados como ambíguos durante a construção deste livro de códigos (ex.: doc0121, doc0145, doc0169, doc0185, doc0210, doc0233, doc0244, doc0297) são bons candidatos para a discussão em sala.
