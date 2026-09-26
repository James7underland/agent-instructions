"""Формулы Word (OMML) из LaTeX: LaTeX → MathML (latex2mathml) → OMML (MML2OMML.XSL из Microsoft Office).

В Word формула получается «настоящей» (редактируется редактором формул, как набранная вручную через Alt+=).
    from wordmath import eq, tex_num
    eq(doc.add_paragraph(), r"\\omega_{0}=\\frac{2\\pi}{143{,}2}=0{,}044\\ \\text{рад/с}")
Десятичная запятая в LaTeX — `{,}` (иначе Word ставит после неё пробел); `tex_num(1.25)` → "1{,}25".
Единицы и русский текст — `\\text{...}` (прямой шрифт). Минус — обычный "-".
Нужны: pip-пакет latex2mathml, установленный Office (MML2OMML.XSL ищется в Program Files).
"""
from __future__ import annotations

import glob
import os
from functools import lru_cache

from lxml import etree

M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"


@lru_cache(maxsize=1)
def _xslt():
    cands = [os.environ.get("MML2OMML_XSL", "")]
    for base in (os.environ.get("ProgramFiles", r"C:\Program Files"),
                 os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")):
        cands += glob.glob(os.path.join(base, "Microsoft Office", "root", "Office*", "MML2OMML.XSL"))
        cands += glob.glob(os.path.join(base, "Microsoft Office", "Office*", "MML2OMML.XSL"))
    for c in cands:
        if c and os.path.exists(c):
            return etree.XSLT(etree.parse(c))
    raise FileNotFoundError("MML2OMML.XSL не найден (нужен Microsoft Office) — задайте MML2OMML_XSL")


def omml(latex: str):
    """LaTeX → элемент <m:oMath>."""
    from latex2mathml.converter import convert
    mml = etree.fromstring(convert(latex).encode("utf-8"))
    return _xslt()(mml).getroot()


def eq(paragraph, latex: str):
    """Добавить формулу в конец абзаца python-docx (можно чередовать с обычным текстом run'ами)."""
    paragraph._p.append(omml(latex))
    return paragraph


def tex_num(x, nd=3, keep_zeros=False):
    """Число для LaTeX: до nd знаков, без хвостовых нулей, десятичная запятая {,}."""
    s = f"{x:.{nd}f}"
    if not keep_zeros:
        s = s.rstrip("0").rstrip(".")
    if s in ("-0", ""):
        s = "0"
    return s.replace(".", "{,}")
