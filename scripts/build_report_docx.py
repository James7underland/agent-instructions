# -*- coding: utf-8 -*-
"""Канонический скрипт сборки академических отчетов из Markdown в DOCX и PDF.

Соответствует ГОСТ 7.32-2017 и стандартам кафедры АТП РГУ нефти и газа (НИУ) имени И. М. Губкина.

Реализует сквозной 11-стадийный конвейер:
1. prepare_markdown(): очистка HTML-оберток, трансляция выключных формул в связку {body} + [N],
   трансляция картинок, таблиц, списков, инъекция маркера оглавления ZZZTOCZZZ.
2. pypandoc.convert_file(): синтаксическая трансляция Markdown AST в OOXML с чистыми деревьями OMML.
3. build_title_doc() + merge_title_then_body(): создание титула кафедры АТП и слияние через разрыв раздела.
4. configure_page(): принудительная настройка формата листа A4 (210x297 мм) и полей 30/15/20/20 мм ДЛЯ ВСЕХ СЕКЦИЙ.
5. insert_toc_placeholder(): вставка нативного динамического поля Word TOC \\o "1-2" \\h \\z \\u.
6. style_body_paragraphs(): оформление стилей Heading 1/2/3, красной строки 1.25 см, интервала 1.5, выравнивания по ширине.
7. layout_formulas(): распаковка m:oMathPara, настройка табуляторов (4677 и 9354 twips), вставка табов и номера (N).
8. format_tables(): шрифт строго 14 pt Times New Roman, двухосевое центрирование, tblHeader, cantSplit, поля ячеек.
9. scale_figures(): пропорциональное масштабирование под полосу набора (165x155 мм) и сцепка keep_with_next с подписью.
10. replace_dashes_and_quotes() + normalize_math(): средние тире –, удаление паразитной жирности w:b из формул.
11. word_finalize() + export_to_pdf(): Word COM сброс красной строки оглавления (st_id -20/-21), обновление полей, экспорт в PDF.

Использование из командной строки:
    python scripts/build_report_docx.py --input Отчет.md
    python scripts/build_report_docx.py -i Отчет.md -o Отчет.docx -p Отчет.pdf --theme "Тема работы"

Использование как библиотеки:
    from scripts.build_report_docx import build_report
    build_report(input_md="Отчет.md", output_docx="Отчет.docx", output_pdf="Отчет.pdf")
"""

from __future__ import annotations

import argparse
import copy
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Sequence

import pypandoc
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Mm, Pt

MATH_FONT = "Times New Roman"
TWIP_BAND = 9354      # 165 мм — полоса набора листа A4 при полях 30/15 мм
TWIP_CENTER = 4677    # 82.5 мм — центр полосы набора (позиция формулы)
MATH_SZ = "28"        # 14 pt (28 полупунктов) в OOXML


def set_run_rfonts(run, name: str = "Times New Roman") -> None:
    """Устанавливает гарнитуру шрифта для всех языковых наборов символов."""
    run.font.name = name
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rFonts.set(qn(attr), name)


def set_paragraph_keep(paragraph, keep_next: bool = False, keep_lines: bool = False) -> None:
    """Устанавливает свойства неразрывности абзаца keepNext и keepLines."""
    pPr = paragraph._p.get_or_add_pPr()
    for tag, on in (("w:keepNext", keep_next), ("w:keepLines", keep_lines)):
        el = pPr.find(qn(tag))
        if on and el is None:
            pPr.append(OxmlElement(tag))
        elif not on and el is not None:
            pPr.remove(el)


def suppress_hyphens(paragraph) -> None:
    """Отключает автоматический перенос слов для абзаца."""
    pPr = paragraph._p.get_or_add_pPr()
    if pPr.find(qn("w:suppressAutoHyphens")) is None:
        pPr.append(OxmlElement("w:suppressAutoHyphens"))


def configure_page(section) -> None:
    """Устанавливает формат листа A4 и стандартные поля кафедры АТП (30-15-20-20 мм)."""
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.left_margin = Mm(30)
    section.right_margin = Mm(15)
    section.top_margin = Mm(20)
    section.bottom_margin = Mm(20)


def clear_paragraph(paragraph) -> None:
    """Удаляет все дочерние элементы абзаца, кроме свойств pPr."""
    for child in list(paragraph._p):
        if child.tag != qn("w:pPr"):
            paragraph._p.remove(child)


def set_text(paragraph, text: str, *, bold: bool = False, size: float = 14) -> None:
    """Очищает абзац и добавляет одиночный текстовый run с заданными параметрами."""
    clear_paragraph(paragraph)
    run = paragraph.add_run(text)
    set_run_rfonts(run)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = False


def setup_styles(doc: Document) -> None:
    """Инициализирует базовые стили документа: Normal, Heading 1/2/3, TOC 1/2."""
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(14)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    nf = normal.paragraph_format
    nf.space_before = Pt(0)
    nf.space_after = Pt(0)
    nf.line_spacing = 1.5
    nf.first_line_indent = Cm(1.25)

    for name, before, after in (
        ("Heading 1", Pt(0), Pt(12)),
        ("Heading 2", Pt(12), Pt(6)),
        ("Heading 3", Pt(6), Pt(4)),
    ):
        if name not in doc.styles:
            continue
        st = doc.styles[name]
        st.font.name = "Times New Roman"
        st.font.size = Pt(14)
        st.font.bold = True
        st.font.color.rgb = None
        st._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        pf = st.paragraph_format
        pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pf.first_line_indent = Cm(0)
        pf.space_before = before
        pf.space_after = after
        pf.line_spacing = 1.5
        pf.keep_with_next = True
        pf.keep_together = True

    for name in ("toc 1", "toc 2", "TOC 1", "TOC 2"):
        if name in doc.styles:
            st = doc.styles[name]
            st.font.name = "Times New Roman"
            st.font.size = Pt(14)
            st.font.bold = False
            st.paragraph_format.line_spacing = 1.0
            st.paragraph_format.space_before = Pt(0)
            st.paragraph_format.space_after = Pt(0)
            st.paragraph_format.first_line_indent = Cm(0)
            if "1" in name:
                st.paragraph_format.left_indent = Cm(0)
            elif "2" in name:
                st.paragraph_format.left_indent = Pt(14)


