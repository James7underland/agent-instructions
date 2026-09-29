#!/usr/bin/env python3
"""props.py — свойства и параметрические расчёты в Symmetry (COM-движок), с таблицами и графиками.

  envelope CASE STREAM OUT.png [--csv F] [--title T]
        фазовая P–T огибающая потока (Envelope.PTEnvelope): кривые кипения/росы, критическая точка,
        крикондебар, крикондентерм; + текущая точка потока. STREAM = /Gas (поток кейса).
  hydrate CASE STREAM --p 1000:10000:1000 [--png F] [--csv F]
        кривая гидратообразования T_гидр(P) для состава потока (HydrateThermoBased.Hydrate)
  dew CASE STREAM --p 1000,3000,5000 [--kind dew|bubble|water]
        температура точки росы (VapFrac=1) / кипения (VapFrac=0) / росы по воде (WaterDewPoint) при давлениях
  sweep CASE --set PATH --range A:B:STEP [--unit U] --get PATH[@unit][=Метка]... [--png F] [--csv F] [--xlabel ..]
        (элемент вектора: --get "/Gas.Out.Fraction[3]=x воды" — индекс компонента с 0)
        параметрический расчёт: меняем спецификацию, пересчитываем, пишем результаты (аналог Case Study)
CASE = .vsym/.vmp или .tst (тогда кейс строится из скрипта). Единицы давления по умолчанию kPa, температуры C.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sym  # noqa: E402


def load(case):
    eng = sym.Engine(echo=lambda *a: None)
    if case.lower().endswith(".tst"):
        sym.run_commands(eng, list(sym.iter_script_lines([case], [])), quiet=True)
    else:
        sym.open_case(eng, case)
    eng.eval("units SI")
    eng.solve()
    eng.msgs.clear()
    return eng


def rng(s):
    if ":" in s:
        a, b, st = (float(x) for x in s.split(":"))
        out, x = [], a
        while x <= b + 1e-9 * max(1, abs(b)):
            out.append(round(x, 10)); x += st
        return out
    return [float(x) for x in s.split(",")]


def num(s):
    return float(s.replace(",", "."))


def temp_stream(eng, src, name="_TMP"):
    """Поток-копия состава src (для расчётов при других P/T), без подключения к схеме."""
    frac = eng.value(f"{src}.Out.Fraction")[0]
    for c in [f"{'/' + name} = Stream.Stream_Material()", f"/{name}.In.MoleFlow = 100 kmol/h",
              f"/{name}.In.Fraction = " + " ".join(f"{x:.12g}" for x in frac)]:
        eng.eval(c)
    eng.solve(); eng.msgs.clear()
    return "/" + name


def parse_q1(txt):
    lines = str(txt).splitlines()
    hdr = next((i for i, l in enumerate(lines) if "vapSat" in l and "liqSat" in l), None)
    if hdr is None:
        return [], []
    half = lines[hdr].index(re.search(r"\S+ liqSat PointType", lines[hdr]).group(0))
    vap, liq = [], []
    for l in lines[hdr + 2:]:
        for m in re.finditer(r"(-?\d+(?:[.,]\d+)?(?:[eE][-+]?\d+)?)\s+(-?\d+(?:[.,]\d+)?(?:[eE][-+]?\d+)?)", l):
            p, t = num(m.group(1)), num(m.group(2))
            (vap if m.start() < half else liq).append((p, t))
    return vap, liq


def cmd_envelope(a):
    eng = load(a.case)
    s = a.stream
    for c in ['/_ENV = Envelope.PTEnvelope("InitPressures = 1000 2000 3000 4000 5000 6000 7000 8000 9000 10000 11000 '
              '12000; Starting_P = 500 kPa")', f"/_ENV.In -> {s}.Out", "/_ENVo = Stream.Stream_Material()",
              "/_ENVo.In -> /_ENV.Out"]:
        eng.eval(c)
        eng.solve()            # огибающая считается только при пересчёте после каждой команды (как в .tst)
    err = [m for t, m in eng.msgs if t != "Info"]; eng.msgs.clear()
    vap, liq = parse_q1(eng.eval("/_ENV.Q1.Results"))   # таблица кривых лежит в .Q1.Results
    pts = {k: eng.value(f"/_ENV.{k}", "kPa" if k.endswith("_P") else "C")[0] for k in
           ["Crit_P", "Crit_T", "Cricondenbar_P", "Cricondenbar_T", "Cricondentherm_P", "Cricondentherm_T"]}
    cur = (eng.value(f"{s}.Out.P", "kPa")[0], eng.value(f"{s}.Out.T", "C")[0])
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in pts.items()}, "поток:", cur, err[:2])
    print(f"точек: роса {len(vap)}, кипение {len(liq)}")
    if a.csv:
        with open(a.csv, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["кривая", "P, kPa", "T, C"])
            for p, t in vap:
                w.writerow(["роса", f"{p:.6g}".replace(".", ","), f"{t:.6g}".replace(".", ",")])
            for p, t in liq:
                w.writerow(["кипение", f"{p:.6g}".replace(".", ","), f"{t:.6g}".replace(".", ",")])
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 6))
    if vap:
        ax.plot([t for p, t in vap], [p / 1000 for p, t in vap], "-", color="tab:red", label="кривая точек росы")
    if liq:
        ax.plot([t for p, t in liq], [p / 1000 for p, t in liq], "-", color="tab:blue", label="кривая кипения")
    for key, lab, mk in [("Crit", "критическая точка", "ko"), ("Cricondenbar", "крикондебар", "k^"),
                         ("Cricondentherm", "крикондентерм", "k>")]:
        P, T = pts[f"{key}_P"], pts[f"{key}_T"]
        if P is not None and T is not None:
            ax.plot(T, P / 1000, mk, label=f"{lab} ({T:.1f} °C; {P / 1000:.2f} МПа)")
    if cur[0] is not None:
        ax.plot(cur[1], cur[0] / 1000, "*", color="green", ms=12, label=f"поток {s} ({cur[1]:.1f} °C; {cur[0] / 1000:.2f} МПа)")
    ax.set_xlabel("T, °C"); ax.set_ylabel("P, МПа"); ax.grid(True, alpha=0.35); ax.legend(fontsize=8)
    ax.set_title(a.title or f"Фазовая огибающая {s}")
    fig.tight_layout(); fig.savefig(a.out, dpi=150)
    print("png ->", a.out)


def cmd_hydrate(a):
    eng = load(a.case)
    tmp = temp_stream(eng, a.stream)
    Ts = eng.value(f"{a.stream}.Out.T", "C")[0]
    for c in [f"{tmp}.In.T = {Ts} C", f"{tmp}.In.P = 1000 kPa", "/_HYD = HydrateThermoBased.Hydrate()",
              f"/_HYD.In -> {tmp}.Out", "/_HYo = Stream.Stream_Material()", "/_HYo.In -> /_HYD.Out"]:
        eng.eval(c)
    eng.solve(); eng.msgs.clear()
    rows = []
    for p in rng(a.p):
        eng.eval(f"{tmp}.In.P = {p} kPa"); eng.solve()
        th = eng.value("/_HYD.HydrateTemp", "C")[0]
        err = [m for t, m in eng.msgs if t != "Info"]; eng.msgs.clear()
        rows.append((p, th)); print(f"P = {p:g} kPa  T_гидр = {th if th is None else round(th, 2)} C", err[:1])
    out_rows(rows, ["P, kPa", "T гидратообразования, C"], a.csv)
    if a.png:
        plot_xy([r[1] for r in rows], [r[0] / 1000 for r in rows], "T, °C", "P, МПа",
                a.title or f"Кривая гидратообразования ({a.stream})", a.png, "гидраты образуются левее/выше кривой")


def cmd_dew(a):
    eng = load(a.case)
    tmp = temp_stream(eng, a.stream)
    rows = []
    if a.kind == "water":
        eng.eval(f"{tmp}.In.T = 20 C"); eng.eval(f"{tmp}.In.P = 1000 kPa")
        for c in ['/_WDP = WaterDewPoint.WaterDewPoint("StartingT = 280.0 K; StepT = 2.0 K")', f"/_WDP.In -> {tmp}.Out",
                  "/_WDo = Stream.Stream_Material()", "/_WDo.In -> /_WDP.Out"]:
            eng.eval(c)
    else:
        eng.eval(f"{tmp}.In.VapFrac = {1 if a.kind == 'dew' else 0}")
    for p in rng(a.p):
        eng.eval(f"{tmp}.In.P = {p} kPa"); eng.solve()
        t = eng.value("/_WDP.DewPoint" if a.kind == "water" else f"{tmp}.Out.T", "C")[0]
        if a.kind == "water" and t is None:          # WaterDewPoint чувствителен к стартовой T — перебираем
            for t0 in (260, 300, 240, 320, 220):
                eng.msgs.clear(); eng.eval(f"/_WDP.StartingT = {t0} K"); eng.solve()
                t = eng.value("/_WDP.DewPoint", "C")[0]
                if t is not None:
                    break
        err = [m for tt, m in eng.msgs if tt != "Info"]; eng.msgs.clear()
        rows.append((p, t)); print(f"P = {p:g} kPa  T_{a.kind} = {t if t is None else round(t, 3)} C", err[:1])
    out_rows(rows, ["P, kPa", f"T {a.kind}, C"], a.csv)


def cmd_sweep(a):
    eng = load(a.case)
    gets = []
    for g in a.get:
        lab = None
        if "=" in g:
            g, lab = g.split("=", 1)
        p, u = sym.parse_path_unit(sym.unmangle(g))
        gets.append((p, u, lab or (p + (f", {u}" if u else ""))))
    setp = sym.unmangle(a.set)
    rows = []
    for x in rng(a.range):
        eng.eval(f"{setp} = {x} {a.unit or ''}".rstrip()); eng.solve()
        err = [m for t, m in eng.msgs if t != "Info"]; eng.msgs.clear()
        vals = []
        for p, u, _ in gets:
            try:
                m = re.match(r"^(.*)\[(\d+)\]$", p)          # /S.Out.Fraction[3] — элемент вектора
                v = eng.value(m.group(1) if m else p, u)[0]
                vals.append(v[int(m.group(2))] if m else (v if not isinstance(v, list) else None))
            except Exception:
                vals.append(None)
        rows.append([x] + vals)
        print(f"{setp} = {x:g}: " + "; ".join(f"{lab}={'-' if v is None else f'{v:.5g}'}" for (_, _, lab), v in zip(gets, vals))
              + (f"   !! {err[0]}" if err else ""))
    heads = [f"{a.xlabel or setp}" + (f", {a.unit}" if a.unit else "")] + [lab for _, _, lab in gets]
    out_rows(rows, heads, a.csv)
    if a.png:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        n = len(gets)
        fig, axes = plt.subplots(n, 1, figsize=(8, 2.6 * n + 0.6), sharex=True, squeeze=False)
        for i, (ax, (_, _, lab)) in enumerate(zip(axes[:, 0], gets)):
            ax.plot([r[0] for r in rows], [r[i + 1] for r in rows], "o-", ms=3)
            ax.set_ylabel(lab, fontsize=8); ax.grid(True, alpha=0.35)
        axes[-1, 0].set_xlabel(heads[0])
        if a.title:
            fig.suptitle(a.title)
        fig.tight_layout(); fig.savefig(a.png, dpi=150); print("png ->", a.png)


def out_rows(rows, heads, path):
    if not path:
        return
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(heads)
        for r in rows:
            w.writerow(["" if v is None else f"{v:.6g}".replace(".", ",") for v in r])
    print("csv ->", path)


def plot_xy(x, y, xl, yl, title, out, note=""):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(x, y, "o-", ms=4)
    ax.set_xlabel(xl); ax.set_ylabel(yl); ax.set_title(title); ax.grid(True, alpha=0.35)
    if note:
        ax.text(0.02, 0.97, note, transform=ax.transAxes, va="top", fontsize=8, color="dimgray")
    fig.tight_layout(); fig.savefig(out, dpi=150); print("png ->", out)


def main():
    argv = [sym.unmangle(x) for x in sys.argv[1:]]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("envelope"); p.add_argument("case"); p.add_argument("stream"); p.add_argument("out")
    p.add_argument("--csv"); p.add_argument("--title")
    p = sub.add_parser("hydrate"); p.add_argument("case"); p.add_argument("stream"); p.add_argument("--p", required=True)
    p.add_argument("--png"); p.add_argument("--csv"); p.add_argument("--title")
    p = sub.add_parser("dew"); p.add_argument("case"); p.add_argument("stream"); p.add_argument("--p", required=True)
    p.add_argument("--kind", default="dew", choices=["dew", "bubble", "water"]); p.add_argument("--csv")
    p = sub.add_parser("sweep"); p.add_argument("case"); p.add_argument("--set", required=True)
    p.add_argument("--range", required=True); p.add_argument("--unit"); p.add_argument("--get", action="append", required=True)
    p.add_argument("--png"); p.add_argument("--csv"); p.add_argument("--title"); p.add_argument("--xlabel")
    a = ap.parse_args(argv)
    globals()["cmd_" + a.cmd](a)
    sym.hard_exit(0)


if __name__ == "__main__":
    main()
