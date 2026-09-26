"""Извлечение форм Delphi (бинарный DFM, ресурсы RCDATA) из exe и перевод в текстовый .dfm.

python dfm.py <exe> [--out DIR]        # все формы exe -> текст (stdout или DIR/<exe>.txt)
python dfm.py --all <dir> --out DIR    # все exe каталога
python dfm.py <exe> --summary          # кратко: формы, меню, кнопки, поля, подписи
Только stdlib. Строки в DFM — cp1251.
"""
import struct, sys, os, glob, argparse

RT_RCDATA = 10


def pe_resources(data):
    """Вернуть {(type, name): bytes} для ресурсов PE."""
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    nsec = struct.unpack_from('<H', data, pe + 6)[0]
    optsz = struct.unpack_from('<H', data, pe + 20)[0]
    opt = pe + 24
    # data directory #2 = resources (PE32)
    rva_res = struct.unpack_from('<I', data, opt + 96 + 2 * 8)[0]
    secs = []
    off = opt + optsz
    for i in range(nsec):
        s = data[off + 40 * i: off + 40 * i + 40]
        vsz, va, rsz, rptr = struct.unpack_from('<IIII', s, 8)
        secs.append((va, max(vsz, rsz), rptr))

    def r2o(rva):
        for va, sz, ptr in secs:
            if va <= rva < va + sz:
                return rva - va + ptr
        raise ValueError(hex(rva))

    base = r2o(rva_res)
    out = {}

    def name_of(entry_name):
        if entry_name & 0x80000000:
            p = base + (entry_name & 0x7fffffff)
            n = struct.unpack_from('<H', data, p)[0]
            return data[p + 2: p + 2 + 2 * n].decode('utf-16-le')
        return entry_name

    def walk(p, path):
        nnamed, nid = struct.unpack_from('<HH', data, p + 12)
        for i in range(nnamed + nid):
            nm, target = struct.unpack_from('<II', data, p + 16 + 8 * i)
            key = path + [name_of(nm)]
            if target & 0x80000000:
                walk(base + (target & 0x7fffffff), key)
            else:
                drva, dsz = struct.unpack_from('<II', data, base + target)
                o = r2o(drva)
                out[(key[0], key[1])] = data[o:o + dsz]
    walk(base, [])
    return out


class Reader:
    def __init__(self, b):
        self.b, self.p = b, 0

    def u8(self):
        v = self.b[self.p]; self.p += 1; return v

    def peek(self):
        return self.b[self.p]

    def fmt(self, f):
        v = struct.unpack_from(f, self.b, self.p); self.p += struct.calcsize(f); return v[0]

    def sstr(self):
        n = self.u8(); s = self.b[self.p:self.p + n]; self.p += n
        return s.decode('cp1251', 'replace')


def ext80(b):
    """Delphi Extended (80 бит) -> float."""
    mant = int.from_bytes(b[:8], 'little'); se = int.from_bytes(b[8:10], 'little')
    sign = -1 if se & 0x8000 else 1; e = se & 0x7fff
    if e == 0 and mant == 0:
        return 0.0
    return sign * mant / (1 << 63) * 2.0 ** (e - 16383)


def q(s):
    out, inq = '', False
    for ch in s:
        if 32 <= ord(ch) < 127 or ord(ch) >= 0x400 or ch in '«»№—–':
            if not inq:
                out += "'"; inq = True
            out += "''" if ch == "'" else ch
        else:
            if inq:
                out += "'"; inq = False
            out += '#%d' % ord(ch)
    if inq:
        out += "'"
    return out or "''"