def prepare_markdown(md_text: str) -> str:
    """Выполняет предобработку Markdown перед отправкой в Pandoc AST."""
    # 1. Удаление веб-стилей, шапки титульника и служебных HTML-элементов
    md_text = re.sub(r"<style>.*?</style>\s*", "", md_text, flags=re.DOTALL)
    md_text = re.sub(r"^#\s+Отчёт[^\n]*\n+", "", md_text, count=1, flags=re.M)
    md_text = re.sub(
        r'<div class="title-block">.*?</div>\s*'
        r'<div class="title-right">.*?</div>\s*'
        r'<div class="title-city">.*?</div>\s*'
        r"-{3,}\s*",
        "",
        md_text,
        flags=re.DOTALL,
    )

    # 2. Удаление статического веб-оглавления и колонтитулов
    md_text = re.sub(r'<p class="toc-title">.*?</p>\s*<ul class="toc-list">.*?</ul>\s*', "", md_text, flags=re.DOTALL)
    md_text = re.sub(r'<div class="page-footer">.*?</div>\s*', "", md_text, flags=re.DOTALL)
    md_text = re.sub(r"^\s*---+\s*$", "", md_text, flags=re.M)
    md_text = re.sub(r'<a\s+id="[^"]*"></a>', "", md_text)

    # 2.1. Нормализация знаков неравенства в LaTeX формулах для Pandoc AST
    md_text = re.sub(r"\\gt\b", ">", md_text)
    md_text = re.sub(r"\\lt\b", "<", md_text)

    # 3. Маркерный механизм нумерации формул
    def eq_repl(m: re.Match[str]) -> str:
        body = re.sub(r"</?p[^>]*>", "", m.group(1).strip())
        num = m.group(2).strip()
        return f"\n\n{body}\n\n[{num}]\n\n"

    md_text = re.sub(
        r'<div class="eq">\s*<div class="eq-body">\s*(.*?)\s*</div>\s*'
        r'<div class="eq-num">\s*\(?(\d+[а-яА-Яa-zA-Z]*)\)?\s*</div>\s*</div>',
        eq_repl,
        md_text,
        flags=re.DOTALL,
    )

    # 4. Преобразование рисунков и подписей (поддержка <img> и ![]())
    def fig_repl(m: re.Match[str]) -> str:
        img_src = m.group(1).strip()
        cap = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        return f"\n\n![]({img_src})\n\n{cap}\n\n"

    md_text = re.sub(
        r'<figure[^>]*>\s*<img\s+src="([^"]+)"[^>]*>\s*<figcaption>(.*?)</figcaption>\s*</figure>',
        fig_repl,
        md_text,
        flags=re.DOTALL,
    )
    md_text = re.sub(
        r"<figure[^>]*>\s*!\[([^\]]*)\]\(([^)]+)\)\s*<figcaption>(.*?)</figcaption>\s*</figure>",
        lambda m: f"\n\n![]({m.group(2).strip()})\n\n{re.sub(r'<[^>]+>', '', m.group(3)).strip()}\n\n",
        md_text,
        flags=re.DOTALL,
    )

    # 5. Преобразование подписей таблиц
    md_text = re.sub(
        r'<p class="table-caption">(.*?)</p>',
        lambda m: f"\n\n{re.sub(r'<[^>]+>', '', m.group(1)).strip()}\n\n",
        md_text,
        flags=re.DOTALL,
    )

    # 6. Очистка таблиц: <br/> -> пробел, sub/sup/i/b -> Markdown синтаксис
    def clean_table(m: re.Match[str]) -> str:
        tbl = m.group(0)
        tbl = re.sub(r"<br\s*/?>", " ", tbl)
        tbl = re.sub(r"<sub>(.*?)</sub>", r"~\1~", tbl)
        tbl = re.sub(r"<sup>(.*?)</sup>", r"^\1^", tbl)
        tbl = re.sub(r"<i>(.*?)</i>", r"*\1*", tbl)
        tbl = re.sub(r"<b>(.*?)</b>", r"**\1**", tbl)
        return tbl

    md_text = re.sub(r"(\|.*?\n)+", clean_table, md_text)

    # 6.1. Автоматическая вставка пустых строк перед маркированными и нумерованными списками
    md_text = re.sub(r"([^\n])\n([ \t]*[-*+]\s+[^\n]+)", r"\1\n\n\2", md_text)
    md_text = re.sub(r"([^\n])\n([ \t]*\d+\.\s+[^\n]+)", r"\1\n\n\2", md_text)

    # 7. Нормализация заголовков глав и структурных разделов
    md_text = re.sub(
        r"^##\s+ГЛАВА\s+(\d+)(?:<br/>|\s+)(.*)$",
        r"# ГЛАВА \1 \2",
        md_text,
        flags=re.M | re.I,
    )
    md_text = re.sub(r"^##\s+ЦЕЛЬ РАБОТЫ\s*$", r"# ЦЕЛЬ РАБОТЫ", md_text, flags=re.M)
    md_text = re.sub(r"^##\s+ВЫВОДЫ\s*$", r"# ВЫВОДЫ", md_text, flags=re.M)
    md_text = re.sub(r"^##\s+ЗАКЛЮЧЕНИЕ\s*$", r"# ЗАКЛЮЧЕНИЕ", md_text, flags=re.M)
    md_text = re.sub(
        r"^##\s+(?:СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ|СПИСОК ИСПОЛЬЗОВАННОЙ ЛИТЕРАТУРЫ)\s*$",
        r"# СПИСОК ИСПОЛЬЗОВАННОЙ ЛИТЕРАТУРЫ",
        md_text,
        flags=re.M,
    )
    md_text = re.sub(
        r"^##\s+ПРИЛОЖЕНИЕ\s+([А-ЯA-Z])(?:<br/>|\s+)(.*)$",
        r"# ПРИЛОЖЕНИЕ \1 \2",
        md_text,
        flags=re.M | re.I,
    )
    md_text = re.sub(r"^##\s+(\d+\.\d+)\.?\s+(.*)$", r"## \1. \2", md_text, flags=re.M)
    md_text = re.sub(r"^###\s+(\d+\.\d+)\.?\s+(.*)$", r"## \1. \2", md_text, flags=re.M)
    md_text = re.sub(r"^####\s+(\d+\.\d+\.\d+)\.?\s+(.*)$", r"### \1. \2", md_text, flags=re.M)

    # Инъекция динамического маркера оглавления
    return "# СОДЕРЖАНИЕ\n\nZZZTOCZZZ\n\n" + md_text.strip() + "\n"


def _title_para(doc: Document, text: str, *, align, space_before=0, space_after=0, bold=False) -> None:
    p = doc.add_paragraph()
    set_text(p, text, bold=bold, size=14)
    p.alignment = align
    pf = p.paragraph_format
    pf.first_line_indent = Cm(0)
    pf.line_spacing = 1.5
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)


