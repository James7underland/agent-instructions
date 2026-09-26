# -*- coding: utf-8 -*-
"""Компоновка ФСА (ГОСТ 21.208-2013 / 21.408-2013): координаты, проверка пересечений, превью, layout.json.

Эталон — установка ректификации (7 контуров). Для новой схемы скопировать файл в рабочую папку,
переписать разделы PROCESS (оборудование, трубы, контуры) и ПОДВАЛ (LOOPS), запустить:
    python layout.py [папка_вывода]      -> layout.json + preview.png, в консоли NO COLLISIONS или список ошибок.
Координаты в мм от левого нижнего угла листа A3 (420x297). Рамка x 20..415, y 5..292, штамп x 230..415, y 5..60.
"""
import json, math, sys, os

HERE = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
sym = {}        # id -> symbol
pipes, signals, labels, dots, arrows, plines = [], [], [], [], [], []

# ------------------------------------------------------------------ symbols
def inst(i, kind, x, y, letters, pos, loop, param='', device='', note='', layer='Приборы', podval=False, npos='u'):
    sym[i] = dict(id=i, t=kind, x=x, y=y, letters=letters, pos=pos, loop=loop, param=param,
                  device=device, note=note, layer=layer, podval=podval, npos=npos)

def valve(i, x, y, pos, loop, act='up', fail='', pos_side='auto'):
    sym[i] = dict(id=i, t='valve', x=x, y=y, pos=pos, loop=loop, act=act, fail=fail, pos_side=pos_side)

def equip(i, kind, x, y, pos, w=None, h=None, flipx=False, txt=None):
    sym[i] = dict(id=i, t=kind, x=x, y=y, pos=pos, w=w, h=h, flipx=flipx, txt=txt)

def num(i, x, y, n, podval=False):
    sym[i] = dict(id=i, t='num', x=x, y=y, n=n, podval=podval)

def pipe(pts, arrow=True, lw=0.35, kind='pipe'):
    pipes.append(dict(pts=pts, arrow=arrow, lw=lw, kind=kind))

def label(x, y, text, size=3.5, align='l', angle=0, layer='Надписи'):
    labels.append(dict(x=x, y=y, text=text, size=size, align=align, angle=angle, layer=layer))

ACT_ANGLE = {'up': 0, 'left': 90, 'down': 180, 'right': 270}

def rot(a, b, th):
    t = math.radians(th)
    return (a * math.cos(t) - b * math.sin(t), a * math.sin(t) + b * math.cos(t))

def cnx(i, k):
    """Координаты точки соединения k фигуры i (как в мастерах трафарета)."""
    s = sym[i]; x, y = s['x'], s['y']; t = s['t']
    if t in ('field', 'panel'):
        return [(x, y + 5), (x, y - 5), (x - 5, y), (x + 5, y), (x - 4.33, y + 2.5), (x + 4.33, y + 2.5),
                (x - 4.33, y - 2.5), (x + 4.33, y - 2.5)][k]
    if t == 'ctrl':
        return [(x, y + 5), (x, y - 5), (x - 9, y), (x + 9, y), (x - 9, y + 2.5), (x + 9, y + 2.5),
                (x - 9, y - 2.5), (x + 9, y - 2.5)][k]
    if t == 'num':
        return [(x, y + 2), (x, y - 2), (x - 3, y), (x + 3, y)][k]
    if t == 'valve':
        loc = [(-3.5, 0), (3.5, 0), (0, -1.75), (0, 10), (-2.5, 7.5), (2.5, 7.5)][k]
        dx, dy = rot(loc[0], loc[1], ACT_ANGLE[s['act']])
        return (x + dx, y + dy)
    raise ValueError(t)

def vcnx(i, name):
    """Точка клапана по смыслу: 'body' (сторона без ИМ), 'far', 'act_l', 'act_r', 'act_u', 'act_d'."""
    if name == 'body': return 2
    if name == 'far': return 3
    p4, p5 = cnx(i, 4), cnx(i, 5)
    if name == 'act_l': return 4 if p4[0] < p5[0] else 5
    if name == 'act_r': return 5 if p4[0] < p5[0] else 4
    if name == 'act_u': return 4 if p4[1] > p5[1] else 5
    if name == 'act_d': return 5 if p4[1] > p5[1] else 4
    raise ValueError(name)

