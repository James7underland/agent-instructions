#!/usr/bin/env python3
"""trend.py — график по CSV журналам (plcbridge --log, softplc --log, dyn.py --csv): столбцы ';' или ','.

  python trend.py LOG.csv --png out.png [--cols LT100.PV,PT100.PV] [--x "t, s"] [--title "..."]
                  [--mark 47:"Pсырья 5600" --mark 117:"отказ LV"]
Каждый столбец — своя панель (общая ось времени); bool/0-1 — ступенчатый график.
"""
from __future__ import annotations

import argparse
import csv
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def num(s):
    s = (s or "").strip().replace(",", ".")
    if s in ("", "None", "nan"):
        return None
    if s.lower() in ("true", "false"):
        return 1.0 if s.lower() == "true" else 0.0
    try:
        return float(s)
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--png", required=True)
    ap.add_argument("--cols")
    ap.add_argument("--x")
    ap.add_argument("--title", default="")
    ap.add_argument("--mark", action="append", default=[])
    a = ap.parse_args()
    raw = open(a.csv, encoding="utf-8-sig").read().splitlines()
    delim = ";" if raw[0].count(";") >= raw[0].count(",") else ","
    rows = list(csv.reader(raw, delimiter=delim))
    head, data = rows[0], rows[1:]
    xi = head.index(a.x) if a.x else 0
    cols = a.cols.split(",") if a.cols else [h for i, h in enumerate(head) if i != xi]
    miss = [c for c in cols if c not in head]
    if miss:
        sys.exit(f"нет столбцов {miss}; есть: {head}")
    x = [num(r[xi]) for r in data]
    fig, axs = plt.subplots(len(cols), 1, figsize=(10, 1.6 + 1.5 * len(cols)), sharex=True, squeeze=False)
    for ax, c in zip(axs[:, 0], cols):
        j = head.index(c)
        y = [num(r[j]) if j < len(r) else None for r in data]
        pts = [(xx, yy) for xx, yy in zip(x, y) if xx is not None and yy is not None]
        if not pts:
            continue
        xs, ys = zip(*pts)
        binary = set(ys) <= {0.0, 1.0}
        (ax.step if binary else ax.plot)(xs, ys, where="post", lw=1.4) if binary else ax.plot(xs, ys, lw=1.4)
        ax.set_ylabel(c, rotation=0, ha="right", va="center", fontsize=9)
        ax.grid(alpha=0.3)
        for m in a.mark:
            t, _, lbl = m.partition(":")
            ax.axvline(float(t), color="tab:red", ls="--", lw=0.8)
            if ax is axs[0, 0] and lbl:
                ax.annotate(lbl.strip('"'), (float(t), 1), xycoords=("data", "axes fraction"), fontsize=8,
                            color="tab:red", ha="left", va="bottom")
    axs[-1, 0].set_xlabel(head[xi])
    if a.title:
        fig.suptitle(a.title)
    fig.tight_layout()
    fig.savefig(a.png, dpi=110)
    print("png ->", a.png)


if __name__ == "__main__":
    main()