def extract_title_metadata(md_raw: str) -> dict[str, str]:
    """Извлекает реквизиты титульного листа из HTML-блоков Markdown, если они присутствуют."""
    meta: dict[str, str] = {}
    tb_m = re.search(r'<div class="title-block">(.*?)</div>', md_raw, flags=re.DOTALL)
    if tb_m:
        tb_content = tb_m.group(1)
        paras = [re.sub(r'<[^>]+>', '', p).strip() for p in re.findall(r'<p>(.*?)</p>', tb_content, flags=re.DOTALL)]
        paras = [
            p for p in paras
            if p and not p.lower().startswith("минобр")
            and not p.lower().startswith("ргу")
            and not p.lower().startswith("факультет")
            and not p.lower().startswith("кафедра")
        ]
        i = 0
        while i < len(paras):
            text = paras[i]
            if text.upper() in {"ОТЧЁТ", "ТЕХНИЧЕСКОЕ ЗАДАНИЕ", "ПОЯСНИТЕЛЬНАЯ ЗАПИСКА"}:
                meta["doc_title"] = text
                if i + 1 < len(paras) and paras[i + 1].upper() != "ДИСЦИПЛИНА":
                    meta["work_type"] = paras[i + 1]
                    i += 1
            elif text.upper() == "ДИСЦИПЛИНА":
                if i + 1 < len(paras):
                    meta["discipline"] = paras[i + 1]
                    i += 1
            elif text.startswith("«") or text.startswith("Тема"):
                meta["theme"] = text
            i += 1

    tr_m = re.search(r'<div class="title-right">(.*?)</div>', md_raw, flags=re.DOTALL)
    if tr_m:
        tr_paras = [re.sub(r'<[^>]+>', '', p).strip() for p in re.findall(r'<p>(.*?)</p>', tr_m.group(1), flags=re.DOTALL)]
        tr_paras = [p for p in tr_paras if p]
        try:
            v_idx = tr_paras.index("Выполнил:")
            meta["author_group"] = tr_paras[v_idx + 1]
            meta["author_name"] = tr_paras[v_idx + 2]
        except (ValueError, IndexError):
            pass
        try:
            p_idx = tr_paras.index("Проверил:")
            meta["supervisor_role"] = tr_paras[p_idx + 1]
            meta["supervisor_name"] = tr_paras[p_idx + 2]
        except (ValueError, IndexError):
            pass

    tc_m = re.search(r'<div class="title-city">\s*<p>(.*?)</p>', md_raw, flags=re.DOTALL)
    if tc_m:
        meta["city_year"] = re.sub(r'<[^>]+>', '', tc_m.group(1)).strip()

    return meta


def build_title_doc(
    *,
    doc_title: str = "ОТЧЁТ",
    work_type: str = "по лабораторной работе",
    discipline: str = "«Оптимизация и оптимальное управление»",
    theme: str = "Тема работы",
    author_group: str = "студент группы АТ-23-01",
    author_name: str = "Гимранов Э. А.",
    supervisor_role: str = "профессор кафедры АТП",
    supervisor_name: str = "Тараканов Д. В.",
    city_year: str = "Москва, 2026",
) -> Document:
    """Генерирует изолированный документ титульного листа по эталону кафедры АТП."""
    doc = Document()
    setup_styles(doc)
    for section in doc.sections:
        configure_page(section)

    if doc.paragraphs:
        p0 = doc.paragraphs[0]
        p0._element.getparent().remove(p0._element)

    C, R = WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.RIGHT
    for line in (
        "МИНОБРНАУКИ РОССИИ",
        "ФЕДЕРАЛЬНОЕ ГОСУДАРСТВЕННОЕ БЮДЖЕТНОЕ ОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ",
        "ВЫСШЕГО ОБРАЗОВАНИЯ",
        "«РОССИЙСКИЙ ГОСУДАРСТВЕННЫЙ УНИВЕРСИТЕТ НЕФТИ И ГАЗА",
        "(НАЦИОНАЛЬНЫЙ ИССЛЕДОВАТЕЛЬСКИЙ УНИВЕРСИТЕТ)",
        "ИМЕНИ И. М. ГУБКИНА»",
        "Факультет автоматики и вычислительной техники",
        "Кафедра автоматизации технологических процессов",
    ):
        _title_para(doc, line, align=C)

    _title_para(doc, "", align=C, space_before=24)
    _title_para(doc, doc_title, align=C, bold=False)
    if work_type:
        _title_para(doc, work_type, align=C, bold=False)
    _title_para(doc, "", align=C)
    _title_para(doc, "ДИСЦИПЛИНА", align=C, bold=False)
    _title_para(doc, discipline, align=C, bold=False)
    _title_para(doc, "", align=C)
    theme_clean = theme.strip()
    if not theme_clean.startswith("«") and not theme_clean.startswith("\""):
        theme_str = f"«{theme_clean.strip('«»')}»"
    else:
        theme_str = theme_clean
    if doc_title.upper() == "ОТЧЁТ":
        _title_para(doc, f"Тема: {theme_str}", align=C, bold=False)
    else:
        _title_para(doc, theme_str, align=C, bold=False)
    _title_para(doc, "", align=C, space_before=24)

    for line in (
        "Выполнил:",
        author_group,
        author_name,
        "",
        "Проверил:",
        supervisor_role,
        supervisor_name,
    ):
        _title_para(doc, line, align=R)

    return doc


def _ensure_sect_margins(sect_pr) -> None:
    pg_mar = sect_pr.find(qn("w:pgMar"))
    if pg_mar is None:
        pg_mar = OxmlElement("w:pgMar")
        sect_pr.append(pg_mar)
    pg_mar.set(qn("w:left"), str(int(30 * 56.7)))
    pg_mar.set(qn("w:right"), str(int(15 * 56.7)))
    pg_mar.set(qn("w:top"), str(int(20 * 56.7)))
    pg_mar.set(qn("w:bottom"), str(int(20 * 56.7)))

    pg_sz = sect_pr.find(qn("w:pgSz"))
    if pg_sz is None:
        pg_sz = OxmlElement("w:pgSz")
        sect_pr.append(pg_sz)
    pg_sz.set(qn("w:w"), "11906")
    pg_sz.set(qn("w:h"), "16838")
    pg_sz.set(qn("w:code"), "9")


def _fill_city_footer(footer, city_year: str = "Москва, 2026") -> None:
    footer.is_linked_to_previous = False
    p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    clear_paragraph(p)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.first_line_indent = Cm(0)
    pf.line_spacing = 1.5
    run = p.add_run(city_year)
    set_run_rfonts(run)
    run.font.size = Pt(14)
    run.bold = False


def _add_page_field(paragraph) -> None:
    clear_paragraph(paragraph)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    set_run_rfonts(run)
    run.font.size = Pt(14)
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    r2 = paragraph.add_run()
    set_run_rfonts(r2)
    r2._r.append(instr)
    r3 = paragraph.add_run()
    set_run_rfonts(r3)
    r3._r.append(sep)
    r4 = paragraph.add_run()
    set_run_rfonts(r4)
    r4._r.append(end)


