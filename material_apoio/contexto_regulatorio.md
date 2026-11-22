# IA na política brasileira: eleições de 2026 e debate regulatório

*Material de apoio ao Bloco 7 (ética, limites e debate). Situação levantada em 08/10/2026 e **atualizada em 06/11/2026**. Confira de novo na véspera da aula: as datas e o status mudam rápido.*

---

## 1. Eleições de 2026: regras do TSE para IA

**Norma:** Resolução TSE nº **23.755, de 2 de março de 2026**, que alterou a Res. nº 23.610/2019 (propaganda eleitoral). Ela consolida e amplia o que a Res. nº 23.732/2024 já previa para as eleições municipais de 2024.

| Tema | O que a norma estabelece (resumo) |
|------------------|--------------------------------------------------------------|
| **Rotulagem** | Conteúdo de propaganda criado ou substancialmente alterado por IA deve informar, de forma explícita e destacada, que foi fabricado ou manipulado e qual tecnologia foi usada. O formato varia por mídia (áudio, imagem, vídeo, impresso). |
| **Deepfakes** | São proibidos deepfakes que beneficiem ou prejudiquem candidaturas, mesmo com autorização de uso de imagem ou voz. Em 01/09/2026 o TSE esclareceu os critérios: a proibição incide quando o conteúdo sintético tem realismo suficiente para simular a imagem, a voz ou a manifestação de uma pessoa e caracteriza propaganda eleitoral. |
| **Janela final** | Fica vedado publicar, republicar e impulsionar novos conteúdos sintéticos com imagem, voz ou manifestação de candidatos e pessoas públicas entre 72 horas antes e 24 horas depois do encerramento da votação. |
| **Sistemas de IA** | Sistemas de IA não podem recomendar voto, ranquear, sugerir ou priorizar candidaturas. Há restrições ao uso eleitoral de avatares e *chatbots* que simulem pessoas. |
| **Plataformas** | Dever de agir, canais de denúncia, remoção de conteúdo ilícito e suspensão de impulsionamento e monetização. |
| **Sanções** | Multa (art. 57-D da Lei 9.504/97), cassação de registro ou mandato em casos graves, crimes previstos no Código Eleitoral. |