def sig(a, ai, b, bi, route='S', kind='el', via=None, mid=None):
    """Линия связи между точками соединения. kind: el (электрич., штрих), imp (импульсная/пневм., сплошная)."""
    p1, p2 = cnx(a, ai), cnx(b, bi)
    if via is not None: pts = [p1] + via + [p2]
    elif route == 'S': pts = [p1, p2]
    elif route == 'VH': pts = [p1, (p1[0], p2[1]), p2]
    elif route == 'HV': pts = [p1, (p2[0], p1[1]), p2]
    elif route == 'VHV': pts = [p1, (p1[0], mid), (p2[0], mid), p2]
    elif route == 'HVH': pts = [p1, (mid, p1[1]), (mid, p2[1]), p2]
    signals.append(dict(a=a, ai=ai, b=b, bi=bi, pts=[list(map(lambda v: round(v, 3), p)) for p in pts], kind=kind))

# ------------------------------------------------------------------ bboxes for checks
def shapes_geom():
    g = []  # (id, kind, geom) geom: ('c', x, y, r) or ('r', x1, y1, x2, y2)
    for s in sym.values():
        t, x, y = s['t'], s['x'], s['y']
        if t in ('field', 'panel'): g.append((s['id'], 'inst', ('c', x, y, 5)))
        elif t == 'ctrl': g.append((s['id'], 'inst', ('r', x - 9, y - 5, x + 9, y + 5)))
        elif t == 'num': g.append((s['id'], 'num', ('r', x - 1.8, y - 1.6, x + 1.8, y + 1.6)))
        elif t == 'valve':
            ax, ay = rot(0, 7.5, ACT_ANGLE[s['act']])
            g.append((s['id'], 'act', ('c', x + ax, y + ay, 2.5)))
            if ACT_ANGLE[s['act']] in (0, 180): g.append((s['id'], 'vbody', ('r', x - 3.5, y - 1.75, x + 3.5, y + 1.75)))
            else: g.append((s['id'], 'vbody', ('r', x - 1.75, y - 3.5, x + 1.75, y + 3.5)))
        elif t in ('pump',): g.append((s['id'], 'equip', ('c', x, y, 6)))
        elif t == 'hex': g.append((s['id'], 'equip', ('c', x, y, 8)))
        elif t in ('column', 'drum', 'reb'):
            w, h = s['w'], s['h']; g.append((s['id'], 'equip', ('r', x - w / 2, y - h / 2, x + w / 2, y + h / 2)))
    return g