def merge_title_then_body(
    title_doc: Document,
    body_path: Path,
    out_path: Path,
    city_year: str = "Москва, 2026",
) -> Document:
    """Объединяет титульный лист и тело отчета с соблюдением разрыва секции и формата A4."""
    body = Document(str(body_path))
    setup_styles(body)

    for section in body.sections:
        configure_page(section)

    title_nodes = []
    title_sectpr = None
    for child in title_doc.element.body:
        if child.tag == qn("w:sectPr"):
            title_sectpr = copy.deepcopy(child)
            continue
        node = copy.deepcopy(child)
        for sect in node.xpath(".//w:sectPr"):
            parent = sect.getparent()
            if parent is not None:
                parent.remove(sect)
        title_nodes.append(node)

    if title_sectpr is None:
        title_sectpr = OxmlElement("w:sectPr")
    _ensure_sect_margins(title_sectpr)
    if title_sectpr.find(qn("w:titlePg")) is None:
        title_sectpr.append(OxmlElement("w:titlePg"))

    body_elm = body.element.body
    for i, node in enumerate(title_nodes):
        body_elm.insert(i, node)

    p_break = OxmlElement("w:p")
    p_pr = OxmlElement("w:pPr")
    p_pr.append(title_sectpr)
    p_break.append(p_pr)
    body_elm.insert(len(title_nodes), p_break)

    # Принудительная настройка всех секций на лист A4
    for s in body.sections:
        configure_page(s)

    body.sections[0].different_first_page_header_footer = True
    try:
        _fill_city_footer(body.sections[0].first_page_footer, city_year)
        f0 = body.sections[0].footer
        f0.is_linked_to_previous = False
        for p in list(f0.paragraphs):
            clear_paragraph(p)
        h0 = body.sections[0].first_page_header
        h0.is_linked_to_previous = False
        for p in list(h0.paragraphs):
            clear_paragraph(p)
    except Exception:
        pass

    if len(body.sections) > 1:
        configure_page(body.sections[1])
        body.sections[1].different_first_page_header_footer = False
        f1 = body.sections[1].footer
        f1.is_linked_to_previous = False
        fp = f1.paragraphs[0] if f1.paragraphs else f1.add_paragraph()
        _add_page_field(fp)

    body.save(str(out_path))
    return Document(str(out_path))


def _in_math(element) -> bool:
    parent = element.getparent()
    while parent is not None:
        if parent.tag in (qn("m:oMath"), qn("m:oMathPara")):
            return True
        parent = parent.getparent()
    return False


def _set_chapter_heading(paragraph, label: str, title: str, *, page_break: bool = True) -> None:
    paragraph.style = "Heading 1"
    pf = paragraph.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.first_line_indent = Cm(0)
    pf.line_spacing = 1.5
    pf.keep_with_next = True
    pf.keep_together = True
    pf.page_break_before = page_break
    pf.space_before = Pt(18) if not page_break else Pt(0)
    pf.space_after = Pt(12)
    clear_paragraph(paragraph)
    run = paragraph.add_run()
    set_run_rfonts(run)
    run.bold = True
    run.font.size = Pt(14)
    run.font.color.rgb = None
    t1 = OxmlElement("w:t")
    t1.set(qn("xml:space"), "preserve")
    t1.text = label
    run._r.append(t1)
    run._r.append(OxmlElement("w:br"))
    t2 = OxmlElement("w:t")
    t2.set(qn("xml:space"), "preserve")
    t2.text = title
    run._r.append(t2)


def _set_structural_heading(paragraph, title: str, *, page_break: bool = True) -> None:
    paragraph.style = "Heading 1"
    pf = paragraph.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.first_line_indent = Cm(0)
    pf.line_spacing = 1.5
    pf.keep_with_next = True
    pf.keep_together = True
    pf.page_break_before = page_break
    pf.space_before = Pt(0)
    pf.space_after = Pt(12)
    clear_paragraph(paragraph)
    run = paragraph.add_run(title)
    set_run_rfonts(run)
    run.bold = True
    run.font.size = Pt(14)
    run.font.color.rgb = None


def insert_toc_placeholder(doc: Document) -> None:
    """Вставляет нативное динамическое поле оглавления вместо маркера ZZZTOCZZZ."""
    toc_p = None
    for p in doc.paragraphs:
        raw = p.text.strip()
        if "ZZZTOCZZZ" not in raw and "<<<TOC>>>" not in raw:
            continue
        clear_paragraph(p)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        begin = OxmlElement("w:fldChar")
        begin.set(qn("w:fldCharType"), "begin")
        instr = OxmlElement("w:instrText")
        instr.set(qn("xml:space"), "preserve")
        instr.text = ' TOC \\o "1-2" \\h \\z \\u '
        sep = OxmlElement("w:fldChar")
        sep.set(qn("w:fldCharType"), "separate")
        end = OxmlElement("w:fldChar")
        end.set(qn("w:fldCharType"), "end")
        r1 = p.add_run()
        set_run_rfonts(r1)
        r1._r.append(begin)
        r2 = p.add_run()
        set_run_rfonts(r2)
        r2._r.append(instr)
        r3 = p.add_run()
        set_run_rfonts(r3)
        r3._r.append(sep)
        r4 = p.add_run(" ")
        set_run_rfonts(r4)
        r5 = p.add_run()
        set_run_rfonts(r5)
        r5._r.append(end)
        toc_p = p
        break

    if toc_p is not None:
        next_p = toc_p._p.getnext()
        while next_p is not None and next_p.tag == qn("w:p"):
            has_text = bool(next_p.xpath(".//w:t"))
            has_draw = bool(next_p.xpath(".//w:drawing"))
            has_math = bool(next_p.xpath(".//m:oMath"))
            has_sect = bool(next_p.xpath(".//w:sectPr"))
            if not (has_text or has_draw or has_math or has_sect):
                to_del = next_p
                next_p = next_p.getnext()
                to_del.getparent().remove(to_del)
            else:
                break

    for p in doc.paragraphs:
        if p.text.strip().upper() == "СОДЕРЖАНИЕ":
            p.style = doc.styles["Normal"]
            set_text(p, "СОДЕРЖАНИЕ", bold=True)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.space_after = Pt(12)
            p.paragraph_format.page_break_before = False
            break


