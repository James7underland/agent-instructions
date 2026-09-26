"""Чтение/запись файлов вариантов ТАУ-3 (*.VRT, cp1251). Три семейства форматов — см. references/vrt-format.md.

python vrt.py show FILE.VRT                      # разбор в читаемом виде (формат определяется автоматически)
python vrt.py roundtrip FILE.VRT                 # проверка: разбор -> запись даёт тот же текст
python vrt.py poly OUT.VRT --den "3.6 2 1" --num "1.8" [--den "1" --num "1" ...] [--tail FILE|--tail-text T]
        # файл «многочленов» (LINSYS, ANACON, OPTIM, IDENTF, RTLZ): блоки (порядок, a0, строки ai Re Im);
        # --den/--num парами в порядке, который ждёт программа (LINSYS: объект den, num, регулятор den, num)
python vrt.py set-elem FILE.VRT NAME TYPE P1 P2 ... [--width N] [--out OUT]
        # (CONTROL/CASCAD/…) сделать выбранным (*) звено NAME типа TYPE с параметрами (пусто = '', буквы A,B,C,D допустимы)
Только stdlib (+numpy, если есть, для корней; иначе свой алгоритм Дюрана–Кернера).
"""
import sys, re, argparse, cmath

ENC = 'cp1251'
# ширина имени элемента в строках «звеньев» (после флага в колонке 0)
NAME_WIDTH = {'control': 1, 'impuls': 1, 'linsys2': 1, 'linsys3': 1, 'nlinsys': 1, 'phaspl': 1, 'spectr': 2,
              'cascad': 4, 'asympt': 4, 'mvacs2': 5}
FIELD = 8


def read(path):
    return open(path, 'rb').read().decode(ENC)


def detect(text, fname=''):
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return 'empty'
    if 'ДАННЫЕ И РЕЗУЛЬТАТЫ' in text:
        return 'report'
    if lines[0][:1] in ('*', ' ') and re.match(r'^[* ][A-Za-z ]', lines[0]) and not re.match(r'^\s*-?\d', lines[0]):
        return 'elem'
    if len(lines) > 1 and re.match(r'^\s*-?\d+\s*$', lines[0]) and re.match(r'^\s*-?\d\.\d+E[+-]\d{4}\s*$', lines[1]):
        return 'poly'
    return 'table'


# ---------- многочлены ----------
def roots(coefs):
    """Корни многочлена (коэффициенты по убыванию степеней)."""
    c = [float(x) for x in coefs]
    while c and c[0] == 0:
        c.pop(0)
    n = len(c) - 1
    if n < 1:
        return []
    try:
        import numpy as np
        r = list(np.roots(c))
    except ImportError:
        a = [x / c[0] for x in c]
        r = [(0.4 + 0.9j) ** k for k in range(n)]
        for _ in range(500):
            new = []
            for i, z in enumerate(r):
                num = sum(a[k] * z ** (n - k) for k in range(n + 1))
                den = 1
                for j, w in enumerate(r):
                    if j != i:
                        den *= (z - w)
                new.append(z - num / den)
            r = new
    # порядок как у ТАУ-3: вещественные, затем пары (−Im, +Im); по убыванию Re
    r = [complex(z) for z in r]
    r = [complex(z.real, 0.0) if abs(z.imag) < 1e-10 else z for z in r]
    r.sort(key=lambda z: (-z.real, z.imag))
    return r


def fnum(x):
    """Число в стиле Delphi: ' 3.60000000000000E+0000'."""
    if x == 0:
        return ' 0.00000000000000E+0000'
    s = '%.14E' % x
    mant, exp = s.split('E')
    e = int(exp)
    return ('%s%sE%s%04d' % (' ' if x > 0 else '', mant, '+' if e >= 0 else '-', abs(e)))


def poly_block(coefs):
    c = [float(x) for x in coefs]
    n = len(c) - 1
    lines = ['%5d' % n, fnum(c[0])]
    rs = roots(c) if n > 0 else []
    for i in range(1, n + 1):
        z = rs[i - 1]
        lines.append(fnum(c[i]) + ' ' + fnum(z.real) + ' ' + fnum(z.imag))
    return lines


def parse_poly(text):
    lines = text.splitlines()
    blocks, i = [], 0
    while i < len(lines) and re.match(r'^\s*-?\d+\s*$', lines[i]) and i + 1 < len(lines):
        n = int(lines[i]); a0 = float(lines[i + 1])
        coefs, rts = [a0], []
        for k in range(n):
            p = lines[i + 2 + k].split()
            coefs.append(float(p[0])); rts.append(complex(float(p[1]), float(p[2])))
        blocks.append(dict(order=n, coefs=coefs, roots=rts))
        i += 2 + n
    return blocks, lines[i:]


