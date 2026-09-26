"""Графики для отчётов ТАУ «как на миллиметровке»: геометрия в миллиметрах, общая для всех лабораторных.

Зачем свой модуль, а не экспорт Mathcad: у Mathcad размер рамки задаётся в своих единицах (~7 pt), клетки выходят
неквадратными, а подписи выражений («Re(W1·A), Re(W(i·w))») торчат вместо подписей осей. Здесь:
  * рамка графика = целое число клеток, клетка = целое число мм; картинка вставляется в Word в натуральную
    величину (Mm(fig.width_mm)) — на распечатке сетку можно мерить линейкой;
  * одинаковый масштаб осей для АФЧХ/годографов (квадратная клетка, один шаг по Re и Im);
  * подписи осей с единицами, десятичная запятая, Times New Roman; кривые гладкие (плотная сетка частот);
  * подписи точек (частоты на АФЧХ) раскладываются автоматически: не пересекают кривые, оси, точки и друг друга;
    при необходимости — с тонкой выноской.

API (всё в мм, данные — в единицах осей):
  plan_linear(lo, hi, avail_mm, min_cell=5, max_cell=15)   -> Axis (lo, hi, step, n, cell)
  plan_square(xlo, xhi, ylo, yhi, avail_w, avail_h, ...)   -> (Axis x, Axis y) с общим шагом и клеткой
  Sheet(ax_x, ax_y, margins=(l, b, r, t), logx=None)        -> фигура; .ax, .to_mm(x, y), .save(path)
  sheet.place_labels(points, texts, obstacles=[curves...])  -> раскладка подписей без пересечений
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.ticker import FixedLocator, FuncFormatter  # noqa: E402

MM = 1 / 25.4
GRID = "#35c435"      # зелёная «миллиметровка»
CURVE = "#1f3fd0"     # расчётная кривая
POINT = "#e01010"     # экспериментальные точки
CURVE2 = "#d01818"
POINT2 = "#1030c0"

plt.rcParams.update({
    "font.family": "Times New Roman",
    "mathtext.fontset": "stix",
    "axes.linewidth": 0.8,
    "xtick.major.size": 0, "ytick.major.size": 0, "xtick.minor.size": 0, "ytick.minor.size": 0,
    "xtick.major.pad": 2.5, "ytick.major.pad": 2.5,
})

STEPS = [1, 2, 2.5, 5]


def nice_steps(lo=1e-4, hi=1e5):
    k = math.floor(math.log10(lo))
    while 10 ** k <= hi:
        for s in STEPS:
            yield s * 10 ** k
        k += 1


def decimals(step):
    for d in range(0, 8):
        if abs(round(step, d) - step) < 1e-9 * max(1, abs(step)):
            return d
    return 6


def fmt(v, d):
    if abs(v) < 1e-12:
        return "0"
    s = f"{v:.{d}f}"
    if s.startswith("-") and float(s) == 0:
        s = s[1:]
    return s.replace(".", ",").replace("-", "−")


@dataclass
class Axis:
    lo: float
    hi: float
    step: float
    n: int
    cell: float  # мм на одну клетку

    @property
    def mm(self):
        return self.n * self.cell

    def ticks(self):
        return [self.lo + i * self.step for i in range(self.n + 1)]


def plan_linear(lo, hi, avail_mm, min_cell=5, max_cell=15, pad=0.0):
    """Наименьший «круглый» шаг, при котором клетка (целые мм) не меньше min_cell."""
    for s in nice_steps():
        a = math.floor((lo - pad * (hi - lo)) / s + 1e-9) * s
        b = math.ceil((hi + pad * (hi - lo)) / s - 1e-9) * s
        n = int(round((b - a) / s))
        if n < 1:
            continue
        cell = min(max_cell, math.floor(avail_mm / n))
        if cell >= min_cell:
            return Axis(a, b, s, n, float(cell))
    raise ValueError("не удалось подобрать шаг")


def plan_fill(lo, hi, avail_mm, min_cell=5, max_cell=15, pin_hi=False, near=0.92):
    """Ось «по данным» и максимально крупно: диапазон — ровно данные, округлённые до шага (пустого места не больше
    одной клетки), клетка — целые мм, как можно крупнее при данном шаге. Из всех «круглых» шагов берутся те, что дают
    рисунок не меньше near·(лучший), и среди них — самый мелкий шаг (сетка ближе к миллиметровке).
    pin_hi оставлен для совместимости (верх и так = данные, округлённые вверх)."""
    span = max(hi - lo, 1e-9)
    cands = []
    for st in nice_steps(span / 400, span * 2):
        a = math.floor(lo / st + 1e-9) * st
        b = math.ceil(hi / st - 1e-9) * st
        n = int(round((b - a) / st))
        if n < 1:
            continue
        c = min(max_cell, int(avail_mm // n))
        if c >= min_cell:
            cands.append((st, n, c, a))
    if not cands:
        return plan_linear(lo, hi, avail_mm, min_cell, max_cell)
    best_len = max(n * c for st, n, c, a in cands)
    st, n, c, a = min((x for x in cands if x[1] * x[2] >= near * best_len), key=lambda x: x[0])
    return Axis(a, a + n * st, st, n, float(c))


def plan_square_fill(xlo, xhi, ylo, yhi, avail_w, avail_h, min_cell=5, max_cell=15, margin_cells=(1, 1, 1, 1)):
    """Квадратная клетка (целые мм) и один шаг по обеим осям, сетка на всё доступное место.
    Масштаб (мм на единицу) — максимальный, при котором данные + margin_cells помещаются; диапазон — только данные
    + margin_cells (запас под подписи частот), пустыми клетками лист не добивается."""
    ml, mb, mr, mt = margin_cells
    best = None
    span = max(xhi - xlo, yhi - ylo, 1e-9)
    for st in nice_steps(span / 400, span * 2):
        a = math.floor(xlo / st + 1e-9) * st - ml * st
        b = math.ceil(xhi / st - 1e-9) * st + mr * st
        c0 = math.floor(ylo / st + 1e-9) * st - mb * st
        d0 = math.ceil(yhi / st - 1e-9) * st + mt * st
        nx0, ny0 = int(round((b - a) / st)), int(round((d0 - c0) / st))
        cell = min(max_cell, math.floor(min(avail_w / nx0, avail_h / ny0)))
        if cell < min_cell:
            continue
        key = (cell / st, -st)
        if best is None or key > best[0]:
            best = (key, st, cell, a, b, c0, d0, nx0, ny0)
    if best is None:
        return plan_square(xlo, xhi, ylo, yhi, avail_w, avail_h, min_cell, max_cell, margin_cells)
    _, st, cell, a, b, c0, d0, nx0, ny0 = best
    # остаток листа пустыми клетками не заполняем: рисунок в «лишнем» направлении просто уже
    return Axis(a, b, st, nx0, float(cell)), Axis(c0, d0, st, ny0, float(cell))


def plan_square(xlo, xhi, ylo, yhi, avail_w, avail_h, min_cell=5, max_cell=15, margin_cells=(1, 1, 1, 1)):
    """Общий шаг и квадратная клетка. margin_cells = (слева, снизу, справа, сверху) — запас под подписи."""
    ml, mb, mr, mt = margin_cells
    for s in nice_steps():
        a = math.floor(xlo / s + 1e-9) * s - ml * s
        b = math.ceil(xhi / s - 1e-9) * s + mr * s
        c = math.floor(ylo / s + 1e-9) * s - mb * s
        d = math.ceil(yhi / s - 1e-9) * s + mt * s
        nx, ny = int(round((b - a) / s)), int(round((d - c) / s))
        cell = min(max_cell, math.floor(min(avail_w / nx, avail_h / ny)))
        if cell >= min_cell:
            return Axis(a, b, s, nx, float(cell)), Axis(c, d, s, ny, float(cell))
    raise ValueError("не удалось подобрать шаг")


def labeled_ticks(axis, k):
    """Подписываемые линии: кратные k·шаг (0 всегда среди них, если попадает в диапазон)."""
    return [t for t in axis.ticks() if abs(round(t / axis.step)) % k == 0]


def label_every(axis, text_mm):
    """Подписывать каждую k-ю линию сетки, чтобы подписи не слипались."""
    for k in (1, 2, 4, 5, 10):
        if axis.cell * k >= text_mm:
            return k
    return 10


class Sheet:
    """Фигура с рамкой ровно ax_x.mm × ax_y.mm миллиметров. margins — поля вокруг рамки (мм) под числа и подписи."""

    def __init__(self, ax_x: Axis, ax_y: Axis, margins=(17, 13, 6, 5), logx=None, font=9.5, crossed=True):
        l, b, r, t = margins
        self.ax_x, self.ax_y, self.logx = ax_x, ax_y, logx
        self.pw, self.ph = (logx["mm"] if logx else ax_x.mm), ax_y.mm
        self.W, self.H = l + self.pw + r, b + self.ph + t
        self.margins = margins
        self.fig = plt.figure(figsize=(self.W * MM, self.H * MM))
        self.ax = self.fig.add_axes([l / self.W, b / self.H, self.pw / self.W, self.ph / self.H])
        self.font = font
        self.labels_placed = []  # прямоугольники (мм) уже поставленных подписей
        ax = self.ax
        ax.set_ylim(ax_y.lo, ax_y.hi)
        if logx:
            ax.set_xscale("log")
            ax.set_xlim(logx["lo"], logx["hi"])
        else:
            ax.set_xlim(ax_x.lo, ax_x.hi)
        self._grid()
        self.crossed = crossed
        if crossed:  # формат Crossed (как в Mathcad): без рамки, оси со стрелками, числа вдоль осей
            for sp in ax.spines.values():
                sp.set_visible(False)
            ax.tick_params(labelbottom=False, labelleft=False, labeltop=False, labelright=False)

    # ---------------------------------------------------------------- сетка и оси
    def _grid(self):
        ax, font = self.ax, self.font
        ay = self.ax_y
        ky = label_every(ay, font * 0.45)
        ay_d = decimals(ay.step)
        ay_d = decimals(ay.step * ky)
        ax.yaxis.set_major_locator(FixedLocator(labeled_ticks(ay, ky)))
        ax.yaxis.set_minor_locator(FixedLocator(ay.ticks()))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt(v, ay_d)))
        if self.logx:
            lo, hi = self.logx["lo"], self.logx["hi"]
            k0, k1 = round(math.log10(lo)), round(math.log10(hi))
            major = [10.0 ** k for k in range(k0, k1 + 1)]
            minor = [m * 10.0 ** k for k in range(k0, k1) for m in range(1, 10)] + [10.0 ** k1]
            ax.xaxis.set_major_locator(FixedLocator(major))
            ax.xaxis.set_minor_locator(FixedLocator(minor))
            labeled = set(major + [m * 10.0 ** k for k in range(k0, k1) for m in (2, 5)])
            ax.xaxis.set_major_locator(FixedLocator(sorted(labeled)))
            ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt(v, max(0, -math.floor(math.log10(v) + 1e-9)))))
        else:
            axx = self.ax_x
            kx = label_every(axx, len(fmt(axx.hi, decimals(axx.step))) * 0.5 * font * 0.353 + 3)
            ax_d = decimals(axx.step * kx)
            ax.xaxis.set_major_locator(FixedLocator(labeled_ticks(axx, kx)))
            ax.xaxis.set_minor_locator(FixedLocator(axx.ticks()))
            ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt(v, ax_d)))
        ax.tick_params(labelsize=font, which="both")
        ax.grid(True, which="both", color=GRID, lw=0.45, zorder=0)
        ax.set_axisbelow(True)
        for sp in ax.spines.values():
            sp.set_color("black")
            sp.set_zorder(5)

    def zero_axes(self, x=True, y=True, lw=1.1):
        """Координатные оси через 0 (начало координат отмечено)."""
        if y and self.ax_y.lo < 0 < self.ax_y.hi:
            self.ax.axhline(0, color="black", lw=lw, zorder=3)
        if x and not self.logx and self.ax_x.lo < 0 < self.ax_x.hi:
            self.ax.axvline(0, color="black", lw=lw, zorder=3)

    def _txt(self, X, Y, text, size, ha="center", va="center", color="black"):
        x, y = self.from_mm(X, Y)
        return self.ax.text(x, y, text, fontsize=size, ha=ha, va=va, color=color, clip_on=False, zorder=9)

    def _line(self, X0, Y0, X1, Y1, lw=1.1):
        (x0, y0), (x1, y1) = self.from_mm(X0, Y0), self.from_mm(X1, Y1)
        self.ax.plot([x0, x1], [y0, y1], color="black", lw=lw, zorder=8, clip_on=False, solid_capstyle="butt")

    def _arrow(self, X0, Y0, X1, Y1, lw=1.1):
        (x0, y0), (x1, y1) = self.from_mm(X0, Y0), self.from_mm(X1, Y1)
        self.ax.annotate("", xy=(x1, y1), xytext=(x0, y0), annotation_clip=False, zorder=8,
                         arrowprops=dict(arrowstyle="-|>", lw=lw, color="black", mutation_scale=11,
                                         shrinkA=0, shrinkB=0))

    def _free(self, box, curves, marks):
        x0, x1, y0, y1 = box
        if len(curves) and np.any((curves[:, 0] > x0) & (curves[:, 0] < x1) & (curves[:, 1] > y0) & (curves[:, 1] < y1)):
            return False
        if len(marks):
            dx = np.clip(marks[:, 0], x0, x1) - marks[:, 0]
            dy = np.clip(marks[:, 1], y0, y1) - marks[:, 1]
            if np.any(np.hypot(dx, dy) < 1.2):
                return False
        for (a0, a1, b0, b1) in self.labels_placed:
            if not (x1 < a0 or x0 > a1 or y1 < b0 or y0 > b1):
                return False
        return True

    def crossed_axes(self, xlabel, ylabel, x_at=None, y_at=None, xnum="below", obstacles=(), markers=(),
                     right=None, arrow=8, lsize=12):
        """Оси формата Crossed: горизонтальная — на уровне y = x_at (по умолчанию 0, если он в диапазоне, иначе низ),
        вертикальная — x = y_at (0 или левый край); стрелки выходят за сетку, подписи осей — у концов стрелок.
        Числа — вдоль осей; число, которое легло бы на кривую/точку/подпись частоты, не ставится.
        Вызывать ПОСЛЕ place_labels (подписи частот важнее чисел осей).
        xnum: "below" | "above" | "bottom" (числа по нижнему краю сетки — для ЛАЧХ, где у оси тесно).
        right: вторая шкала справа dict(label, ticks=[значения], to_mm=функция(v)->Y, dec, skip=[значения])."""
        curves = np.vstack([o for o in obstacles if len(o)]) if obstacles else np.zeros((0, 2))
        marks = np.asarray(markers, float).reshape(-1, 2)
        font = self.font
        if x_at is None:
            x_at = 0 if self.ax_y.lo <= 0 <= self.ax_y.hi else self.ax_y.lo
        if y_at is None:
            y_at = self.logx["lo"] if self.logx else (0 if self.ax_x.lo <= 0 <= self.ax_x.hi else self.ax_x.lo)
        Xl = float(self.to_mm(y_at, x_at)[0])
        Yl = float(self.to_mm(y_at, x_at)[1])
        inner = 0.5 < Xl < self.pw - 0.5 and 0.5 < Yl < self.ph - 0.5  # оси пересекаются внутри сетки
        th = self.text_size_mm("0", font)[1]

        def put(X, Y, text, ha="center", force=False):
            w, h = self.text_size_mm(text, font)
            cx = X if ha == "center" else (X - w / 2 if ha == "right" else X + w / 2)
            box = (cx - w / 2 - 0.3, cx + w / 2 + 0.3, Y - h / 2 - 0.2, Y + h / 2 + 0.2)
            if not force and not self._free(box, curves, marks):
                return None
            self._txt(cx, Y, text, font)
            self.labels_placed.append(box)
            return box

        # числа по X
        if self.logx:
            lo, hi = self.logx["lo"], self.logx["hi"]
            k0, k1 = round(math.log10(lo)), round(math.log10(hi))
            xt = [10.0 ** k for k in range(k0, k1 + 1)]  # только декады: 0,01 0,1 1 10
            xtxt = [fmt(v, max(0, -math.floor(math.log10(v) + 1e-9))) for v in xt]
        else:
            axx = self.ax_x
            kx = label_every(axx, len(fmt(axx.hi, decimals(axx.step))) * 0.5 * font * 0.353 + 3)
            xt = labeled_ticks(axx, kx)
            xtxt = [fmt(v, decimals(axx.step * kx)) for v in xt]
        Ynum = {"below": Yl - 1.3 - th / 2, "above": Yl + 1.3 + th / 2, "bottom": -2.8 - th / 2}[xnum]  # ниже, чтобы не задевать нижние числа шкал Y
        last_half = 0.0
        for v, t in zip(xt, xtxt):
            if abs(v - y_at) < 1e-12 and (inner or not self.logx):
                continue  # ноль в начале координат ставится один раз ниже
            X = float(self.to_mm(v, x_at)[0])
            b = put(X, Ynum, t)
            if b and X > self.pw - 1:
                last_half = b[1] - self.pw
        # числа по Y
        ay = self.ax_y
        ky = label_every(ay, font * 0.45)
        for v in labeled_ticks(ay, ky):
            if abs(v - x_at) < 1e-12 and not self.logx:
                continue
            Y = float(self.to_mm(y_at, v)[1])
            put(Xl - 1.3, Y, fmt(v, decimals(ay.step * ky)), ha="right")
        if not self.logx:  # «0» в начале координат (снизу слева от пересечения осей)
            oy = Yl - 1.3 - th / 2 if xnum != "above" else Yl + 1.3 + th / 2
            put(Xl - 1.3, oy, "0", ha="right")
        # вторая шкала справа (у ЛАЧХ — ЛФЧХ)
        right_w = 0.0
        if right:
            for v in right["ticks"]:
                if v in right.get("skip", ()):
                    continue
                b = put(self.pw + 1.3, float(right["to_mm"](v)), fmt(v, right.get("dec", 0)), ha="left")
                if b:
                    right_w = max(right_w, b[1] - self.pw)
            self._line(self.pw, 0, self.pw, self.ph)
            self._arrow(self.pw, self.ph - 0.01, self.pw, self.ph + arrow)
            w, h = self.text_size_mm(right["label"], lsize)
            self._txt(self.pw - 1.8, self.ph + arrow - h / 2, right["label"], lsize, ha="right")
        # горизонтальная ось: линия через всю сетку + стрелка, подпись рядом с концом стрелки
        wl, hl = self.text_size_mm(xlabel, lsize)
        start = self.pw + max(last_half, right_w) + 2
        tip = start + wl + 1
        self._line(0, Yl, self.pw, Yl)
        self._arrow(self.pw - 0.01, Yl, tip, Yl)
        side = -1 if xnum == "above" or Yl > self.ph - 1 else 1   # подпись с той стороны, где нет чисел
        if xnum == "bottom":
            side = -1
        ylab = Yl + side * (1.5 + hl / 2)
        self._txt(start + wl / 2, ylab, xlabel, lsize)
        # вертикальная ось со стрелкой, подпись справа от конца стрелки
        self._line(Xl, 0, Xl, self.ph)
        self._arrow(Xl, self.ph - 0.01, Xl, self.ph + arrow)
        self._txt(Xl + 1.8, self.ph + arrow - self.text_size_mm(ylabel, lsize)[1] / 2, ylabel, lsize, ha="left")
        self.need = dict(right=tip + 1, top=self.ph + arrow + 1)

    def labels(self, xlabel, ylabel, size=12):
        self.ax.set_xlabel(xlabel, fontsize=size, labelpad=3)
        self.ax.set_ylabel(ylabel, fontsize=size, labelpad=4)

    # ---------------------------------------------------------------- координаты в мм (от левого нижнего угла рамки)
    def to_mm(self, x, y):
        x, y = np.asarray(x, float), np.asarray(y, float)
        if self.logx:
            lo, hi = math.log10(self.logx["lo"]), math.log10(self.logx["hi"])
            X = (np.log10(x) - lo) / (hi - lo) * self.pw
        else:
            X = (x - self.ax_x.lo) / (self.ax_x.hi - self.ax_x.lo) * self.pw
        Y = (y - self.ax_y.lo) / (self.ax_y.hi - self.ax_y.lo) * self.ph
        return X, Y

    def from_mm(self, X, Y):
        if self.logx:
            lo, hi = math.log10(self.logx["lo"]), math.log10(self.logx["hi"])
            x = 10 ** (lo + X / self.pw * (hi - lo))
        else:
            x = self.ax_x.lo + X / self.pw * (self.ax_x.hi - self.ax_x.lo)
        y = self.ax_y.lo + Y / self.ph * (self.ax_y.hi - self.ax_y.lo)
        return x, y

    def curve_mm(self, x, y, spacing=0.35):
        """Кривая в мм, передискретизированная до шага ≤ spacing (для проверки пересечений), только внутри рамки."""
        X, Y = self.to_mm(x, y)
        ok = np.isfinite(X) & np.isfinite(Y)
        X, Y = X[ok], Y[ok]
        out = [np.array([X[0], Y[0]])]
        for i in range(1, len(X)):
            d = math.hypot(X[i] - X[i - 1], Y[i] - Y[i - 1])
            k = max(1, int(d / spacing))
            for j in range(1, k + 1):
                out.append(np.array([X[i - 1] + (X[i] - X[i - 1]) * j / k, Y[i - 1] + (Y[i] - Y[i - 1]) * j / k]))
        P = np.array(out)
        inside = (P[:, 0] >= -1) & (P[:, 0] <= self.pw + 1) & (P[:, 1] >= -1) & (P[:, 1] <= self.ph + 1)
        return P[inside]

    def text_size_mm(self, text, size):
        r = self.fig.canvas.get_renderer()
        t = self.fig.text(0, 0, text, fontsize=size)
        bb = t.get_window_extent(renderer=r)
        t.remove()
        return bb.width / self.fig.dpi * 25.4, bb.height / self.fig.dpi * 25.4

    # ---------------------------------------------------------------- раскладка подписей
    def place_labels(self, pts_mm, texts, obstacles, markers_mm=(), size=8.5, color="black",
                     prefer=None, max_r=45, gap=0.7, hline=True):
        """pts_mm — точки (мм), texts — подписи; obstacles — список кривых (массивы мм, см. curve_mm), которые
        нельзя пересекать ни подписью, ни выноской; markers_mm — все точки-маркеры (их тоже не закрывать).
        prefer — функция(i) → предпочтительное направление (единичный вектор), по умолчанию — от центра масс кривых.
        Возвращает список (текст, центр_мм, конец_выноски_мм | None) и рисует их."""
        curves = np.vstack([o for o in obstacles if len(o)]) if obstacles else np.zeros((0, 2))
        marks = np.asarray(markers_mm, float).reshape(-1, 2)
        center = curves.mean(axis=0) if len(curves) else np.array([self.pw / 2, self.ph / 2])
        axes_lines = []
        X0, Y0 = self.to_mm(0 if not self.logx else self.logx["lo"], 0)
        if self.ax_y.lo < 0 < self.ax_y.hi:
            axes_lines.append(("h", float(Y0)))
        if not self.logx and self.ax_x.lo < 0 < self.ax_x.hi:
            axes_lines.append(("v", float(X0)))
        sizes = [self.text_size_mm(t, size) for t in texts]
        order = sorted(range(len(texts)), key=lambda i: -np.sum(np.hypot(*(np.asarray(pts_mm) - pts_mm[i]).T) < 12))
        result = [None] * len(texts)

        def free_rect(cx, cy, w, h):
            x0, x1, y0, y1 = cx - w / 2 - gap, cx + w / 2 + gap, cy - h / 2 - gap, cy + h / 2 + gap
            if x0 < 0.8 or y0 < 0.8 or x1 > self.pw - 0.8 or y1 > self.ph - 0.8:
                return False
            if len(curves) and np.any((curves[:, 0] > x0) & (curves[:, 0] < x1) & (curves[:, 1] > y0) & (curves[:, 1] < y1)):
                return False
            if len(marks):
                dx = np.clip(marks[:, 0], x0, x1) - marks[:, 0]
                dy = np.clip(marks[:, 1], y0, y1) - marks[:, 1]
                if np.any(np.hypot(dx, dy) < 1.4):
                    return False
            for kind, v in axes_lines:
                if kind == "h" and y0 < v < y1 or kind == "v" and x0 < v < x1:
                    return False
            for (a0, a1, b0, b1) in self.labels_placed:
                if not (x1 < a0 or x0 > a1 or y1 < b0 or y0 > b1):
                    return False
            return True

        def free_leader(p, q, own):
            L = math.hypot(*(q - p))
            if L < 0.2:
                return True
            n = max(2, int(L / 0.3))
            S = p + (q - p) * np.linspace(0, 1, n)[:, None]
            if len(curves):
                far = np.hypot(*(S - own).T) > 1.8
                d = np.min(np.hypot(S[far, None, 0] - curves[None, :, 0], S[far, None, 1] - curves[None, :, 1]), axis=1) \
                    if far.any() else np.array([9.0])
                if np.any(d < 0.45):
                    return False
            if len(marks):
                others = marks[np.hypot(*(marks - own).T) > 2.6]  # слипшиеся с этой точкой соседи выноске не мешают
                if len(others) and np.any(np.min(np.hypot(S[:, None, 0] - others[None, :, 0],
                                                           S[:, None, 1] - others[None, :, 1]), axis=0) < 1.3):
                    return False
            for (a0, a1, b0, b1) in self.labels_placed:
                if np.any((S[:, 0] > a0) & (S[:, 0] < a1) & (S[:, 1] > b0) & (S[:, 1] < b1)):
                    return False
            return True

        base_boxes = list(self.labels_placed)

        def cross(p1, p2, q1, q2):
            """Пересекаются ли отрезки p1p2 и q1q2 (строго)."""
            def orient(a, b, c):
                return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            d1, d2 = orient(q1, q2, p1), orient(q1, q2, p2)
            d3, d4 = orient(p1, p2, q1), orient(p1, p2, q2)
            return d1 * d2 < 0 and d3 * d4 < 0

        def seg_in_box(a, b, box):
            n = max(2, int(math.hypot(*(b - a)) / 0.3))
            S = a + (b - a) * np.linspace(0, 1, n)[:, None]
            x0, x1, y0, y1 = box
            return bool(np.any((S[:, 0] > x0) & (S[:, 0] < x1) & (S[:, 1] > y0) & (S[:, 1] < y1)))

        def attempt(order):
            """Разложить в заданном порядке; ничего не рисует. Возвращает [(центр, конец_выноски, остриё) | None]."""
            self.labels_placed = list(base_boxes)
            res = [None] * len(texts)
            leaders = []  # уже поставленные выноски: выноски не пересекаются и не проходят через чужие подписи
            for i in order:
                P = np.asarray(pts_mm[i], float)
                w, h = sizes[i]
                u0 = np.asarray(prefer(i), float) if prefer else P - center
                u0 = u0 / (np.linalg.norm(u0) or 1)
                base = math.atan2(u0[1], u0[0])
                best = None
                for r in (1.2, 2.2, 3.5, 5, 7, 9.5, 12.5, 16, 20, 25, 30, 36, max_r):
                    for da in (0, 15, -15, 30, -30, 45, -45, 60, -60, 75, -75, 90, -90, 110, -110, 130, -130,
                               155, -155, 180):
                        a = base + math.radians(da)
                        u = np.array([math.cos(a), math.sin(a)])
                        ext = abs(u[0]) * w / 2 + abs(u[1]) * h / 2
                        c = P + u * (r + ext)
                        if not free_rect(c[0], c[1], w, h):
                            continue
                        box = (c[0] - w / 2 - gap, c[0] + w / 2 + gap, c[1] - h / 2 - gap, c[1] + h / 2 + gap)
                        if any(seg_in_box(a0, a1, box) for a0, a1 in leaders):
                            continue
                        tip = P + u * 1.3
                        end = c - u * ext
                        if r > 2.3 and (not free_leader(tip, end, P) or any(cross(tip, end, a0, a1) for a0, a1 in leaders)):
                            continue
                        best = (c, end if r > 2.3 else None, tip)
                        break
                    if best:
                        break
                if best:
                    c = best[0]
                    self.labels_placed.append((c[0] - w / 2 - gap, c[0] + w / 2 + gap, c[1] - h / 2 - gap,
                                               c[1] + h / 2 + gap))
                    if best[1] is not None:
                        leaders.append((best[2], best[1]))
                    res[i] = best
            return res

        # Порядок важен: соседи могут занять места и перекрыть выноску. Пробуем несколько порядков (по тесноте,
        # слева направо, справа налево, сверху вниз), в каждом не поместившиеся — вперёд очереди; берём лучший.
        P_all = np.asarray(pts_mm, float)
        starts = [order,
                  sorted(range(len(texts)), key=lambda k: P_all[k, 0]),
                  sorted(range(len(texts)), key=lambda k: -P_all[k, 0]),
                  sorted(range(len(texts)), key=lambda k: -P_all[k, 1])]
        res = None
        for start in starts:
            cur_order = list(start)
            cur = attempt(cur_order)
            for _ in range(4):
                failed = [k for k in range(len(texts)) if cur[k] is None]
                if not failed:
                    break
                cur_order = failed + [k for k in cur_order if k not in failed]
                nxt = attempt(cur_order)
                if sum(r is None for r in nxt) < len(failed):
                    cur = nxt
            if res is None or sum(r is None for r in cur) < sum(r is None for r in res):
                res = cur
            if all(r is not None for r in res):
                break
        self.labels_placed = list(base_boxes)
        for i, b in enumerate(res):
            if b is None:
                continue
            c, end, tip = b
            w, h = sizes[i]
            self.labels_placed.append((c[0] - w / 2 - gap, c[0] + w / 2 + gap, c[1] - h / 2 - gap, c[1] + h / 2 + gap))
            xd, yd = self.from_mm(c[0], c[1])
            self.ax.text(xd, yd, texts[i], fontsize=size, color=color, ha="center", va="center", zorder=7,
                         bbox=dict(facecolor="white", edgecolor="none", pad=0.4, alpha=0.9))
            if end is not None:
                (x1, y1), (x2, y2) = self.from_mm(tip[0], tip[1]), self.from_mm(end[0], end[1])
                self.ax.plot([x1, x2], [y1, y2], color="black", lw=0.45, zorder=6)
            result[i] = (texts[i], c, end)
        return result

    def save(self, path, dpi=300):
        self.fig.savefig(path, dpi=dpi, metadata={"Software": None})
        plt.close(self.fig)
        return dict(path=str(path), width_mm=self.W, height_mm=self.H,
                    cell_x=None if self.logx else self.ax_x.cell, cell_y=self.ax_y.cell)