def style_body_paragraphs(doc: Document) -> None:
    """Стилизует абзацы тела документа по академическому стандарту кафедры АТП."""
    in_title = True
    for p in doc.paragraphs:
        text = p.text.strip()
        style_name = p.style.name if p.style else ""

        if in_title:
            if text.upper() == "СОДЕРЖАНИЕ":
                in_title = False
            else:
                for r in p.runs:
                    set_run_rfonts(r)
                    r.bold = False
                    if r.font.size is None:
                        r.font.size = Pt(14)
                p.paragraph_format.first_line_indent = Cm(0)
                p.paragraph_format.line_spacing = 1.5
                continue

        for r in p.runs:
            if _in_math(r._element):
                continue
            set_run_rfonts(r)
            if r.font.size is None or (r.font.size and r.font.size.pt > 16):
                r.font.size = Pt(14)

        pf = p.paragraph_format
        suppress_hyphens(p)

        if text.upper() == "СОДЕРЖАНИЕ":
            continue

        # Главы: ГЛАВА N НАИМЕНОВАНИЕ
        ch = re.match(r"^(ГЛАВА\s+(\d+))\s+(.+)$", text, flags=re.I)
        if ch:
            _set_chapter_heading(p, ch.group(1).upper(), ch.group(3).upper(), page_break=True)
            continue

        # Приложение: ПРИЛОЖЕНИЕ А НАИМЕНОВАНИЕ
        app = re.match(r"^(ПРИЛОЖЕНИЕ\s+([А-ЯA-Z]))\s+(.+)$", text, flags=re.I)
        if app:
            _set_chapter_heading(p, app.group(1).upper(), app.group(3).upper(), page_break=True)
            continue

        # Структурные разделы (ЦЕЛЬ РАБОТЫ, ВЫВОДЫ, СПИСОК...)
        if text.upper() in {"ЦЕЛЬ РАБОТЫ", "ВЫВОДЫ", "ЗАКЛЮЧЕНИЕ", "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", "СПИСОК ИСПОЛЬЗОВАННОЙ ЛИТЕРАТУРЫ"}:
            hdr_text = "СПИСОК ИСПОЛЬЗОВАННОЙ ЛИТЕРАТУРЫ" if "СПИСОК" in text.upper() else text.upper()
            _set_structural_heading(p, hdr_text, page_break=True)
            continue

        # Основные нумерованные разделы (1 ОБЩИЕ ПОЛОЖЕНИЯ, 2 ТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ...)
        m_sec = re.match(r"^(\d+)\s+([^\n\r]+)$", text)
        if (m_sec and not re.match(r"^\d+\.\d+", text)) or (style_name == "Heading 1" and not text.startswith("СОДЕРЖАНИЕ")):
            _set_structural_heading(p, text, page_break=True)
            continue

        # Подразделы: 1.1., 2.3., и т.д.
        sub = bool(re.match(r"^\d+\.\d+", text)) or style_name in {"Heading 2", "Heading 3"}
        if sub or style_name.startswith("Heading"):
            p.style = doc.styles["Heading 2"]
            pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pf.first_line_indent = Cm(0)
            pf.line_spacing = 1.5
            pf.keep_with_next = True
            pf.keep_together = True
            pf.page_break_before = False
            for r in p.runs:
                if _in_math(r._element):
                    continue
                r.bold = True
                r.font.color.rgb = None
                r.font.size = Pt(14)
            continue

        # Подписи рисунков и таблиц
        if text.startswith("Рисунок") or text.startswith("Таблица"):
            pf.alignment = (
                WD_ALIGN_PARAGRAPH.CENTER if text.startswith("Рисунок") else WD_ALIGN_PARAGRAPH.LEFT
            )
            pf.first_line_indent = Cm(0)
            pf.line_spacing = 1.5
            pf.space_before = Pt(6) if text.startswith("Рисунок") else Pt(12)
            pf.space_after = Pt(6) if text.startswith("Рисунок") else Pt(2)
            pf.keep_with_next = text.startswith("Таблица")
            pf.keep_together = True
            for r in p.runs:
                r.bold = False
            continue

        # Абзац с рисунком
        if p._p.xpath(".//w:drawing"):
            pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pf.first_line_indent = Cm(0)
            pf.line_spacing = 1.0
            pf.space_before = Pt(6)
            pf.space_after = Pt(0)
            pf.keep_with_next = True
            pf.keep_together = True
            continue

        # Маркер формулы [1]
        if re.fullmatch(r"\[\d+[а-яА-Яa-zA-Z]*\]", text):
            continue

        # Листинги кода
        if p.style.name == "Source Code" or text.startswith('"""') or text.startswith("# ===="):
            pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
            pf.first_line_indent = Cm(0)
            pf.line_spacing = 1.0
            pf.space_before = Pt(2)
            pf.space_after = Pt(2)
            for r in p.runs:
                r.font.name = "Courier New"
                r.font.size = Pt(9.5)
            continue

        # Нумерованные и маркированные списки
        if p._p.xpath(".//w:numPr"):
            pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            pf.first_line_indent = Cm(0)
            pf.left_indent = Cm(1.25)
            pf.line_spacing = 1.5
            pf.space_before = Pt(0)
            pf.space_after = Pt(2)
            for r in p.runs:
                if not _in_math(r._element):
                    set_run_rfonts(r)
                    r.font.size = Pt(14)
            continue

        # Обычный абзацный текст
        if text:
            words = len(text.split())
            pf.alignment = WD_ALIGN_PARAGRAPH.LEFT if words <= 10 else WD_ALIGN_PARAGRAPH.JUSTIFY
            pf.first_line_indent = Cm(1.25)
            pf.line_spacing = 1.5
            pf.space_before = Pt(0)
            pf.space_after = Pt(0)


def _set_borders(parent, tag: str) -> None:
    old = parent.find(qn(tag))
    if old is not None:
        parent.remove(old)
    borders = OxmlElement(tag)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "8")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "000000")
        borders.append(el)
    parent.append(borders)