def text_box(l):
    w = len(l['text']) * l['size'] * 0.56 + 0.4; h = l['size'] * 0.8
    x, y = l['x'], l['y']
    if l['angle'] in (90, -90):
        w, h = h, w
        return ('r', x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    x1 = {'l': x, 'c': x - w / 2, 'r': x - w}[l['align']]
    return ('r', x1, y - h / 2, x1 + w, y + h / 2)

def seg_hits(p, q, geom, tol):
    (x1, y1), (x2, y2) = p, q
    if geom[0] == 'c':
        _, cx, cy, r = geom
        dx, dy = x2 - x1, y2 - y1; L2 = dx * dx + dy * dy
        tt = 0 if L2 == 0 else max(0, min(1, ((cx - x1) * dx + (cy - y1) * dy) / L2))
        px, py = x1 + tt * dx, y1 + tt * dy
        return math.hypot(px - cx, py - cy) < r - tol
    _, a1, b1, a2, b2 = geom
    a1 += tol; b1 += tol; a2 -= tol; b2 -= tol
    if a1 >= a2 or b1 >= b2: return False
    # Liang-Barsky
    dx, dy = x2 - x1, y2 - y1; u0, u1 = 0.0, 1.0
    for pp, qq in ((-dx, x1 - a1), (dx, a2 - x1), (-dy, y1 - b1), (dy, b2 - y1)):
        if pp == 0:
            if qq < 0: return False
        else:
            r = qq / pp
            if pp < 0: u0 = max(u0, r)
            else: u1 = min(u1, r)
            if u0 > u1: return False
    return True

def box_of(geom):
    if geom[0] == 'c': return (geom[1] - geom[3], geom[2] - geom[3], geom[1] + geom[3], geom[2] + geom[3])
    return geom[1:]

def boxes_overlap(a, b, gap):
    return not (a[2] + gap <= b[0] or b[2] + gap <= a[0] or a[3] + gap <= b[1] or b[3] + gap <= a[1])

def check():
    errs = []
    G = shapes_geom()
    # символы между собой
    for i in range(len(G)):
        for j in range(i + 1, len(G)):
            (ia, ka, ga), (ib, kb, gb) = G[i], G[j]
            if ia == ib: continue
            if 'equip' in (ka, kb) and ('vbody' in (ka, kb) or 'inst' in (ka, kb)):
                gap = -0.1
            else:
                gap = 1.0
            if ka == 'num' or kb == 'num': gap = 0.8
            if boxes_overlap(box_of(ga), box_of(gb), gap):
                if ga[0] == 'c' and gb[0] == 'c' and math.hypot(ga[1] - gb[1], ga[2] - gb[2]) >= ga[3] + gb[3] + gap: continue
                errs.append(f'overlap {ia}/{ka} ~ {ib}/{kb}')
    # линии связи через символы
    for s in signals:
        for p, q in zip(s['pts'], s['pts'][1:]):
            for (i, k, g) in G:
                if i in (s['a'], s['b']) and k != 'act' : continue
                if i in (s['a'], s['b']) and k == 'act' and sym[i]['t'] == 'valve': continue
                if k == 'equip': continue
                if seg_hits(p, q, g, 0.3): errs.append(f'signal {s["a"]}->{s["b"]} crosses {i}/{k}')
    for pl in pipes:
        for p, q in zip(pl['pts'], pl['pts'][1:]):
            for (i, k, g) in G:
                if k in ('equip', 'vbody'): continue
                if k == 'inst' and sym[i].get('inline'): continue
                if seg_hits(p, q, g, 0.3): errs.append(f'pipe {pl["pts"][0]} crosses {i}/{k}')
    # надписи
    LB = list(labels)
    for s in sym.values():
        if s['t'] == 'valve':
            ax, ay = rot(0, 7.5, ACT_ANGLE[s['act']])
            if ACT_ANGLE[s['act']] in (90, 270): LB.append(dict(x=s['x'] + ax - 3, y=s['y'] + ay - 4.8, text=s['pos'], size=3.5, align='l', angle=0))
            elif s['pos_side'] == 'l': LB.append(dict(x=s['x'] + ax - 3.2, y=s['y'] + ay, text=s['pos'], size=3.5, align='r', angle=0))
            else: LB.append(dict(x=s['x'] + ax + 3.2, y=s['y'] + ay, text=s['pos'], size=3.5, align='l', angle=0))
    for s in sym.values():
        if s.get('note'):
            hw = 9 if s['t'] == 'ctrl' else 5
            LB.append(dict(x=s['x'] + hw + 0.8, y=s['y'] + (3 if s['npos'] == 'u' else -3), text=s['note'], size=2.5, align='l', angle=0, layer='note'))
    L = [(n, text_box(l)) for n, l in enumerate(LB)]
    for n, tb in L:
        for (i, k, g) in G:
            if boxes_overlap(tb[1:], box_of(g), 0.4) and not (g[0] == 'c' and not seg_hits((tb[1], (tb[2] + tb[4]) / 2), (tb[3], (tb[2] + tb[4]) / 2), g, -0.4) and not seg_hits((tb[1], tb[2]), (tb[3], tb[2]), g, -0.4) and not seg_hits((tb[1], tb[4]), (tb[3], tb[4]), g, -0.4)):
                errs.append(f'label "{LB[n]["text"]}" overlaps {i}/{k}')
        for s in signals + pipes:
            for p, q in zip(s['pts'], s['pts'][1:]):
                if seg_hits(p, q, tb, 0.0): errs.append(f'label "{LB[n]["text"]}" crossed by line from {s["pts"][0]}')
        for m, tb2 in L:
            if m > n and boxes_overlap(tb[1:], tb2[1:], 0.4): errs.append(f'label "{LB[n]["text"]}" ~ "{LB[m]["text"]}"')
    # в пределах поля
    for (i, k, g) in G:
        b = box_of(g)
        if b[0] < 21 or b[2] > 414 or b[3] > 291 or (b[0] > 229 and b[1] < 61): errs.append(f'{i} outside field')
    # пересечения линий связи между собой и с трубопроводами
    def seg_x(p1, p2, p3, p4):
        def cr(a, b, c): return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        d1, d2, d3, d4 = cr(p3, p4, p1), cr(p3, p4, p2), cr(p1, p2, p3), cr(p1, p2, p4)
        return ((d1 > 1e-6 and d2 < -1e-6) or (d1 < -1e-6 and d2 > 1e-6)) and ((d3 > 1e-6 and d4 < -1e-6) or (d3 < -1e-6 and d4 > 1e-6))
    SG = [s for s in signals if s['kind'] != 'pod']
    for i, s1 in enumerate(SG):
        for s2 in SG[i + 1:] + [dict(pts=p['pts'], a='pipe', b='pipe') for p in pipes]:
            for p, q in zip(s1['pts'], s1['pts'][1:]):
                for r, t in zip(s2['pts'], s2['pts'][1:]):
                    if seg_x(p, q, r, t): errs.append(f'crossing {s1["a"]}->{s1["b"]} x {s2["a"]}->{s2["b"]} near {p}')
    return errs

# ================================================================== PROCESS
# xE - по месту (круг без черты); xT, xY и регуляторы - на щите (с чертой). ИМ электрические.
# --- контур 1: расход сырья (FIRCA) --------------------------------------
pipe([(25, 148), (64, 148)])                                   # сырьё -> Н-1
pipe([(76, 154), (82, 154), (82, 168), (120, 168)])            # Н-1 -> Т-2
equip('N1', 'pump', 70, 148, 'Н-1')
equip('T2', 'hex', 128, 168, 'Т-2', txt=(-9, 10))
valve('V1', 50, 148, '1-5', 1, 'up')
inst('FE1', 'field', 97, 168, 'FE', '1-1', 1, 'Расход сырья СН', 'Сужающее устройство'); sym['FE1']['inline'] = True
inst('FT1', 'panel', 97, 186, 'FT', '1-2', 1, 'Расход сырья СН', 'Преобразователь расхода')
inst('FC1', 'ctrl', 72, 195, 'FIRCA', '1-3', 1, 'Расход сырья СН', 'Регулятор расхода (функция ПЛК)', note='L', npos='d')
inst('FY1', 'panel', 50, 168, 'FY', '1-4', 1, 'Расход сырья СН', 'Блок управления ИМ')
sig('FE1', 0, 'FT1', 1)
sig('FT1', 0, 'FC1', 5, 'VH')
sig('FC1', 4, 'FY1', 0, 'HV')
sig('FY1', 1, 'V1', 3)
num('b1', 97, 155.5, 1);  sig('FE1', 1, 'b1', 0)
num('b2', 50, 137.5, 2);  sig('V1', 2, 'b2', 0)
label(25, 151.3, 'Сырьё (СН)')

# --- контур 2: температура сырья после Т-2 (TIRC) -------------------------
pipe([(136, 168), (170, 168)])                                 # Т-2 -> К-3
pipe([(88, 208), (140, 208), (140, 183.2), (131.826, 175.026)])  # теплоноситель (вход в «молнию»)
pipe([(124.174, 160.974), (116, 152.8)])                        # теплоноситель выход
valve('V2', 112, 208, '2-4', 2, 'up')
inst('TE2', 'field', 152, 179, 'TE', '2-1', 2, 'Температура сырья после Т-2', 'Термопреобразователь')
inst('TC2', 'ctrl', 134, 228, 'TIRC', '2-2', 2, 'Температура сырья после Т-2', 'Регулятор температуры (функция ПЛК)')
inst('TY2', 'panel', 112, 228, 'TY', '2-3', 2, 'Температура сырья после Т-2', 'Блок управления ИМ')
plines.append(dict(pts=[(152, 174), (152, 168)])); dots.append((152, 168))
sig('TE2', 0, 'TC2', 5, 'VH')
sig('TC2', 4, 'TY2', 5, 'S')
sig('TY2', 1, 'V2', 3)
num('b3', 165, 179, 3);   sig('TE2', 3, 'b3', 2)
num('b4', 112, 197.5, 4); sig('V2', 2, 'b4', 0)
label(87, 208, 'Теплоноситель', align='r')

# --- колонна, куб, испаритель -------------------------------------------
equip('K3', 'column', 180, 187, 'К-3', 20, 98)                  # y 138..236
equip('I7', 'reb', 212, 146, 'И-7', 26, 12, txt=(0, -9.5))
pipe([(190, 146), (199, 146)])
pipe([(205, 152), (205, 160), (190, 160)])
pipe([(220, 168), (220, 152)])
label(223, 167.5, 'Пар')
pipe([(225, 146), (272, 146)])
label(274, 146, 'Кубовый продукт')

# --- контур 4: уровень в кубе К-3 (LIRCA) --------------------------------
valve('V4', 245, 146, '4-5', 4, 'up')
inst('LE4', 'field', 200, 172, 'LE', '4-1', 4, 'Уровень в кубе К-3', 'Чувствительный элемент уровнемера')
inst('LT4', 'panel', 200, 190, 'LT', '4-2', 4, 'Уровень в кубе К-3', 'Преобразователь уровня')
inst('LC4', 'ctrl', 224, 185, 'LIRCA', '4-3', 4, 'Уровень в кубе К-3', 'Регулятор уровня (функция ПЛК)', note='H, L', npos='d')
inst('LY4', 'panel', 245, 166, 'LY', '4-4', 4, 'Уровень в кубе К-3', 'Блок управления ИМ')
plines.append(dict(pts=[(195, 172), (190, 172)])); dots.append((190, 172))
sig('LE4', 0, 'LT4', 1)
sig('LT4', 7, 'LC4', 4)
sig('LC4', 5, 'LY4', 0, 'HV')
sig('LY4', 1, 'V4', 3)
num('b7', 213, 172, 7);   sig('LE4', 3, 'b7', 2)
num('b8', 245, 135.5, 8); sig('V4', 2, 'b8', 0)

# --- верх колонны: пары на КХ-4 ------------------------------------------
pipe([(180, 236), (180, 248), (216, 248)])
equip('KX4', 'hex', 224, 248, 'КХ-4', txt=(-10, 9))
pipe([(194, 240), (219.2, 240), (220.174, 240.974)])          # хладагент вход
label(194, 242.8, 'Хладагент', size=3.2)
pipe([(227.826, 255.026), (232, 259.2), (232, 266), (256, 266)]) # хладагент выход
label(251, 263.2, 'Хладагент', size=3.2)
pipe([(232, 248), (299.5, 248)])                               # КХ-4 -> Е-5
equip('E5', 'drum', 322, 248, 'Е-5', 45, 16)                    # 299.5..344.5 x 240..256

# --- контур 6: температура после КХ-4 (TIRC) -----------------------------
valve('V6', 244, 266, '6-4', 6, 'up', pos_side='l')
inst('TE6', 'field', 280, 261, 'TE', '6-1', 6, 'Температура после КХ-4', 'Термопреобразователь')
inst('TC6', 'ctrl', 280, 273.5, 'TIRC', '6-2', 6, 'Температура после КХ-4', 'Регулятор температуры (функция ПЛК)')
inst('TY6', 'panel', 257, 273.5, 'TY', '6-3', 6, 'Температура после КХ-4', 'Блок управления ИМ')
plines.append(dict(pts=[(280, 256), (280, 248)])); dots.append((280, 248))
sig('TE6', 0, 'TC6', 1, 'S')
sig('TC6', 4, 'TY6', 5, 'S')
sig('TY6', 2, 'V6', vcnx('V6', 'act_r'))
num('b11', 293, 261, 11); sig('TE6', 3, 'b11', 2)
num('b12', 244, 255.5, 12); sig('V6', 2, 'b12', 0)

# --- контур 3: давление верха К-3 (PIRCAS) --------------------------------
inst('PE3', 'field', 165, 244, 'PE', '3-1', 3, 'Давление верха колонны К-3', 'Чувствительный элемент (отбор давления)')
inst('PT3', 'panel', 165, 262, 'PT', '3-2', 3, 'Давление верха колонны К-3', 'Преобразователь давления')
plines.append(dict(pts=[(170, 244), (180, 244)])); dots.append((180, 244))
pipe([(337, 256), (337, 266), (370, 266)])                     # газ
label(372, 266, 'Газ')
valve('V3', 352, 266, '3-5', 3, 'up')
inst('PC3', 'ctrl', 315, 273.5, 'PIRCAS', '3-3', 3, 'Давление верха колонны К-3', 'Регулятор давления (функция ПЛК)', note='H', npos='d')
inst('PY3', 'panel', 336, 273.5, 'PY', '3-4', 3, 'Давление верха колонны К-3', 'Блок управления ИМ')
sig('PE3', 0, 'PT3', 1)
sig('PT3', 0, 'PC3', 0, via=[(165, 288), (315, 288)])
sig('PC3', 5, 'PY3', 4, 'S')
sig('PY3', 3, 'V3', vcnx('V3', 'act_l'))
num('b5', 151, 244, 5);   sig('PE3', 2, 'b5', 3)
num('b6', 352, 255.5, 6); sig('V3', 2, 'b6', 0)

# --- Н-6, орошение (контур 5) ---------------------------------------------
pipe([(308, 240), (308, 214), (300, 214)])                     # Е-5 -> всас Н-6
equip('N6', 'pump', 294, 214, 'Н-6', flipx=True)                # 288..300 x 208..220
pipe([(288, 220), (280, 220), (280, 228), (190, 228)])         # нагнетание Н-6 -> орошение К-3
valve('V5', 214, 228, '5-5', 5, 'down')
inst('FE5', 'field', 252, 228, 'FE', '5-1', 5, 'Расход орошения в К-3', 'Сужающее устройство'); sym['FE5']['inline'] = True
inst('FT5', 'panel', 252, 210.5, 'FT', '5-2', 5, 'Расход орошения в К-3', 'Преобразователь расхода')
inst('FC5', 'ctrl', 233, 208, 'FIRC', '5-3', 5, 'Расход орошения в К-3', 'Регулятор расхода (функция ПЛК)')
inst('FY5', 'panel', 214, 208, 'FY', '5-4', 5, 'Расход орошения в К-3', 'Блок управления ИМ')
sig('FE5', 1, 'FT5', 0)
sig('FT5', 2, 'FC5', 5, 'S')
sig('FC5', 6, 'FY5', 7, 'S')
sig('FY5', 0, 'V5', 3)
num('b9', 252, 240.5, 9);   sig('FE5', 0, 'b9', 1)
num('b10', 214, 235.5, 10); sig('V5', 2, 'b10', 1)

# --- дистиллят (контур 7): расход на всасе Н-6, клапан на выходе Е-5 -----
pipe([(340, 240), (340, 206), (390, 206)])                     # Е-5 -> дистиллят
label(392, 206, 'Дистиллят', size=3.2)
valve('V7', 376, 206, '7-5', 7, 'down')
inst('FE7', 'field', 308, 228, 'FE', '7-1', 7, 'Расход дистиллята', 'Сужающее устройство'); sym['FE7']['inline'] = True
inst('FT7', 'panel', 324, 228, 'FT', '7-2', 7, 'Расход дистиллята', 'Преобразователь расхода')
inst('FC7', 'ctrl', 354, 186, 'FIRC', '7-3', 7, 'Расход дистиллята', 'Регулятор расхода (функция ПЛК)')
inst('FY7', 'panel', 376, 186, 'FY', '7-4', 7, 'Расход дистиллята', 'Блок управления ИМ')
sig('FE7', 3, 'FT7', 2)
sig('FT7', 1, 'FC7', 4, 'VH')
sig('FC7', 5, 'FY7', 4, 'S')
sig('FY7', 0, 'V7', 3)
num('b13', 295, 228, 13);  sig('FE7', 2, 'b13', 3)
num('b14', 376, 216.5, 14); sig('V7', 2, 'b14', 1)
# ================================================================== ПОДВАЛ
PX0, PX1, XG, XF = 25, 410, 36, 70
ROWS = [  # key, title, y1, y2, group
    ('field', 'Приборы по месту', 110, 124, None),
    ('panel', 'Приборы на щите', 104, 110, None),
    ('R', 'Регистрация', 98, 104, 'ПЛК'), ('C', 'Стабилизация', 92, 98, 'ПЛК'),
    ('A', 'Сигнализация', 86, 92, 'ПЛК'), ('S', 'Блокировка', 80, 86, 'ПЛК'),
    ('I', 'Индикация', 74, 80, 'АРМ'), ('A2', 'Сигнализация', 68, 74, 'АРМ'), ('DU', 'Дист. управление', 62, 68, 'АРМ')]
RY = {k: (y1 + y2) / 2 for k, _, y1, y2, _ in ROWS}
LOOPS = [  # loop, sensor id, функции, пределы
    (1, 'FE1', 'R C A I A2 DU', '…м³/ч'), (2, 'TE2', 'R C I DU', '…°С'), (3, 'PE3', 'R C A S I A2 DU', '…МПа'),
    (4, 'LE4', 'R C A I A2 DU', '…мм'), (5, 'FE5', 'R C I DU', '…м³/ч'), (6, 'TE6', 'R C I DU', '…°С'),
    (7, 'FE7', 'R C I DU', '…м³/ч')]
podval = dict(x0=PX0, x1=PX1, xg=XG, xf=XF, rows=[dict(key=k, title=t, y1=a, y2=b, group=g) for k, t, a, b, g in ROWS],
              cols=[], lines=[], dots=[], arrows=[], texts=[])
for (lp, sid, funcs, rng) in LOOPS:
    mx = 82 + (lp - 1) * 47; cx = mx + 23
    s = sym[sid]
    inst(f'pv{lp}', 'field', mx, 117, s['letters'], s['pos'], lp, s['param'], s['device'], podval=True)
    num(f'pb{2*lp-1}', mx, 127.5, 2 * lp - 1, podval=True)
    num(f'pb{2*lp}', cx, 127.5, 2 * lp, podval=True)
    sig(f'pb{2*lp-1}', 1, f'pv{lp}', 0, 'S', 'pod')
    podval['lines'].append(dict(pts=[[mx, 112], [mx, 62]]))
    podval['lines'].append(dict(pts=[[cx, 125.5], [cx, RY['DU']]]))
    for f in funcs.split():
        podval['dots'].append([mx if f != 'DU' else cx, RY[f]])
    podval['arrows'].append(dict(pts=[[mx, RY['C']], [cx, RY['C']]]))
    podval['texts'].append(dict(x=mx + 6.2, y=119.5, text=rng, size=2.5, align='l'))
    podval['cols'].append(dict(loop=lp, mx=mx, cx=cx))

# ================================================================== OUTPUT
if __name__ == '__main__':
    errs = check()
    print('\n'.join(errs) if errs else 'NO COLLISIONS')
    data = dict(symbols=list(sym.values()), pipes=pipes, signals=signals, labels=labels, dots=dots,
                plines=plines, podval=podval)
    json.dump(data, open(os.path.join(HERE, 'layout.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    # preview
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Rectangle, Polygon
    fig, ax = plt.subplots(figsize=(420 / 25.4 * 1.6, 297 / 25.4 * 1.6), dpi=110)
    ax.set_xlim(0, 420); ax.set_ylim(0, 297); ax.set_aspect('equal'); ax.axis('off')
    ax.add_patch(Rectangle((20, 5), 395, 287, fill=False, lw=1))
    ax.add_patch(Rectangle((230, 5), 185, 55, fill=False, lw=1))
    ax.add_patch(Rectangle((20, 278), 70, 14, fill=False, lw=0.6))
    for p in pipes:
        xs, ys = zip(*p['pts']); ax.plot(xs, ys, 'k-', lw=1.0)
        if p['arrow']:
            (x1, y1), (x2, y2) = p['pts'][-2], p['pts'][-1]
            ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='-|>', lw=0.8, color='k'))
    for p in plines:
        xs, ys = zip(*p['pts']); ax.plot(xs, ys, 'k-', lw=0.5)
    for s in signals:
        xs, ys = zip(*s['pts']); ax.plot(xs, ys, 'k' + ('--' if s['kind'] == 'el' else '-'), lw=0.5)
    for s in sym.values():
        t, x, y = s['t'], s['x'], s['y']
        if t in ('field', 'panel'):
            ax.add_patch(Circle((x, y), 5, fill=True, fc='w', ec='k', lw=1.2, zorder=3))
            ax.text(x, y + 1.8, s['letters'], ha='center', va='center', fontsize=5, zorder=4)
            ax.text(x, y - 2.2, s['pos'], ha='center', va='center', fontsize=5, zorder=4)
            if s['note']: ax.text(x + 6, y + 2, s['note'], fontsize=4, zorder=4)
        elif t == 'ctrl':
            ax.add_patch(Rectangle((x - 9, y - 5), 18, 10, fc='w', ec='k', lw=1.2, zorder=3)); ax.plot([x - 9, x + 9], [y, y], 'k-', lw=0.5, zorder=4)
            ax.text(x, y + 2.3, s['letters'], ha='center', va='center', fontsize=5, zorder=4)
            ax.text(x, y - 2.4, s['pos'], ha='center', va='center', fontsize=5, zorder=4)
            if s['note']: ax.text(x + 10, y - 4.5, s['note'], fontsize=4, zorder=4)
        elif t == 'num': ax.text(x, y, str(s['n']), ha='center', va='center', fontsize=5)
        elif t == 'valve':
            th = ACT_ANGLE[s['act']]
            pts = [rot(a, b, th) for a, b in [(-3.5, -1.75), (3.5, 1.75), (3.5, -1.75), (-3.5, 1.75)]]
            ax.add_patch(Polygon([(x + a, y + b) for a, b in pts], closed=True, fc='w', ec='k', lw=0.8, zorder=3))
            sx, sy = rot(0, 10, th); ax.plot([x, x + sx], [y, y + sy], 'k-', lw=0.8, zorder=3)
            cx_, cy_ = rot(0, 12.5, th); ax.add_patch(Circle((x + cx_, y + cy_), 2.5, fc='w', ec='k', lw=1, zorder=3))
            ax.text(x + cx_ + 3.2, y + cy_, s['pos'], fontsize=4.5, va='center', zorder=4)
        elif t == 'pump': ax.add_patch(Circle((x, y), 6, fc='w', ec='k', lw=0.8, zorder=2)); ax.text(x, y, s['pos'], ha='center', va='center', fontsize=5)
        elif t == 'hex': ax.add_patch(Circle((x, y), 8, fc='w', ec='k', lw=0.8, zorder=2)); ax.text(x - 9, y + 10, s['pos'], ha='center', fontsize=5)
        elif t in ('column', 'drum', 'reb'):
            ax.add_patch(Rectangle((x - s['w'] / 2, y - s['h'] / 2), s['w'], s['h'], fc='w', ec='k', lw=0.8, zorder=2)); ax.text(x, y, s['pos'], ha='center', va='center', fontsize=5)
    for l in labels:
        ax.text(l['x'], l['y'], l['text'], ha={'l': 'left', 'c': 'center', 'r': 'right'}[l['align']], va='center', fontsize=l['size'] * 1.35, rotation=l['angle'])
    for d in dots: ax.add_patch(Circle(d, 0.7, color='k', zorder=5))
    # podval
    pv = podval
    ax.add_patch(Rectangle((PX0, 62), PX1 - PX0, 62, fill=False, lw=1))
    for r in pv['rows']:
        ax.plot([PX0, PX1], [r['y1'], r['y1']], 'k-', lw=0.4)
        ax.text(XG + 1.5 if r['group'] else PX0 + 1.5, (r['y1'] + r['y2']) / 2, r['title'], fontsize=4.5, va='center')
    ax.plot([XF, XF], [62, 124], 'k-', lw=0.8); ax.plot([XG, XG], [62, 104], 'k-', lw=0.8)
    for l in pv['lines']:
        xs, ys = zip(*l['pts']); ax.plot(xs, ys, 'k-', lw=0.5)
    for d in pv['dots']: ax.add_patch(Circle(d, 0.8, color='k', zorder=5))
    for a in pv['arrows']:
        ax.annotate('', xy=a['pts'][1], xytext=a['pts'][0], arrowprops=dict(arrowstyle='-|>', lw=0.6, color='k'))
    for t in pv['texts']: ax.text(t['x'], t['y'], t['text'], fontsize=3.5)
    fig.savefig(os.path.join(HERE, 'preview.png'), bbox_inches='tight')
    print('preview saved')
