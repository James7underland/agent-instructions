#!/usr/bin/env python3
"""visio_layout.py — координаты фигур PFD для скрипта .tst: вставляет Info.Visio в конструкторы.

GUI Symmetry рисует PFD (фигуры + линии связей) только когда команды выполняются В САМОМ GUI; координаты берёт из
параметров конструктора: аппарат — "Info.Visio = {}; Info.Visio.X = 4.5; Info.Visio.Y = 6.0" (дюймы, Y вверх),
поток — "... Info.Visio.X0 = ..; Y0 = ..; X1 = ..; Y1 = .." (концы линии). Кейс, сохранённый движком, PFD не имеет —
GUI сам ставит аппараты в ряд, потоки списком, без линий.

  python visio_layout.py model.tst -o model_vis.tst [--dx 1.6 --dy 1.3]
Раскладка: аппараты по слоям (длина пути от входных потоков), в слое — сверху вниз; регуляторы/логика — нижний ряд;
поток — между аппаратами-концами (граничные — отрезком слева/справа). Уже заданные Info.Visio не трогаются.
"""
from __future__ import annotations

import argparse
import re
from collections import defaultdict

CREATE = re.compile(r'^(/[A-Za-z_][\w%-]*)\s*=\s*([A-Za-z_][\w.]*)\((.*)\)\s*(#.*)?$')
CONN = re.compile(r'^(/[A-Za-z_][\w%-]*)\.([\w%]+)\s*->\s*(/[A-Za-z_][\w%-]*)\.([\w%]+)\s*$')
SIGNAL_KINDS = ("Controller.", "DigitalLogic.", "CauseEffect.", "Scheduler.", "SelectorBlock.", "DataFilter.",
                "ProCalc.", "Set.", "Balance.", "OPCClient.", "Envelope.", "HydrateThermoBased.", "WaterDewPoint.",
                "Properties.", "CaseStudy.")


def parse(lines):
    objs, order, edges = {}, [], []
    for ln in lines:
        s = ln.strip()
        m = CREATE.match(s)
        if m and "." not in m.group(1)[1:]:
            objs[m.group(1)] = m.group(2)
            order.append(m.group(1))
            continue
        m = CONN.match(s)
        if m:
            a, pa, b, pb = m.groups()
            edges.append((a, pa, b, pb))
    return objs, order, edges


def layout(lines, dx=1.6, dy=1.3, x0=1.0, ytop=7.5):
    objs, order, edges = parse(lines)
    is_stream = {o: objs[o].startswith("Stream.Stream_") for o in objs}
    # поток: откуда (аппарат, порт) → куда (аппарат, порт)
    s_from, s_to = {}, {}
    for a, pa, b, pb in edges:
        if a in is_stream and is_stream.get(a) and pa == "In":      # /S1.In -> /U.Out  (поток получает из U)
            s_from[a] = b
        elif b in is_stream and is_stream.get(b) and pb == "In":    # /U.Out -> /S1.In
            s_from[b] = a
        elif a in is_stream and is_stream.get(a) and pa == "Out":   # /S1.Out -> /U.In
            s_to[a] = b
        elif b in is_stream and is_stream.get(b) and pb == "Out":   # /U.In -> /S1.Out
            s_to[b] = a
    units = [o for o in order if not is_stream[o] and not objs[o].startswith(SIGNAL_KINDS)]
    signals = [o for o in order if objs[o].startswith(SIGNAL_KINDS)]
    succ = defaultdict(set)
    for s in objs:
        if is_stream.get(s) and s in s_from and s in s_to:
            succ[s_from[s]].add(s_to[s])
    level = {u: 0 for u in units}
    for _ in range(len(units)):                     # длиннейший путь (с защитой от рециклов)
        changed = False
        for u in units:
            for v in succ[u]:
                if v in level and level[v] < level[u] + 1 and level[u] + 1 < len(units):
                    level[v] = level[u] + 1
                    changed = True
        if not changed:
            break
    cols = defaultdict(list)
    for u in units:
        cols[level[u]].append(u)
    pos = {}
    for c, us in cols.items():
        for i, u in enumerate(us):
            pos[u] = (x0 + dx * (c + 1), ytop - 0.5 - dy * i - (0.4 if c % 2 else 0.0))
    ymin = min([p[1] for p in pos.values()] + [ytop])
    for i, s in enumerate(signals):
        pos[s] = (x0 + dx * (i % 8), ymin - dy - dy * (i // 8))
    spos = {}
    for s in objs:
        if not is_stream.get(s):
            continue
        a, b = s_from.get(s), s_to.get(s)
        if a in pos and b in pos:
            (xa, ya), (xb, yb) = pos[a], pos[b]
            spos[s] = (xa + 0.4, ya, xb - 0.4, yb)
        elif b in pos:                                   # входной граничный
            xb, yb = pos[b]
            spos[s] = (xb - dx + 0.1, yb, xb - 0.4, yb)
        elif a in pos:                                   # выходной граничный
            xa, ya = pos[a]
            spos[s] = (xa + 0.4, ya, xa + dx - 0.1, ya)
    out = []
    for ln in lines:
        m = CREATE.match(ln.strip())
        if m and "Info.Visio" not in ln and (m.group(1) in pos or m.group(1) in spos):
            name, ctor, args, com = m.group(1), m.group(2), m.group(3).strip(), m.group(4) or ""
            if name in spos:
                X0, Y0, X1, Y1 = spos[name]
                vis = f"Info.Visio = {{}}; Info.Visio.X0 = {X0:.2f}; Info.Visio.Y0 = {Y0:.2f}; " \
                      f"Info.Visio.X1 = {X1:.2f}; Info.Visio.Y1 = {Y1:.2f}"
            else:
                X, Y = pos[name]
                vis = f"Info.Visio = {{}}; Info.Visio.X = {X:.2f}; Info.Visio.Y = {Y:.2f}"
            if not args:
                args = f'"{vis}"'
            elif args.startswith('"') and args.endswith('"'):
                inner = args[1:-1].rstrip().rstrip(";")
                args = f'"{inner}; {vis}"'
            else:                                         # нестандартные аргументы — не трогаем
                out.append(ln)
                continue
            out.append(f"{name} = {ctor}({args}){(' ' + com) if com else ''}")
        else:
            out.append(ln.rstrip("\n"))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tst")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--dx", type=float, default=1.6)
    ap.add_argument("--dy", type=float, default=1.3)
    a = ap.parse_args()
    lines = open(a.tst, encoding="utf-8-sig").read().splitlines()
    res = layout(lines, a.dx, a.dy)
    open(a.out, "w", encoding="utf-8").write("\n".join(res) + "\n")
    print(f"# {a.out}: координаты PFD добавлены")


if __name__ == "__main__":
    main()