def format_tables(doc: Document, col_widths_map: dict[int, list[float]] | None = None) -> None:
    """Форматирует таблицы по стандарту: 14 pt, двухосевое центрирование, cantSplit."""
    if col_widths_map is None:
        col_widths_map = {}

    for t_idx, table in enumerate(doc.tables):
        tbl = table._tbl
        tbl_pr = tbl.tblPr
        if tbl_pr is None:
            tbl_pr = OxmlElement("w:tblPr")
            tbl.insert(0, tbl_pr)

        jc = tbl_pr.find(qn("w:jc"))
        if jc is None:
            jc = OxmlElement("w:jc")
            tbl_pr.append(jc)
        jc.set(qn("w:val"), "center")

        tbl_w = tbl_pr.find(qn("w:tblW"))
        if tbl_w is None:
            tbl_w = OxmlElement("w:tblW")
            tbl_pr.append(tbl_w)
        tbl_w.set(qn("w:w"), str(TWIP_BAND))
        tbl_w.set(qn("w:type"), "dxa")

        layout = tbl_pr.find(qn("w:tblLayout"))
        if layout is None:
            layout = OxmlElement("w:tblLayout")
            tbl_pr.append(layout)
        layout.set(qn("w:type"), "fixed")

        _set_borders(tbl_pr, "w:tblBorders")

        num_cols = len(table.columns)
        if t_idx in col_widths_map:
            col_w_mm = col_widths_map[t_idx]
        elif num_cols > 0:
            even_w = 165.0 / num_cols
            col_w_mm = [even_w] * num_cols
        else:
            col_w_mm = []

        for r_idx, row in enumerate(table.rows):
            tr_pr = row._tr.get_or_add_trPr()
            if tr_pr.find(qn("w:cantSplit")) is None:
                tr_pr.append(OxmlElement("w:cantSplit"))
            if r_idx == 0 and tr_pr.find(qn("w:tblHeader")) is None:
                tr_pr.append(OxmlElement("w:tblHeader"))

            for c_idx, cell in enumerate(row.cells):
                tc_pr = cell._tc.get_or_add_tcPr()
                _set_borders(tc_pr, "w:tcBorders")

                # Полное центрирование по вертикали
                v_align = tc_pr.find(qn("w:vAlign"))
                if v_align is None:
                    v_align = OxmlElement("w:vAlign")
                    tc_pr.append(v_align)
                v_align.set(qn("w:val"), "center")

                # Компактные внутренние отступы ячейки
                tc_mar = tc_pr.find(qn("w:tcMar"))
                if tc_mar is not None:
                    tc_pr.remove(tc_mar)
                tc_mar = OxmlElement("w:tcMar")
                for side, val in (("top", "70"), ("bottom", "70"), ("left", "50"), ("right", "50")):
                    m_el = OxmlElement(f"w:{side}")
                    m_el.set(qn("w:w"), val)
                    m_el.set(qn("w:type"), "dxa")
                    tc_mar.append(m_el)
                tc_pr.append(tc_mar)

                if c_idx < len(col_w_mm):
                    w_twips = int(col_w_mm[c_idx] * 56.7)
                    tc_w = tc_pr.find(qn("w:tcW"))
                    if tc_w is None:
                        tc_w = OxmlElement("w:tcW")
                        tc_pr.append(tc_w)
                    tc_w.set(qn("w:w"), str(w_twips))
                    tc_w.set(qn("w:type"), "dxa")

                for p in cell.paragraphs:
                    p.paragraph_format.first_line_indent = Cm(0)
                    p.paragraph_format.line_spacing = 1.0
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.paragraph_format.space_before = Pt(2)
                    p.paragraph_format.space_after = Pt(2)
                    p.paragraph_format.keep_with_next = (r_idx == 0)
                    p.paragraph_format.keep_together = True

                    for r in p.runs:
                        if _in_math(r._element):
                            continue
                        set_run_rfonts(r)
                        r.font.size = Pt(14)
                        if r_idx == 0:
                            r.bold = True

        # Межабзацный интервал после таблицы: 12 pt
        next_sib = tbl.getnext()
        while next_sib is not None and next_sib.tag != qn("w:p"):
            next_sib = next_sib.getnext()
        if next_sib is not None and next_sib.tag == qn("w:p"):
            pPr_next = next_sib.find(qn("w:pPr"))
            if pPr_next is None:
                pPr_next = OxmlElement("w:pPr")
                next_sib.insert(0, pPr_next)
            sp_el = pPr_next.find(qn("w:spacing"))
            if sp_el is None:
                sp_el = OxmlElement("w:spacing")
                pPr_next.append(sp_el)
            sp_el.set(qn("w:before"), "240")


def _set_formula_tabs(p_el) -> None:
    pPr = p_el.find(qn("w:pPr"))
    if pPr is None:
        pPr = OxmlElement("w:pPr")
        p_el.insert(0, pPr)
    tabs = pPr.find(qn("w:tabs"))
    if tabs is not None:
        pPr.remove(tabs)
    tabs = OxmlElement("w:tabs")
    t_c = OxmlElement("w:tab")
    t_c.set(qn("w:val"), "center")
    t_c.set(qn("w:pos"), str(TWIP_CENTER))
    t_r = OxmlElement("w:tab")
    t_r.set(qn("w:val"), "right")
    t_r.set(qn("w:pos"), str(TWIP_BAND))
    tabs.append(t_c)
    tabs.append(t_r)

    idx = 0
    for i, el in enumerate(list(pPr)):
        if el.tag in (qn("w:pStyle"), qn("w:keepNext"), qn("w:keepLines"), qn("w:pageBreakBefore")):
            idx = i + 1
    pPr.insert(idx, tabs)

    jc = pPr.find(qn("w:jc"))
    if jc is None:
        jc = OxmlElement("w:jc")
        pPr.append(jc)
    jc.set(qn("w:val"), "left")

    spacing = pPr.find(qn("w:spacing"))
    if spacing is None:
        spacing = OxmlElement("w:spacing")
        pPr.append(spacing)
    spacing.set(qn("w:line"), "360")
    spacing.set(qn("w:lineRule"), "auto")

    ind = pPr.find(qn("w:ind"))
    if ind is None:
        ind = OxmlElement("w:ind")
        pPr.append(ind)
    ind.set(qn("w:firstLine"), "0")


def _make_tab_run() -> object:
    r = OxmlElement("w:r")
    r.append(OxmlElement("w:tab"))
    return r


def _paragraph_plain_text(node) -> str:
    return "".join(t.text or "" for t in node.findall(".//" + qn("w:t"))).strip()


def _unwrap_omath_para(p_el) -> None:
    for ompara in list(p_el.findall(".//" + qn("m:oMathPara"))):
        parent = ompara.getparent()
        idx = list(parent).index(ompara)
        for child in list(ompara):
            if child.tag == qn("m:oMathParaPr"):
                continue
            parent.insert(idx, child)
            idx += 1
        parent.remove(ompara)


def layout_formulas(doc: Document) -> None:
    """Выравнивает формулы по центру полосы, проставляет номера у правого края."""
    body = doc.element.body
    children = list(body)
    for i, node in enumerate(children):
        if node.tag != qn("w:p"):
            continue
        txt = _paragraph_plain_text(node)
        m = re.fullmatch(r"\[(\d+[а-яА-Яa-zA-Z]*)\]", txt)
        if not m:
            continue
        prev = None
        for j in range(i - 1, -1, -1):
            cand = children[j]
            if cand.tag != qn("w:p"):
                break
            if not _paragraph_plain_text(cand) and not cand.findall(".//" + qn("m:oMath")):
                continue
            prev = cand
            break
        if prev is None:
            continue
        oms = prev.findall(".//" + qn("m:oMath"))
        if not oms:
            continue
        _unwrap_omath_para(prev)
        oms = prev.findall(".//" + qn("m:oMath"))
        _set_formula_tabs(prev)
        first_om = oms[0]
        prev.insert(list(prev).index(first_om), _make_tab_run())
        last_om = prev.findall(".//" + qn("m:oMath"))[-1]
        prev.insert(list(prev).index(last_om) + 1, _make_tab_run())
        r = OxmlElement("w:r")
        rPr = OxmlElement("w:rPr")
        rFonts = OxmlElement("w:rFonts")
        for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
            rFonts.set(qn(attr), MATH_FONT)
        rPr.append(rFonts)
        sz = OxmlElement("w:sz")
        sz.set(qn("w:val"), "28")
        rPr.append(sz)
        r.append(rPr)
        t = OxmlElement("w:t")
        t.text = f"({m.group(1)})"
        r.append(t)
        prev.append(r)

        next_node = node.getnext()
        if next_node is not None and next_node.tag == qn("w:p"):
            next_txt = _paragraph_plain_text(next_node)
            if re.match(r"^где\b", next_txt):
                pPr_prev = prev.find(qn("w:pPr"))
                if pPr_prev is not None and pPr_prev.find(qn("w:keepNext")) is None:
                    pPr_prev.append(OxmlElement("w:keepNext"))

        body.remove(node)


