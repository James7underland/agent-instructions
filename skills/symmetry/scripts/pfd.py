#!/usr/bin/env python3
"""pfd.py — технологическая схема (PFD) кейса Symmetry по его топологии, без Visio и GUI.

  python pfd.py CASE.vsym OUT.png [--values] [--units SI] [--title "..."] [--props T,P,MoleFlow] [--no-energy]
                                  [--width 14] [--svg]
Топология берётся из _metadata.json внутри .vsym (есть и у кейсов, сохранённых движком). С --values движок
пересчитывает кейс и подписывает потоки (по умолчанию T, P, мольный расход). Раскладка: слои слева направо
по потоку, рециклы — обратные линии под схемой, энергетические потоки — красные штриховые.
Нужен, когда GUI-схема кейса, собранного скриптом, «рассыпана» (GUI не соединяет линии) или нужна картинка в отчёт.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

STREAM_T = {"Stream.Stream_Material": "mat", "Stream.Stream_Energy": "ene", "Stream.Stream_Signal": "sig"}


def load_meta(case):
    import vsym
    return vsym.load_meta(case)


def op_of(conn):
    """'/T1.Feed_10_feed' -> ('/T1', 'Feed_10_feed'); '/S1.In' -> ('/S1','In')."""
    if not conn:
        return None, None
    p, _, port = conn.rpartition(".")
    return p, port


def topology(meta):
    ops, streams = {}, []
    for u in (meta.get("root") or {}).get("unitOps", []) or []:
        tp, path = u.get("tp", ""), u.get("p")
        kind = STREAM_T.get(tp)
        if kind:
            src = dst = None
            for pr in (u.get("matPortsIn") or []) + (u.get("enePortsIn") or []):
                if pr.get("conn"):
                    src = op_of(pr["conn"])
            for pr in (u.get("matPortsOut") or []) + (u.get("enePortsOut") or []):
                if pr.get("conn"):
                    dst = op_of(pr["conn"])
            # у энергетических потоков порты могут называться иначе — ищем любые conn
            if kind == "ene" and not (src or dst):
                for key, val in u.items():
                    if isinstance(val, list):
                        for pr in val:
                            if isinstance(pr, dict) and pr.get("conn"):
                                o = op_of(pr["conn"])
                                if pr.get("n") == "In":
                                    src = o
                                else:
                                    dst = o
            streams.append({"name": u.get("n"), "path": path, "kind": kind, "src": src, "dst": dst})
        else:
            ops[path] = {"name": u.get("n"), "tp": tp, "path": path}
    return ops, streams


def category(tp):
    t = tp.lower()
    for key, cat in [("tower", "tower"), ("distillation", "tower"), ("absorber", "tower"), ("heatexchanger", "hx"),
                     ("multisided", "hx"), ("aircooler", "cooler"), ("cooler", "cooler"), ("heater", "heater"),
                     ("valve", "valve"), ("flash", "vessel"), ("separator", "vessel"), ("multifeedsep", "vessel"),
                     ("tank", "vessel"), ("expander", "expander"), ("compressor", "compressor"), ("pump", "pump"),
                     ("mixer", "mixer"), ("split", "splitter"), ("reactor", "reactor"), ("rxn", "reactor"),
                     ("cstr", "reactor"), ("pfr", "reactor"), ("controller", "ctrl"), ("pipe", "pipe")]:
        if key in t:
            return cat
    return "box"


SIZE = {"tower": (0.9, 3.2), "vessel": (0.8, 1.5), "hx": (1.0, 1.0), "heater": (0.8, 0.8), "cooler": (0.8, 0.8),
        "valve": (0.6, 0.5), "compressor": (1.0, 0.9), "expander": (1.0, 0.9), "pump": (0.8, 0.8),
        "mixer": (0.5, 0.5), "splitter": (0.5, 0.5), "reactor": (1.1, 1.4), "ctrl": (0.6, 0.6), "pipe": (1.2, 0.35),
        "box": (1.1, 0.8)}


def layout(ops, streams):
    """Слои по самому длинному пути от источников, обратные рёбра (рециклы) по DFS не учитываются."""
    edges = [(s["src"][0], s["dst"][0]) for s in streams
             if s["kind"] == "mat" and s["src"] and s["dst"] and s["src"][0] in ops and s["dst"][0] in ops]
    succ = {k: [] for k in ops}
    for a, b in edges:
        succ[a].append(b)
    indeg = {k: 0 for k in ops}
    for a, b in edges:
        indeg[b] += 1
    back, state = set(), {}
    # корни обхода: сначала аппараты с внешним питанием (поток без источника), затем без входящих связей
    fed = {s["dst"][0] for s in streams if s["kind"] == "mat" and s["dst"] and not (s["src"] and s["src"][0] in ops)}
    order = sorted(ops, key=lambda k: (k not in fed, indeg[k] > 0, k))

    def dfs(u):
        state[u] = 1
        for v in succ[u]:
            if state.get(v) == 1:
                back.add((u, v))
            elif not state.get(v):
                dfs(v)
        state[u] = 2
    for k in order:
        if not state.get(k):
            dfs(k)
    fwd = [(a, b) for a, b in edges if (a, b) not in back]
    layer = {k: 0 for k in ops}
    for _ in range(len(ops) + 1):
        changed = False
        for a, b in fwd:
            if layer[b] < layer[a] + 1:
                layer[b] = layer[a] + 1; changed = True
        if not changed:
            break
    # ступени: порядок внутри слоя — барицентр предшественников
    layers = {}
    for k, l in layer.items():
        layers.setdefault(l, []).append(k)
    pos_y = {}
    for l in sorted(layers):
        items = layers[l]
        def bary(k):
            pr = [pos_y[a] for a, b in fwd if b == k and a in pos_y]
            return sum(pr) / len(pr) if pr else 0.0
        items.sort(key=lambda k: (bary(k), k))
        n = len(items)
        for i, k in enumerate(items):
            pos_y[k] = (i - (n - 1) / 2) * 3.2 if not any(a in pos_y for a, b in fwd if b == k) or n > 1 else bary(k)
    pos = {k: (layer[k] * 3.6, pos_y[k]) for k in ops}
    return pos, back


def draw_symbol(ax, cat, x, y, w, h, label):
    import matplotlib.patches as P
    kw = dict(fill=True, fc="white", ec="black", lw=1.4, zorder=3)
    if cat == "tower":
        ax.add_patch(P.FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0,rounding_size=0.35", **kw))
        for i in range(1, 8):
            yy = y - h / 2 + i * h / 8
            ax.plot([x - w / 2 + 0.08, x + w / 2 - 0.08], [yy, yy], color="black", lw=0.6, zorder=4)
    elif cat == "vessel":
        ax.add_patch(P.FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0,rounding_size=0.3", **kw))
    elif cat in ("heater", "cooler", "pump"):
        ax.add_patch(P.Circle((x, y), w / 2, **kw))
        if cat == "pump":
            ax.add_patch(P.Polygon([[x - w / 4, y - w / 3], [x - w / 4, y + w / 3], [x + w / 2.4, y]], closed=True,
                                   fc="none", ec="black", lw=1.0, zorder=4))
        else:
            ax.plot([x - w / 2, x - w / 6, x + w / 6, x + w / 2], [y - w / 6, y + w / 6, y - w / 6, y + w / 6],
                    color="red" if cat == "heater" else "blue", lw=1.2, zorder=4)
    elif cat == "hx":
        ax.add_patch(P.Circle((x, y), w / 2, **kw))
        ax.plot([x - w / 2, x - w / 5, x + w / 5, x + w / 2], [y, y + w / 4, y - w / 4, y], color="black", lw=1.0, zorder=4)
    elif cat == "valve":
        ax.add_patch(P.Polygon([[x - w / 2, y - h / 2], [x - w / 2, y + h / 2], [x + w / 2, y - h / 2], [x + w / 2, y + h / 2]],
                               closed=True, **kw))
    elif cat in ("compressor", "expander"):
        big, small = h / 2, h / 4
        pts = [[x - w / 2, y - big], [x - w / 2, y + big], [x + w / 2, y + small], [x + w / 2, y - small]]
        if cat == "expander":
            pts = [[x - w / 2, y - small], [x - w / 2, y + small], [x + w / 2, y + big], [x + w / 2, y - big]]
        ax.add_patch(P.Polygon(pts, closed=True, **kw))
    elif cat in ("mixer", "splitter"):
        ax.add_patch(P.Circle((x, y), w / 2, **kw))
    elif cat == "reactor":
        ax.add_patch(P.FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0,rounding_size=0.2", **kw))
        ax.add_patch(P.Rectangle((x - w / 2 + 0.08, y - h / 2 + 0.08), w - 0.16, h - 0.16, fc="none", ec="black", lw=0.7, zorder=4))
    else:
        ax.add_patch(P.Rectangle((x - w / 2, y - h / 2), w, h, **kw))
    ax.text(x, y - h / 2 - 0.22, label, ha="center", va="top", fontsize=9, fontweight="bold", zorder=5)


def port_point(cat, pos, size, port, side, idx, n, nstages=0):
    import re
    x, y = pos
    w, h = size
    pl = (port or "").lower()
    if cat == "tower":
        m = re.search(r"_(\d+)_", port or "")
        top, bot = y + h / 2 - 0.12, y - h / 2 + 0.12
        if m and nstages:
            k = int(m.group(1))
            if side == "out" and k == 0:
                return (x + w / 2, top if "vap" in pl else top - 0.45)
            if side == "out" and k >= nstages:
                return (x + w / 2, bot)
            yy = top - (top - bot) * k / max(nstages, 1)
            return ((x - w / 2) if side == "in" else (x + w / 2), yy)
    if side == "out":
        if cat in ("tower", "vessel") and any(k in pl for k in ("vap", "condenser", "gas", "top")):
            return (x + w / 2, y + h / 2 - 0.15)
        if cat in ("tower", "vessel") and any(k in pl for k in ("liq", "reboiler", "bott")):
            return (x + w / 2, y - h / 2 + 0.15)
        return (x + w / 2, y + (0 if n <= 1 else (h * 0.7) * (0.5 - idx / (n - 1))))
    if cat == "tower" and "feed" in pl:
        return (x - w / 2, y + (0 if n <= 1 else (h * 0.6) * (0.5 - idx / (n - 1))))
    return (x - w / 2, y + (0 if n <= 1 else (h * 0.6) * (0.5 - idx / (n - 1))))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("case"); ap.add_argument("out")
    ap.add_argument("--values", action="store_true"); ap.add_argument("--units", default="SI")
    ap.add_argument("--props", default="T,P,MoleFlow"); ap.add_argument("--title", default="")
    ap.add_argument("--no-energy", action="store_true"); ap.add_argument("--width", type=float, default=0)
    a = ap.parse_args()
    meta = load_meta(a.case)
    ops, streams = topology(meta)
    if not ops:
        sys.exit("в кейсе нет unit operations (или подсхемы — рисуется только корневая схема)")
    pos, back = layout(ops, streams)
    vals = {}
    if a.values:
        import sym
        eng = sym.Engine(echo=lambda *x: None)
        sym.open_case(eng, a.case)
        eng.eval(f"units {a.units}"); eng.msgs.clear()
        for s in streams:
            if s["kind"] != "mat":
                continue
            row = []
            for p in a.props.split(","):
                try:
                    v, u = eng.value(f"{s['path']}.Out.{p}")
                    if v is not None:
                        short = {"T": "T", "P": "P", "MoleFlow": "F", "MassFlow": "G", "VapFrac": "e"}.get(p, p)
                        v = 0.0 if abs(v) < 1e-20 else v
                        row.append(f"{short}={v:.4g} {u}".strip())
                except Exception:
                    pass
            vals[s["name"]] = row
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
    W = a.width or max(8, (max(xs) - min(xs)) * 0.75 + 6)
    H = max(4.5, (max(ys) - min(ys)) * 0.75 + 4.5)
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_aspect("equal"); ax.axis("off")
    cats = {k: category(o["tp"]) for k, o in ops.items()}
    for k, o in ops.items():
        draw_symbol(ax, cats[k], *pos[k], *SIZE[cats[k]], o["name"])
    # счётчики портов для разнесения
    outs, ins = {}, {}
    for s in streams:
        if s["src"] and s["src"][0] in ops:
            outs.setdefault(s["src"][0], []).append(s["src"][1])
        if s["dst"] and s["dst"][0] in ops:
            ins.setdefault(s["dst"][0], []).append(s["dst"][1])
    import re as _re
    nst = {}
    for k in ops:
        nums = [int(m) for pl in outs.get(k, []) + ins.get(k, []) for m in _re.findall(r"_(\d+)_", pl or "")]
        nst[k] = max(nums) if nums else 0
    ymin = min(ys) - 2.6
    rec_k = 0
    for s in streams:
        src, dst = s["src"], s["dst"]
        if s["kind"] == "sig":
            continue
        if s["kind"] == "ene":
            if a.no_energy:
                continue
            k = (src or dst)[0] if (src or dst) else None
            if k not in ops:
                continue
            x, y = pos[k]; w, h = SIZE[cats[k]]
            if src:
                p0, p1 = (x, y - h / 2), (x + 0.6, y - h / 2 - 0.7)
            else:
                p0, p1 = (x - 0.6, y - h / 2 - 0.7), (x, y - h / 2)
            ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle="-|>", color="red", lw=1.1, ls="--"), zorder=2)
            ax.text(p1[0] + 0.05 if src else p0[0] - 0.05, (p0[1] + p1[1]) / 2 - 0.1, s["name"], color="red", fontsize=7,
                    ha="left" if src else "right")
            continue
        if src and src[0] in ops:
            lst = outs[src[0]]
            p0 = port_point(cats[src[0]], pos[src[0]], SIZE[cats[src[0]]], src[1], "out", lst.index(src[1]), len(lst),
                            nst[src[0]])
        else:
            p0 = None
        if dst and dst[0] in ops:
            lst = ins[dst[0]]
            p1 = port_point(cats[dst[0]], pos[dst[0]], SIZE[cats[dst[0]]], dst[1], "in", lst.index(dst[1]), len(lst),
                            nst[dst[0]])
        else:
            p1 = None
        if p0 is None and p1 is None:
            continue
        ext = None
        if p0 is None:
            p0 = (p1[0] - 1.6, p1[1]); ext = "feed"
        if p1 is None:
            p1 = (p0[0] + 1.6, p0[1]); ext = "prod"
        is_back = src and dst and (src[0], dst[0]) in back
        if is_back:
            yb = ymin - 0.5 * rec_k; rec_k += 1
            pts = [p0, (p0[0] + 0.5, p0[1]), (p0[0] + 0.5, yb), (p1[0] - 0.5, yb), (p1[0] - 0.5, p1[1]), p1]
        elif abs(p0[1] - p1[1]) < 1e-6:
            pts = [p0, p1]
        else:
            xm = (p0[0] + p1[0]) / 2 if p1[0] > p0[0] + 0.4 else p0[0] + 0.5
            pts = [p0, (xm, p0[1]), (xm, p1[1]), p1]
        xx = [p[0] for p in pts]; yy = [p[1] for p in pts]
        ax.plot(xx[:-1] + [xx[-1] - 0.001], yy, color="black", lw=1.2, zorder=1)
        ax.annotate("", xy=pts[-1], xytext=pts[-2], arrowprops=dict(arrowstyle="-|>", color="black", lw=1.2), zorder=2)
        if ext:
            # внешние потоки: подпись в одну колонку у свободного конца линии (не наезжает на соседние)
            txt = s["name"] + (": " + ", ".join(vals[s["name"]]) if vals.get(s["name"]) else "")
            xe, ye = (p0[0] - 0.08, p0[1]) if ext == "feed" else (p1[0] + 0.08, p1[1])
            ax.text(xe, ye, txt, ha="right" if ext == "feed" else "left", va="center", fontsize=6.8, color="navy",
                    zorder=5, linespacing=1.15)
            continue
        # подпись на самом длинном горизонтальном участке
        segs = [(abs(pts[i + 1][0] - pts[i][0]), i) for i in range(len(pts) - 1) if abs(pts[i + 1][1] - pts[i][1]) < 1e-6]
        L, i = max(segs) if segs else (0, 0)
        mx, my = (pts[i][0] + pts[i + 1][0]) / 2, pts[i][1]
        ax.text(mx, my + 0.12, s["name"], ha="center", va="bottom", fontsize=8, color="navy", zorder=5)
        if vals.get(s["name"]):
            ax.text(mx, my - 0.12, "\n".join(vals[s["name"]]), ha="center", va="top", fontsize=6.5, color="dimgray",
                    zorder=5, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    if a.title:
        ax.set_title(a.title, fontsize=12)
    ax.autoscale_view()
    ax.margins(0.08)
    fig.tight_layout()
    fig.savefig(a.out, dpi=170)
    print(f"pfd -> {a.out}  (операций {len(ops)}, потоков {len(streams)}, рециклов {len(back)})")
    if a.values:
        sym.hard_exit(0)


if __name__ == "__main__":
    main()