# ---------- звенья ----------
def parse_elem(text, nw):
    res = []
    for ln in text.splitlines():
        if not ln.strip():
            continue
        sel = ln[0] == '*'
        name = ln[1:1 + nw].rstrip()
        typ = ln[1 + nw:3 + nw].strip()
        rest = ln[3 + nw:]
        params = [rest[k:k + FIELD].strip() for k in range(0, len(rest.rstrip()), FIELD)]
        res.append(dict(selected=sel, name=name, type=typ, params=params, raw=ln))
    return res


def elem_line(sel, name, typ, params, nw, pad=None):
    s = ('*' if sel else ' ') + name.ljust(nw)[:nw] + str(typ).rjust(2)[:2]
    for p in params:
        p = str(p)
        if len(p) > FIELD:
            p = ('%.6g' % float(p))[:FIELD]
        s += p.ljust(FIELD)
    if pad:
        s = s.ljust(pad)
    return s


def set_elem(path, name, typ, params, nw, out=None):
    text = read(path)
    lines = text.splitlines()
    pad = max((len(l) for l in lines), default=0)
    new, found = [], False
    for ln in lines:
        e = parse_elem(ln, nw)
        if e and e[0]['name'] == name:
            if e[0]['type'] == str(typ):
                if not found:
                    new.append(elem_line(True, name, typ, params, nw, pad)); found = True
                continue
            if e[0]['selected']:
                ln = ' ' + ln[1:]
        new.append(ln)
    if not found:
        new.append(elem_line(True, name, typ, params, nw, pad))
    data = '\r\n'.join(new) + '\r\n'
    open(out or path, 'wb').write(data.encode(ENC))
    return data


def prog_of(path):
    import os
    return re.sub(r'\.vrt$', '', os.path.basename(path), flags=re.I).lower()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd'); ap.add_argument('args', nargs='*')
    ap.add_argument('--den', action='append', default=[]); ap.add_argument('--num', action='append', default=[])
    ap.add_argument('--tail'); ap.add_argument('--tail-text')
    ap.add_argument('--width', type=int); ap.add_argument('--out')
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    if a.cmd == 'show':
        t = read(a.args[0]); kind = detect(t, a.args[0]); print('format:', kind)
        if kind == 'poly':
            bl, tail = parse_poly(t)
            for k, b in enumerate(bl):
                print('block %d: order %d coefs %s roots %s' % (k, b['order'], b['coefs'],
                      ['%.6g%+.6gj' % (z.real, z.imag) for z in b['roots']]))
            if tail:
                print('tail:'); print('\n'.join(tail))
        elif kind == 'elem':
            nw = a.width or NAME_WIDTH.get(prog_of(a.args[0]), 1)
            for e in parse_elem(t, nw):
                print('%s %-5s type %-3s %s' % ('*' if e['selected'] else ' ', e['name'], e['type'],
                                               [p for p in e['params']]))
        else:
            print(t)
        return
    if a.cmd == 'roundtrip':
        t = read(a.args[0]); kind = detect(t)
        if kind == 'poly':
            bl, tail = parse_poly(t)
            lines = []
            for b in bl:
                lines += ['%5d' % b['order'], fnum(b['coefs'][0])]
                lines += [fnum(c) + ' ' + fnum(z.real) + ' ' + fnum(z.imag) for c, z in zip(b['coefs'][1:], b['roots'])]
            re_t = '\r\n'.join(lines + tail)
            ok = [l.rstrip() for l in re_t.splitlines()] == [l.rstrip() for l in t.splitlines()]
        elif kind == 'elem':
            nw = a.width or NAME_WIDTH.get(prog_of(a.args[0]), 1)
            es = parse_elem(t, nw)
            ok = all(elem_line(e['selected'], e['name'], e['type'], e['params'], nw).rstrip() == e['raw'].rstrip()
                     for e in es)
            if not ok:
                for e in es:
                    l2 = elem_line(e['selected'], e['name'], e['type'], e['params'], nw).rstrip()
                    if l2 != e['raw'].rstrip():
                        print('DIFF\n %r\n %r' % (e['raw'].rstrip(), l2))
        else:
            ok = True
        print('format', kind, 'roundtrip', 'OK' if ok else 'DIFF'); return
    if a.cmd == 'poly':
        lines = []
        for d, n in zip(a.den, a.num):
            lines += poly_block(d.replace(',', ' ').split()) + poly_block(n.replace(',', ' ').split())
        if a.tail:
            lines += read(a.tail).splitlines()
        if a.tail_text:
            lines += a.tail_text.split('\\n')
        open(a.args[0], 'wb').write(('\r\n'.join(lines) + '\r\n').encode(ENC))
        print('\n'.join(lines)); return
    if a.cmd == 'set-elem':
        path, name, typ = a.args[0], a.args[1], a.args[2]
        nw = a.width or NAME_WIDTH.get(prog_of(path), 1)
        print(set_elem(path, name, typ, a.args[3:], nw, a.out)); return
    ap.error('неизвестная команда')


if __name__ == '__main__':
    main()