def scale_figures(doc: Document) -> None:
    """Масштабирует рисунки под полосу набора 165x155 мм."""
    max_w = float(Mm(165))
    max_h = float(Mm(155))
    for shape in doc.inline_shapes:
        try:
            w, h = float(shape.width), float(shape.height)
            if w <= 0 or h <= 0:
                continue
            scale = min(max_w / w, max_h / h)
            shape.width = int(w * scale)
            shape.height = int(h * scale)
        except Exception:
            pass


def set_math_document_font(doc: Document) -> None:
    """Задает шрифт формул Times New Roman в настройках документа settings.xml."""
    settings = doc.settings.element
    math_pr = settings.find(qn("m:mathPr"))
    if math_pr is None:
        math_pr = OxmlElement("m:mathPr")
        settings.append(math_pr)
    math_font = math_pr.find(qn("m:mathFont"))
    if math_font is None:
        math_font = OxmlElement("m:mathFont")
        math_pr.insert(0, math_font)
    math_font.set(qn("m:val"), MATH_FONT)


def _set_w_sz(wrPr) -> None:
    for tag in ("w:sz", "w:szCs"):
        el = wrPr.find(qn(tag))
        if el is None:
            el = OxmlElement(tag)
            wrPr.append(el)
        el.set(qn("w:val"), MATH_SZ)


def normalize_math(doc: Document) -> None:
    """Удаляет паразитное жирное начертание из формул и выставляет 14 pt шрифт."""
    root = doc.element
    for rfonts in root.xpath(".//m:oMath//w:rFonts"):
        for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
            rfonts.set(qn(attr), MATH_FONT)
    for b in root.xpath(".//m:oMath//w:b | .//m:oMath//w:bCs"):
        parent = b.getparent()
        if parent is not None:
            parent.remove(b)
    for mr in root.xpath(".//m:r"):
        wrPr = mr.find(qn("w:rPr"))
        if wrPr is None:
            rPr = mr.find(qn("m:rPr"))
            idx = list(mr).index(rPr) + 1 if rPr is not None else 0
            wrPr = OxmlElement("w:rPr")
            mr.insert(idx, wrPr)
        _set_w_sz(wrPr)
    for ctrl in root.xpath(".//m:oMath//w:rPr"):
        _set_w_sz(ctrl)


def replace_dashes_and_quotes(doc: Document) -> None:
    """Заменяет длинные тире на средние с пробелами в тексте и таблицах."""
    def _fix_text(s: str) -> str:
        s = s.replace("\u2014", "\u2013").replace("\u2015", "\u2013").replace("\u2012", "\u2013")
        s = s.replace(" - ", " \u2013 ")
        s = re.sub(r"(Рисунок\s+\d+)\s+-+\s+", r"\1 – ", s)
        s = re.sub(r"(Таблица\s+\d+)\s+-+\s+", r"\1 – ", s)
        s = re.sub(r"(\d+)\s*[\u2013\u2014]\s*(\d+)", r"\1-\2", s)
        return s

    for p in doc.paragraphs:
        for r in p.runs:
            if not _in_math(r._element) and r.text:
                r.text = _fix_text(r.text)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for r in p.runs:
                        if not _in_math(r._element) and r.text:
                            r.text = _fix_text(r.text)


def word_finalize(docx_path: Path) -> None:
    """Финализирует оглавление, стили TOC, таблицы и поля через Word COM API."""
    try:
        import win32com.client as win32
    except ImportError:
        print("[WARN] pywin32 недоступен. Пропуск COM-финализации.")
        return

    word = win32.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        doc = word.Documents.Open(str(docx_path.resolve()))
        doc.Content.LanguageID = 1049

        # Сброс паразитной красной строки оглавления
        for st_id in (-20, -21):  # wdStyleTOC1 = -20, wdStyleTOC2 = -21
            try:
                st = doc.Styles(st_id)
                st.ParagraphFormat.LineSpacingRule = 0
                st.ParagraphFormat.SpaceBefore = 0
                st.ParagraphFormat.SpaceAfter = 0
                st.ParagraphFormat.FirstLineIndent = 0
                st.Font.Size = 14
                st.Font.Name = "Times New Roman"
                st.Font.Bold = False
            except Exception:
                pass

        try:
            doc.Styles(-20).ParagraphFormat.LeftIndent = 0
            doc.Styles(-21).ParagraphFormat.LeftIndent = 14.0
        except Exception:
            pass

        doc.Fields.Update()
        if doc.TablesOfContents.Count:
            toc = doc.TablesOfContents(1)
            toc.Update()
            for p in toc.Range.Paragraphs:
                p.Format.FirstLineIndent = 0
                p.Range.Font.Name = "Times New Roman"
                p.Range.Font.Size = 14
                p.Range.Font.Bold = False

        for t in doc.Tables:
            try:
                t.Range.Font.Name = "Times New Roman"
                t.Range.Font.Size = 14
                t.Range.ParagraphFormat.Alignment = 1
                t.Range.Cells.VerticalAlignment = 1
                t.Rows(1).HeadingFormat = -1
                t.Rows.AllowBreakAcrossPages = 0
            except Exception:
                pass

        try:
            for i in range(1, doc.OMaths.Count + 1):
                rng = doc.OMaths(i).Range
                rng.Font.Name = MATH_FONT
                rng.Font.Size = 14
                rng.Font.Bold = False
        except Exception:
            pass

        doc.Save()
        doc.Close(False)
        print("[OK] Word COM: стили TOC, таблицы, поля и формулы успешно обновлены")
    finally:
        word.Quit()


def export_to_pdf(docx_path: Path, pdf_path: Path) -> None:
    """Выполняет эталонный экспорт в PDF через Word COM API."""
    print(f"[PDF] Экспорт {docx_path.name} в {pdf_path.name}...")
    try:
        import win32com.client as win32
    except ImportError:
        print("[WARN] pywin32 недоступен. Пропуск экспорта в PDF.")
        return

    word = win32.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        doc = word.Documents.Open(str(docx_path.resolve()))
        doc.Fields.Update()
        if doc.TablesOfContents.Count:
            doc.TablesOfContents(1).Update()
        doc.ExportAsFixedFormat(
            OutputFileName=str(pdf_path.resolve()),
            ExportFormat=17,   # wdExportFormatPDF
            OpenAfterExport=False,
            OptimizeFor=0,     # wdExportOptimizeForPrint
            CreateBookmarks=1, # wdExportCreateWordBookmarks
        )
        pages = doc.ComputeStatistics(2)
        doc.Close(False)
        print(f"[OK] Экспорт в PDF завершен! Страниц: {pages}, файл: {pdf_path.name}")
    finally:
        word.Quit()


