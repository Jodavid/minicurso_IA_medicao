-- Filtro Lua para o PDF (LaTeX):
-- 1. Converte caixas (::: {.caixa}, .aviso, .ia) e títulos ([...]{.titulo-caixa})
--    em ambientes tcolorbox estilizados.
-- 2. Abas R | Python (::: {.abas} / ::: {.aba data-nome="R"}): no PDF, blocos em
--    sequência com o título "Em R" / "Em Python" (no HTML, abas.html cria as abas).
-- 3. Atualiza o cabeçalho corrente (\markboth) em capítulos não numerados
--    (como Apresentação), evitando que herdem "Sumário".

function Header(el)
  if FORMAT:match("latex") and el.level == 1 and el.classes:includes("unnumbered") then
    local txt = pandoc.utils.stringify(el.content)
    return {
      el,
      pandoc.RawBlock("latex", "\\markboth{" .. txt .. "}{" .. txt .. "}")
    }
  end
end

function Span(el)
  if FORMAT:match("latex") and el.classes:includes("titulo-caixa") then
    local inlines = pandoc.List({
      pandoc.RawInline("latex", "{\\sffamily\\bfseries\\color{corTituloCaixa}")
    })
    inlines:extend(el.content)
    inlines:insert(pandoc.RawInline("latex", "}\\par\\nopagebreak[4]\\vspace{3pt}\\nopagebreak[4]\\noindent\\ignorespaces "))
    return inlines
  end
end

function Div(el)
  -- Abas R | Python: no PDF, cada aba vira um bloco com o título "Em R" / "Em Python"
  if FORMAT:match("latex") and el.classes:includes("aba") then
    local nome = el.attributes["nome"] or el.attributes["data-nome"] or ""
    local blocks = pandoc.List({
      pandoc.RawBlock("latex", "\\par\\medskip\\noindent{\\sffamily\\bfseries\\small\\color{azulEscuro}Em " .. nome ..
        "}\\par\\nopagebreak[4]")
    })
    blocks:extend(el.content)
    return blocks
  end
  if FORMAT:match("latex") and el.classes:includes("abas") then
    return el.content
  end
  if FORMAT:match("latex") and el.classes:includes("caixa") then
    local env = "caixanota"
    if el.classes:includes("aviso") then
      env = "caixaaviso"
    elseif el.classes:includes("ia") then
      env = "caixaia"
    end
    local blocks = pandoc.List({
      pandoc.RawBlock("latex", "\\begin{" .. env .. "}")
    })
    blocks:extend(el.content)
    blocks:insert(pandoc.RawBlock("latex", "\\end{" .. env .. "}"))
    return blocks
  end
end