def read_value(r, ind):
    t = r.u8()
    if t == 0: return 'nil?'
    if t == 1:
        items = []
        while r.peek() != 0:
            items.append(read_value(r, ind + 2))
        r.u8(); return '(' + ' '.join(items) + ')'
    if t == 2: return str(r.fmt('<b'))
    if t == 3: return str(r.fmt('<h'))
    if t == 4: return str(r.fmt('<i'))
    if t == 5:
        v = ext80(r.b[r.p:r.p + 10]); r.p += 10; return repr(v)
    if t in (6, 7):
        s = r.sstr(); return q(s) if t == 6 else s
    if t == 8: return 'False'
    if t == 9: return 'True'
    if t == 10:
        n = r.fmt('<i'); r.p += n; return '{binary %d bytes}' % n
    if t == 11:
        items = []
        while True:
            s = r.sstr()
            if not s: break
            items.append(s)
        return '[' + ', '.join(items) + ']'
    if t == 12:
        n = r.fmt('<i'); s = r.b[r.p:r.p + n].decode('cp1251', 'replace'); r.p += n; return q(s)
    if t == 13: return 'nil'
    if t == 14:
        pad = ' ' * (ind + 2); lines = ['<']
        while r.peek() != 0:
            if r.peek() in (2, 3, 4):
                read_value(r, ind)
            assert r.u8() == 1
            lines.append(pad + 'item')
            while r.peek() != 0:
                nm = r.sstr(); lines.append(pad + '  %s = %s' % (nm, read_value(r, ind + 4)))
            r.u8(); lines.append(pad + 'end')
        r.u8(); return '\n'.join(lines) + '>'
    if t == 15: return repr(r.fmt('<f'))
    if t in (16, 17): return repr(r.fmt('<d'))
    if t == 18:
        n = r.fmt('<i'); s = r.b[r.p:r.p + 2 * n].decode('utf-16-le'); r.p += 2 * n; return q(s)
    if t == 19: return str(r.fmt('<q'))
    if t == 20:
        n = r.fmt('<i'); s = r.b[r.p:r.p + n].decode('utf-8', 'replace'); r.p += n; return q(s)
    raise ValueError('unknown value type %d at %d' % (t, r.p))


def read_object(r, ind, lines):
    kw = 'object'
    if r.peek() & 0xF0 == 0xF0:
        flags = r.u8() & 0x0F
        if flags & 2:  # ffChildPos
            read_value(r, ind)
        kw = 'inherited' if flags & 1 else ('inline' if flags & 4 else 'object')
    cls = r.sstr(); name = r.sstr()
    pad = ' ' * ind
    lines.append('%s%s %s: %s' % (pad, kw, name, cls) if name else '%s%s %s' % (pad, kw, cls))
    while r.peek() != 0:
        pn = r.sstr(); v = read_value(r, ind + 2)
        lines.append('%s  %s = %s' % (pad, pn, v))
    r.u8()
    while r.peek() != 0:
        read_object(r, ind + 2, lines)
    r.u8()
    lines.append(pad + 'end')


def dfm_to_text(b):
    assert b[:4] == b'TPF0'
    r = Reader(b); r.p = 4; lines = []
    read_object(r, 0, lines)
    return '\n'.join(lines)


def forms_of(exe):
    data = open(exe, 'rb').read()
    res = pe_resources(data)
    forms = {}
    for (t, n), b in sorted(res.items(), key=lambda x: str(x[0][1])):
        if t == RT_RCDATA and b[:4] == b'TPF0':
            forms[str(n)] = dfm_to_text(b)
    return forms


def summary(text):
    """Кратко: объекты с Caption/Text/Hint (что видит пользователь)."""
    out, stack = [], []
    cur = None
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith(('object ', 'inherited ', 'inline ')):
            cur = s.split(' ', 1)[1]; stack.append(cur)
        elif s == 'end':
            if stack: stack.pop()
        elif ' = ' in s and s.split(' = ')[0] in ('Caption', 'Text', 'Hint', 'Items.Strings', 'Lines.Strings', 'Title'):
            if s.split(' = ', 1)[1] not in ("''",):
                out.append('%s%s  %s' % ('  ' * (len(stack) - 1), stack[-1] if stack else '?', s))
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('exe', nargs='?')
    ap.add_argument('--all')
    ap.add_argument('--out')
    ap.add_argument('--summary', action='store_true')
    a = ap.parse_args()
    exes = sorted(glob.glob(os.path.join(a.all, '*.exe'))) if a.all else [a.exe]
    sys.stdout.reconfigure(encoding='utf-8')
    for exe in exes:
        forms = forms_of(exe)
        body = []
        for n, t in forms.items():
            body.append('// ===== %s =====\n%s\n' % (n, summary(t) if a.summary else t))
        txt = '\n'.join(body)
        if a.out:
            os.makedirs(a.out, exist_ok=True)
            base = os.path.splitext(os.path.basename(exe))[0].lower()
            fn = os.path.join(a.out, base + ('.summary.txt' if a.summary else '.dfm.txt'))
            open(fn, 'w', encoding='utf-8').write(txt)
            print('%s: %d forms -> %s' % (exe, len(forms), fn))
        else:
            print(txt)


if __name__ == '__main__':
    main()