def build_report(
    input_md: str | Path,
    output_docx: str | Path | None = None,
    output_pdf: str | Path | None = None,
    *,
    doc_title: str | None = None,
    work_type: str | None = None,
    discipline: str | None = None,
    theme: str | None = None,
    author_group: str | None = None,
    author_name: str | None = None,
    supervisor_role: str | None = None,
    supervisor_name: str | None = None,
    city_year: str | None = None,
    col_widths_map: dict[int, list[float]] | None = None,
    export_pdf: bool = True,
) -> Path:
    """Главная функция конвейера сборки отчета DOCX и PDF из Markdown."""
    input_path = Path(input_md).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Файл {input_path} не найден")

    if output_docx is None:
        out_docx_path = input_path.with_suffix(".docx")
    else:
        out_docx_path = Path(output_docx).resolve()

    if output_pdf is None:
        out_pdf_path = input_path.with_suffix(".pdf")
    else:
        out_pdf_path = Path(output_pdf).resolve()

    root_dir = input_path.parent

    print("=" * 70)
    print(f"КАНОНИЧЕСКАЯ СБОРКА ОТЧЕТА ПО ГОСТ 7.32: {input_path.name}")
    print("=" * 70)

    # 1. Подготовка Markdown и автоизвлечение реквизитов
    print("1. Подготовка и очистка Markdown...")
    md_raw = input_path.read_text(encoding="utf-8")
    meta = extract_title_metadata(md_raw)

    final_doc_title = doc_title or meta.get("doc_title", "ОТЧЁТ")
    final_work_type = work_type or meta.get("work_type", "по лабораторной работе")
    final_discipline = discipline or meta.get("discipline", "«Оптимизация и оптимальное управление»")
    final_theme = theme or meta.get("theme", "Тема работы")
    final_group = author_group or meta.get("author_group", "студент группы АТ-23-01")
    final_author = author_name or meta.get("author_name", "Гимранов Э. А.")
    final_sup_role = supervisor_role or meta.get("supervisor_role", "профессор кафедры АТП")
    final_sup_name = supervisor_name or meta.get("supervisor_name", "Тараканов Д. В.")
    final_city_year = city_year or meta.get("city_year", "Москва, 2026")

    md_prep = prepare_markdown(md_raw)

    tmp_md = root_dir / f"_{input_path.stem}_prep.md"
    tmp_body = root_dir / f"_{input_path.stem}_body.docx"
    tmp_md.write_text(md_prep, encoding="utf-8")

    # 2. Трансляция Pandoc
    print("2. Синтаксическая трансляция Pandoc (OMML формулы, разметка)...")
    try:
        pypandoc.convert_file(
            str(tmp_md),
            "docx",
            outputfile=str(tmp_body),
            extra_args=[
                f"--resource-path={root_dir}",
                "-f", "markdown+tex_math_dollars+raw_html",
                "--standalone",
            ],
        )
    finally:
        tmp_md.unlink(missing_ok=True)

    # 3. Титульный лист и слияние
    print("3. Формирование титульного листа кафедры АТП и слияние секций...")
    title_doc = build_title_doc(
        doc_title=final_doc_title,
        work_type=final_work_type,
        discipline=final_discipline,
        theme=final_theme,
        author_group=final_group,
        author_name=final_author,
        supervisor_role=final_sup_role,
        supervisor_name=final_sup_name,
        city_year=final_city_year,
    )
    doc = merge_title_then_body(title_doc, tmp_body, out_docx_path, final_city_year)
    tmp_body.unlink(missing_ok=True)

    # 4-10. Стилизация, формулы, таблицы, рисунки, типографика
    print("4. Стилизация абзацев, оглавления, формул, таблиц и иллюстраций...")
    insert_toc_placeholder(doc)
    style_body_paragraphs(doc)
    layout_formulas(doc)
    format_tables(doc, col_widths_map)
    scale_figures(doc)
    replace_dashes_and_quotes(doc)
    set_math_document_font(doc)
    normalize_math(doc)

    doc.save(str(out_docx_path))
    print(f"[OK] Сохранен структурированный {out_docx_path.name} ({out_docx_path.stat().st_size:,} байт)")

    # 11. Word COM финализация и экспорт PDF
    if sys.platform == "win32":
        print("5. Финализация через MS Word COM...")
        word_finalize(out_docx_path)
        if export_pdf:
            print("6. Экспорт в PDF через MS Word COM...")
            export_to_pdf(out_docx_path, out_pdf_path)

    print("=" * 70)
    print(f"ГОТОВО! Итоговый DOCX: {out_docx_path.name}")
    if export_pdf and out_pdf_path.exists():
        print(f"ГОТОВО! Итоговый PDF:  {out_pdf_path.name}")
    print("=" * 70)
    return out_docx_path


def main(argv: Sequence[str] | None = None) -> int:
    """Точка входа CLI."""
    parser = argparse.ArgumentParser(description="Сборка отчета по ГОСТ 7.32 кафедры АТП")
    parser.add_argument("-i", "--input", required=True, help="Путь к исходному файлу Markdown (*.md)")
    parser.add_argument("-o", "--output-docx", help="Путь к результирующему файлу Word (*.docx)")
    parser.add_argument("-p", "--output-pdf", help="Путь к результирующему файлу PDF (*.pdf)")
    parser.add_argument("--doc-title", default=None, help="Заголовок документа (например, 'ОТЧЁТ' или 'ТЕХНИЧЕСКОЕ ЗАДАНИЕ')")
    parser.add_argument("--work-type", default=None, help="Тип работы (например, 'по домашнему заданию № 3')")
    parser.add_argument("--discipline", default=None, help="Название дисциплины")
    parser.add_argument("--theme", default=None, help="Тема отчета")
    parser.add_argument("--group", default=None, help="Группа студента")
    parser.add_argument("--author", default=None, help="ФИО автора")
    parser.add_argument("--supervisor-role", default=None, help="Должность преподавателя")
    parser.add_argument("--supervisor-name", default=None, help="ФИО преподавателя")
    parser.add_argument("--city-year", default=None, help="Город и год для титульного листа")
    parser.add_argument("--no-pdf", action="store_true", help="Не выполнять экспорт в PDF")

    args = parser.parse_args(argv)

    try:
        build_report(
            input_md=args.input,
            output_docx=args.output_docx,
            output_pdf=args.output_pdf,
            doc_title=args.doc_title,
            work_type=args.work_type,
            discipline=args.discipline,
            theme=args.theme,
            author_group=args.group,
            author_name=args.author,
            supervisor_role=args.supervisor_role,
            supervisor_name=args.supervisor_name,
            city_year=args.city_year,
            export_pdf=not args.no_pdf,
        )
        return 0
    except Exception as exc:
        print(f"[ERR] Ошибка при сборке отчета: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
