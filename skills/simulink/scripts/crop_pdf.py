# -*- coding: utf-8 -*-
"""Снимок модели Simulink: PDF (print -s...) -> обрезанный PNG 300 dpi.

    python crop_pdf.py model_top.pdf [model_reg.pdf ...] [--dpi 300] [--pad 24]

Почему через PDF: при печати модели сразу в PNG Simulink теряет символы
(в блоке 1/(5.2s+1) пропадала «s»), в PDF всё на месте.
Обрезка белых полей с порогом 40 — иначе мешают почти белые пиксели тени.
PNG кладётся рядом с PDF с тем же именем. Нужны pymupdf и pillow.
"""
import argparse
import os

import pymupdf
from PIL import Image, ImageChops

ap = argparse.ArgumentParser()
ap.add_argument("pdf", nargs="+")
ap.add_argument("--dpi", type=int, default=300)
ap.add_argument("--pad", type=int, default=24)
a = ap.parse_args()

for pdf in a.pdf:
    png = os.path.splitext(pdf)[0] + ".png"
    pix = pymupdf.open(pdf)[0].get_pixmap(dpi=a.dpi)
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    diff = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255)))
    bbox = diff.convert("L").point(lambda v: 255 if v > 40 else 0).getbbox()
    if bbox is None:
        raise SystemExit("пустая страница: " + pdf)
    box = (max(0, bbox[0] - a.pad), max(0, bbox[1] - a.pad),
           min(im.width, bbox[2] + a.pad), min(im.height, bbox[3] + a.pad))
    im.crop(box).save(png)
    print(pdf, "->", png, im.crop(box).size)
