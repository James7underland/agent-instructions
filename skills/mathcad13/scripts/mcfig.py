"""Post-processing of Mathcad plot images for the report.

Mathcad writes the trace expressions (e.g. "ImW", "0 ooo", "ReW, -1") to the left of and below the plot.  They are
cut away (the canvas around the plot stays white) and replaced by our own axis names and curve labels.

Label markup: base text is italic Times New Roman; `_{..}` subscript and `^{..}` superscript (upright),
`[..]` upright text in the base line (units, "Re", "Im").  Example: "h_{в.без}(t)", "t, [мин]".
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = r"C:\Windows\Fonts"
F_IT = os.path.join(FONTS, "timesi.ttf")
F_RM = os.path.join(FONTS, "times.ttf")
BLACK = (0, 0, 0)


def _font(path, size):
    return ImageFont.truetype(path, size)


def _segments(text):
    """-> [(kind, str)] kind: 'it' | 'rm' | 'sub' | 'sup'."""
    out, i, buf = [], 0, ""
    while i < len(text):
        c = text[i]
        if c in "_^" and i + 1 < len(text) and text[i + 1] == "{":
            j = text.index("}", i)
            if buf:
                out.append(("it", buf))
                buf = ""
            out.append(("sub" if c == "_" else "sup", text[i + 2:j]))
            i = j + 1
        elif c == "[":
            j = text.index("]", i)
            if buf:
                out.append(("it", buf))
                buf = ""
            out.append(("rm", text[i + 1:j]))
            i = j + 1
        else:
            buf += c
            i += 1
    if buf:
        out.append(("it", buf))
    return out


def text_size(text, size):
    w = 0
    for kind, s in _segments(text):
        f = _font(F_IT if kind == "it" else F_RM, size if kind in ("it", "rm") else int(size * 0.7))
        w += f.getlength(s)
    return int(round(w)), int(size * 1.25)


def draw_text(img, xy, text, size=20, color=BLACK, anchor="lb", bg=None):
    """Draw markup text; anchor: l/c/r + t/m/b of the base-line box (height = size)."""
    d = ImageDraw.Draw(img)
    w, _ = text_size(text, size)
    x, y = xy
    x -= {"l": 0, "c": w / 2, "r": w}[anchor[0]]
    base = y + {"t": size, "m": size / 2, "b": 0}[anchor[1]]  # y of the base line
    if bg:
        d.rectangle([x - 2, base - size - 1, x + w + 2, base + int(size * 0.35)], fill=bg)
    for kind, s in _segments(text):
        if kind in ("it", "rm"):
            f = _font(F_IT if kind == "it" else F_RM, size)
            d.text((x, base), s, font=f, fill=color, anchor="ls")
        else:
            f = _font(F_RM, int(size * 0.7))
            dy = size * 0.22 if kind == "sub" else -size * 0.42
            d.text((x, base + dy), s, font=f, fill=color, anchor="ls")
        x += f.getlength(s)
    return img


def plot_area(img, grid=(0, 255, 0)):
    """Plot area (L, T, R, B): bounding box of the grid lines and of the long black axis lines
    (crossed axes are drawn over the outer grid lines)."""
    a = np.asarray(img.convert("RGB")).astype(int)
    g = (abs(a[..., 0] - grid[0]) < 60) & (abs(a[..., 1] - grid[1]) < 60) & (abs(a[..., 2] - grid[2]) < 60)
    k = a.sum(axis=2) < 100
    ys, xs = np.nonzero(g)
    L, T, R, B = xs.min(), ys.min(), xs.max(), ys.max()
    span_w, span_h = R - L, B - T
    cols = np.nonzero(k.sum(axis=0) > 0.6 * span_h)[0]
    rows = np.nonzero(k.sum(axis=1) > 0.6 * span_w)[0]
    if len(cols):
        L, R = min(L, cols.min()), max(R, cols.max())
    if len(rows):
        T, B = min(T, rows.min()), max(B, rows.max())
    return int(L), int(T), int(R), int(B)


def clean(img, area, gap=10, skip=5):
    """White out everything outside the plot area except tick numbers.

    Tick numbers are dark text reachable from the area edge (row by row to the left, column by column downwards)
    without a blank gap of `gap` px; each such glyph group is kept whole (connected components after a small
    dilation).  Coloured horizontal runs outside the area (legend lines under Mathcad's trace names) are removed."""
    from scipy import ndimage
    a = np.asarray(img.convert("RGB")).copy()
    ai = a.astype(int)
    dark = ai.sum(axis=2) < 700
    colored = (ai.max(axis=2) - ai.min(axis=2)) > 80
    # legend lines under Mathcad's trace names: coloured horizontal runs (ClearType fringes of text are short)
    legend = ndimage.binary_opening(colored, structure=np.ones((1, 8), bool))
    ink = dark & ~legend
    H, W = ink.shape
    L, T, R, B = area
    inside = np.zeros_like(ink)
    inside[max(0, T - 3):B + 4, max(0, L - 3):R + 4] = True
    seed = np.zeros_like(ink)
    for y in range(H):                      # left side
        blank = 0
        for x in range(L - 1, -1, -1):
            if L - x <= skip:
                seed[y, x] = ink[y, x]
                continue
            if ink[y, x]:
                seed[y, x] = True
                blank = 0
            else:
                blank += 1
                if blank >= gap:
                    break
    for x in range(W):                      # below
        blank = 0
        for y in range(B + 1, H):
            if y - B <= skip:
                seed[y, x] = ink[y, x]
                continue
            if ink[y, x]:
                seed[y, x] = True
                blank = 0
            else:
                blank += 1
                if blank >= gap:
                    break
    near = np.zeros_like(ink)               # right and top: numbers sticking out of the area
    near[:, R + 1:min(W, R + 1 + gap)] = True
    near[max(0, T - gap):T, :] = True
    seed |= ink & near & ~inside
    lab, n = ndimage.label(ndimage.binary_dilation(ink & ~inside, iterations=2))
    keep_lab = np.unique(lab[seed & ~inside])
    keep = inside | (np.isin(lab, keep_lab[keep_lab > 0]) & ink)
    # Mathcad's trace names (and their legend line samples) are left-aligned at the region's left edge; tick
    # numbers never start there.  Drop glyph groups (small dilation) that begin within 10 px of the left edge.
    lab1, n1 = ndimage.label(ndimage.binary_dilation(ink & ~inside, iterations=1))
    for sl_i, sl in enumerate(ndimage.find_objects(lab1), 1):
        if sl is not None and sl[1].start < 10 and sl[1].stop < L - 2:
            keep[lab1 == sl_i] = False
    # whatever lies entirely to the left of the tick-number column is legend text as well
    out_left = ink & ~inside
    out_left[:, max(0, L - 2):] = False
    labh, nh = ndimage.label(ndimage.binary_dilation(out_left, structure=np.ones((3, 5), bool)))
    objs = [sl for sl in ndimage.find_objects(labh) if sl is not None]
    legend_rows = [(sl[0].start, sl[0].stop) for sl in objs if sl[1].start < 10]
    starts = [sl[1].start for sl in objs if sl[1].stop >= L - 14 and sl[1].start >= 10 and
              not any(sl[0].start < b and sl[0].stop > a for a, b in legend_rows)]
    if starts:
        x_num = min(starts)
        # pixel-wise: nothing to the left of the tick-number column survives
        keep[:, :max(0, x_num - 1)] = False
    keep |= inside
    a[~keep] = 255
    ys, xs = np.nonzero(keep & (dark | inside))
    return Image.fromarray(a), (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def _poly_px(P, xs, ys):
    return [P(x, y) for x, y in zip(xs, ys)]


def _cum(pts):
    d = [0.0]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d.append(d[-1] + math.hypot(x1 - x0, y1 - y0))
    return d


def _at(pts, dist, s):
    """Point and unit tangent at arc length s."""
    import bisect
    k = min(max(bisect.bisect_left(dist, s), 1), len(pts) - 1)
    (x0, y0), (x1, y1) = pts[k - 1], pts[k]
    seg = dist[k] - dist[k - 1] or 1e-9
    t = (s - dist[k - 1]) / seg
    L = math.hypot(x1 - x0, y1 - y0) or 1e-9
    return (x0 + t * (x1 - x0), y0 + t * (y1 - y0)), ((x1 - x0) / L, (y1 - y0) / L)


def triangle(d, tip, u, color, size=9, width=0.45):
    ux, uy = u
    bx, by = tip[0] - size * ux, tip[1] - size * uy
    nx, ny = -uy, ux
    d.polygon([tip, (bx + size * width * nx, by + size * width * ny), (bx - size * width * nx, by - size * width * ny)],
              fill=color)


def curve_marks(img, P, m, box):
    """m: dict(x=[..], y=[..], color, arrows=[fractions], hatch=dict(side='left', step=22, length=12, angle=45))."""
    d = ImageDraw.Draw(img)
    pts = [p for p in _poly_px(P, m["x"], m["y"]) if box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]]
    if len(pts) < 2:
        return
    dist = _cum(pts)
    col = m.get("color", BLACK)
    for fr in m.get("arrows", ()):
        tip, u = _at(pts, dist, fr * dist[-1])
        triangle(d, tip, u, col, m.get("arrow_size", 10))
    h = m.get("hatch")
    if h:
        step, ln, ang = h.get("step", 22), h.get("length", 12), math.radians(h.get("angle", 45))
        sgn = -1 if h.get("side", "left") == "left" else 1      # screen y grows downwards
        s = h.get("start", step / 2)
        while s < dist[-1] - 2:
            p, (ux, uy) = _at(pts, dist, s)
            # rotate tangent towards the chosen side by angle
            c, sn = math.cos(ang), math.sin(ang) * sgn
            vx, vy = ux * c - uy * sn, ux * sn + uy * c
            d.line([p, (p[0] + ln * vx, p[1] + ln * vy)], fill=h.get("color", col), width=h.get("width", 2))
            s += step


def finish(src, dst, xlim, ylim, xlabel=None, ylabel=None, labels=(), size=20, pad=6, scale=1.0, points=(), logx=False,
           marks=()):
    """Cut Mathcad trace names away and draw our own axis names and curve labels.

    xlim/ylim: axis limits used in the plot (to map data -> pixels).
    labels: [dict(text=, x=, y=, color=, anchor='lb', bg=None)] in data coordinates.
    """
    img = Image.open(src).convert("RGB")
    L, T, R, B = plot_area(img)
    img, (cl, ct, cr, cb) = clean(img, (L, T, R, B))
    crop = img.crop((cl - pad, ct - pad, cr + pad + 1, cb + pad + 1))
    ox, oy = cl - pad, ct - pad

    def fx(x):
        if logx:
            return (math.log10(x) - math.log10(xlim[0])) / (math.log10(xlim[1]) - math.log10(xlim[0]))
        return (x - xlim[0]) / (xlim[1] - xlim[0])

    def to_px(x, y):
        return (L - ox + fx(x) * (R - L),
                B - oy - (y - ylim[0]) / (ylim[1] - ylim[0]) * (B - T))

    ax_x = min(max(1.0 if logx else 0.0, xlim[0]), xlim[1])
    ax_y = min(max(0.0, ylim[0]), ylim[1])
    yl_w = text_size(ylabel, size)[0] if ylabel else 0
    xl_w = text_size(xlabel, size)[0] if xlabel else 0
    top_pad = int(size * 1.6) if ylabel else 0
    right_pad = xl_w + 12 if xlabel else 0
    Y_axis_px, _ = to_px(ax_x, ax_y)
    left_pad = max(0, int(yl_w / 2 - Y_axis_px) + 4) if ylabel else 0
    W = crop.size[0] + left_pad + right_pad
    H = crop.size[1] + top_pad
    out = Image.new("RGB", (W, H), "white")
    out.paste(crop, (left_pad, top_pad))
    dx, dy = left_pad, top_pad

    def P(x, y):
        a, b = to_px(x, y)
        return a + dx, b + dy

    if ylabel:
        ax, _ = P(ax_x, ylim[1])
        draw_text(out, (ax + 6, dy + T - oy - 4), ylabel, size, anchor="lb")
    if xlabel:
        _, ay = P(xlim[1], ax_y)
        draw_text(out, (dx + R - ox + 8, ay - 4), xlabel, size, anchor="lb")
    box = (dx + L - ox, dy + T - oy, dx + R - ox, dy + B - oy)
    for m in marks:
        curve_marks(out, P, m, box)
    dr = ImageDraw.Draw(out)
    for pt in points:
        x, y = P(pt["x"], pt["y"])
        r = pt.get("r", 5)
        dr.ellipse([x - r, y - r, x + r, y + r], fill=pt.get("color", BLACK))
    for lb in labels:
        x, y = P(lb["x"], lb["y"])
        draw_text(out, (x, y), lb["text"], lb.get("size", size), color=lb.get("color", BLACK),
                  anchor=lb.get("anchor", "lb"), bg=lb.get("bg"))
    if scale != 1.0:
        out = out.resize((int(W * scale), int(H * scale)), Image.LANCZOS)
    out.save(dst)
    return dst