**Fontes:** [Res. 23.755/2026 (TSE, texto compilado)](https://www.tse.jus.br/legislacao/compilada/res/2026/resolucao-no-23-755-de-2-de-marco-de-2026) · [Migalhas: o que o TSE autoriza e proíbe](https://www.migalhas.com.br/quentes/455672/ia-nas-campanhas-eleitorais-2026-veja-o-que-tse-autoriza-ou-proibe) · [Estado de Minas: TSE esclarece regras sobre deepfake (set/2026)](https://www.em.com.br/mundo-corporativo/2026/09/7502136-tse-esclarece-regras-sobre-deepfake-nas-eleicoes-de-2026.html). *Confira os artigos no texto oficial antes de citar em slide.*

### Ponte com o minicurso
- A regulação do TSE é infralegal. No **Congresso**, o corpus do minicurso mostra 13 proposições com dimensão eleitoral sobre IA, a maioria apresentada em 2023 e em 2026. É uma pergunta empírica em aberto: o calendário eleitoral puxa a produção legislativa sobre IA?
- **Para debate:** a fiscalização de deepfakes por tribunais e plataformas também usa classificadores automáticos. Quem mede o erro desses classificadores? Os mesmos conceitos do minicurso (sensibilidade, especificidade, viés diferencial entre candidatos ou campos) valem ali.

---

## 2. Marco Legal da IA: PL 2338/2023

| Data | Evento |
|------------------|--------------------------------------------------------------|
| 03/05/2023 | PL 2338/2023 apresentado no Senado (autor: Sen. Rodrigo Pacheco) |
| 10/12/2024 | Aprovado no Plenário do Senado (substitutivo); vários PLs apensados são declarados prejudicados |
| 17/03/2025 | Chega à Câmara dos Deputados |
| 20/05/2025 | Instalada a Comissão Especial (presidente: Dep. Luisa Canziani; relator: Dep. Aguinaldo Ribeiro, PP-PB) |
| nov/2025 a jun/2026 | Pelo menos cinco datas de votação anunciadas e não cumpridas |
| 24/08/2026 | O relator afirma que a votação fica para depois das eleições de outubro |
| 04/10 e 25/10/2026 | 1º e 2º turnos das eleições gerais |
| 27/10/2026 | Última movimentação na API da Câmara (consulta de 06/11/2026): apensação de novos PLs. Situação segue **"Aguardando Parecer"**, sem parecer do relator protocolado |

**Conteúdo central (versão do Senado):** classificação de sistemas por **risco** (excessivo, alto, demais), direitos das pessoas afetadas (informação, explicação, contestação, revisão humana), Sistema Nacional de Regulação e Governança de IA (SIA), avaliação de impacto algorítmico, sanções de até R$ 50 milhões por infração. A inspiração direta é o *AI Act* europeu.

**Fontes:** API de Dados Abertos da Câmara (`/proposicoes/2487262`, consultada em 08/10/2026 e em 06/11/2026) · [Agência Câmara: instalação da comissão](https://www.camara.leg.br/noticias/1160383-comissao-que-vai-analisar-projeto-sobre-inteligencia-artificial-sera-presidida-por-luisa-canziani-aguinaldo-ribeiro-sera-relator/) · [Monitor LCF: situação do PL 2338/2023](https://monitor.lcfconsulting.com.br/proposicoes/pl-2338-2023/) · [DIAP (mai/2025)](https://www.diap.org.br/index.php/noticias/noticias/92249-pl-2338-23-votacao-do-projeto-sobre-inteligencia-artificial-esta-prevista-apenas-para-dezembro)

### Para atualizar o status ao vivo (R)
```r
library(httr2)
request("https://dadosabertos.camara.leg.br/api/v2/proposicoes/2487262") |>
  req_headers(Accept = "application/json") |> req_perform() |>
  resp_body_json() |> purrr::pluck("dados", "statusProposicao", "descricaoSituacao")
```

---

## 3. O que o corpus mostra (e o que ele não pode mostrar)

- **Explosão:** de 2019 a 2022 foram 10 proposições sobre IA nas duas casas; em 2026, até a coleta, já são mais de 110. O ChatGPT (nov/2022) é o marco evidente.
- **Enquadramento punitivo:** uma parte relevante dos projetos cria crimes ou aumenta penas, sobretudo nudez sintética, violência contra mulheres e crianças, fraude e estelionato. **Quanto exatamente, e se isso difere entre campos políticos, é a pergunta que estimamos com PPI no Bloco 5.**
- **Limites do dado:**
  1. A busca por palavra-chave da API da Câmara depende de um indexador; projetos antigos podem estar sub-representados e há falsos positivos (a categoria OUTRO).
  2. A ementa é um resumo; o inteiro teor pode ter outro enquadramento.
  3. "Campo político" é uma classificação de partidos, não de parlamentares, e partidos mudam.
  4. Apresentar um projeto é barato: medir *produção* legislativa não é medir *política pública*.

---

## 4. Perguntas para o debate final

1. Se um LLM classifica 304 ementas em poucos minutos com kappa próximo de 0,7, ainda precisamos de codificadores humanos? **Sim. Para quê, exatamente?**
2. Um modelo aberto local (reprodutível, gratuito, com dados que não saem da máquina) com kappa menor é preferível a uma API comercial com kappa maior (que muda sem aviso)?
3. O viés político dos LLMs (Motoki et al., 2024; Rozado, 2024) pode contaminar a medida de "campo político"? Como testar?
4. Na regulação: rotulagem obrigatória de conteúdo sintético é verificável? Quem audita o detector?
5. O que deve constar num **pacote de replicação** de um artigo que usou LLM? (ver `CHECKLIST.md`)
