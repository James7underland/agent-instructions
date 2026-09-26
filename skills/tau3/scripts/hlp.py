"""Декомпилятор текста WinHelp (.HLP, формат Windows 3.1/95) — в Windows 11 справка ТАУ-3 штатно не открывается.

python hlp.py TAY_3.HLP --list                 # внутренние файлы и |SYSTEM
python hlp.py TAY_3.HLP --out DIR              # все темы -> DIR/NNN_<заголовок>.md + DIR/index.md
python hlp.py TAY_3.HLP --bitmaps DIR          # картинки |bmN (только заголовок/размер; формат MRB/SHG не конвертируется)
python hlp.py TAY_3.HLP                        # весь текст в stdout
Только stdlib. Кодировка текста cp1251.
"""
import struct, sys, os, re, argparse


class Hlp:
    def __init__(self, path):
        self.d = open(path, 'rb').read()
        magic, self.dirstart = struct.unpack_from('<Ii', self.d, 0)
        assert magic == 0x35F3F, 'не WinHelp'
        self.files = self._dir()
        self._system()
        self.phrases = self._phrases()
        self.ctx = {}

    # ---- внутренняя файловая система (B+-дерево) ----
    def _dir(self):
        d = self.d
        p = self.dirstart + 9
        (magic, flags, pagesize, struc, z, splits, root, neg, total, nlev, nent) = \
            struct.unpack_from('<HHH16sHHHhHHI', d, p)
        pages = p + 38
        pg = root
        for _ in range(nlev - 1):
            pg = struct.unpack_from('<H', d, pages + pg * pagesize + 4)[0]
        out = {}
        while True:
            base = pages + pg * pagesize
            unused, n, prev, nxt = struct.unpack_from('<HHhh', d, base)
            q = base + 8
            for _ in range(n):
                e = d.index(b'\0', q)
                name = d[q:e].decode('cp1251')
                out[name] = struct.unpack_from('<i', d, e + 1)[0]
                q = e + 5
            if nxt == -1:
                break
            pg = nxt
        return out

    def file(self, name):
        off = self.files[name]
        reserved, used, fl = struct.unpack_from('<iiB', self.d, off)
        return self.d[off + 9: off + 9 + used]

    def _system(self):
        s = self.file('|SYSTEM')
        magic, self.minor, major, gendate, self.flags = struct.unpack_from('<HHHIH', s, 0)
        self.title = ''
        self.sysrec = []
        p = 12
        if self.minor > 16:
            while p + 4 <= len(s):
                t, n = struct.unpack_from('<HH', s, p)
                data = s[p + 4:p + 4 + n]
                self.sysrec.append((t, data))
                if t == 1:
                    self.title = data.split(b'\0')[0].decode('cp1251', 'replace')
                p += 4 + n
        else:
            self.title = s[p:].split(b'\0')[0].decode('cp1251', 'replace')
        self.compressed = self.minor > 16 and self.flags in (4, 8)
        self.blocksize = 2048 if (self.minor > 16 and self.flags == 8) else 4096
        if self.minor <= 16:
            self.blocksize = 2048

    # ---- сжатие ----
    @staticmethod
    def lz77(b, limit=None):
        out = bytearray(); i = 0; n = len(b)
        while i < n:
            flags = b[i]; i += 1
            for bit in range(8):
                if i >= n:
                    break
                if flags & (1 << bit):
                    if i + 1 >= n:
                        i = n; break
                    w = b[i] | (b[i + 1] << 8); i += 2
                    ln = (w >> 12) + 3; off = (w & 0xFFF) + 1
                    for _ in range(ln):
                        out.append(out[-off] if off <= len(out) else 0)
                else:
                    out.append(b[i]); i += 1
                if limit and len(out) >= limit:
                    return bytes(out[:limit])
        return bytes(out)

    def _phrases(self):
        if '|Phrases' in self.files:
            s = self.file('|Phrases')
            num, hundred = struct.unpack_from('<HH', s, 0)
            if self.minor > 16:
                size = struct.unpack_from('<I', s, 4)[0]
                offs = struct.unpack_from('<%dH' % (num + 1), s, 8)
                img = self.lz77(s[8 + 2 * (num + 1):], size)
                base = offs[0]
                return [img[offs[i] - base:offs[i + 1] - base] for i in range(num)]
            offs = struct.unpack_from('<%dH' % (num + 1), s, 4)
            return [s[4 + offs[i]:4 + offs[i + 1]] for i in range(num)]
        if '|PhrIndex' in self.files:
            return self._hall()
        return []

    def _hall(self):
        idx = self.file('|PhrIndex'); img = self.file('|PhrImage')
        (magic, nent, compsize, imgsize, imgcomp, zero) = struct.unpack_from('<IiiiiI', idx, 0)
        bits_hdr = struct.unpack_from('<H', idx, 24)[0] if len(idx) > 26 else 0
        bitcount = bits_hdr & 0x0F
        if imgsize != imgcomp:
            img = self.lz77(img, imgsize)
        # битовый поток длин фраз
        data = idx[28:]
        pos = 0; bitpos = 0
        def getbit():
            nonlocal pos, bitpos
            v = (struct.unpack_from('<I', data, pos)[0] >> bitpos) & 1
            bitpos += 1
            if bitpos == 32:
                bitpos = 0; pos += 4
            return v
        phr = []; o = 0
        for _ in range(nent):
            n = 1
            while getbit():
                n += 1 << bitcount
            if getbit():
                n += 1
            if bitcount > 1 and getbit():
                n += 2
            if bitcount > 2 and getbit():
                n += 4
            if bitcount > 3 and getbit():
                n += 8
            if bitcount > 4 and getbit():
                n += 16
            phr.append(img[o:o + n]); o += n
        self.hall = True
        return phr

    def expand(self, b):
        """Раскрыть фразовое сжатие LinkData2."""
        if getattr(self, 'hall', False):
            out = bytearray(); i = 0
            while i < len(b):
                c = b[i]; i += 1
                if c & 1 == 0:
                    out += self.phrases[c // 2]
                elif c & 3 == 1:
                    out += self.phrases[128 + (c // 4) * 256 + b[i]]; i += 1
                elif c & 7 == 3:
                    n = c // 8 + 1; out += b[i:i + n]; i += n
                elif c & 15 == 7:
                    out += b' ' * (c // 16 + 1)
                else:
                    out += b'\0' * (c // 16 + 1)
            return bytes(out)
        out = bytearray(); i = 0
        while i < len(b):
            c = b[i]; i += 1
            if c == 0 or c > 0x10 or not self.phrases:
                out.append(c)
            else:
                n = 256 * (c - 1) + b[i]; i += 1
                out += self.phrases[n // 2]
                if n & 1:
                    out.append(32)
        return bytes(out)

    # ---- |TOPIC ----
    def topic_space(self):
        """Виртуальное адресное пространство распакованных блоков: адрес = блок*0x4000 + смещение."""
        t = self.file('|TOPIC')
        bs = self.blocksize
        self.vspace = {}
        buf = bytearray()
        nblocks = (len(t) + bs - 1) // bs
        firsts = []
        for k in range(nblocks):
            blk = t[k * bs:(k + 1) * bs]
            last, first, lasthdr = struct.unpack_from('<iii', blk, 0)
            firsts.append(first)
            body = self.lz77(blk[12:], 0x4000 - 12) if self.compressed else blk[12:]
            body = body.ljust(0x4000 - 12, b'\0')
            buf += b'\0' * 12 + body
        self.topicbuf = bytes(buf)
        return firsts

    def read_at(self, pos, n):
        """Прочитать n байт с виртуального адреса, пропуская 12-байтные заголовки следующих блоков."""
        out = bytearray()
        while n > 0:
            blk, off = divmod(pos, 0x4000)
            if off < 12:
                off = 12
            take = min(n, 0x4000 - off)
            out += self.topicbuf[blk * 0x4000 + off: blk * 0x4000 + off + take]
            n -= take; pos = (blk + 1) * 0x4000 + 12
        return bytes(out)

    def links(self):
        firsts = self.topic_space()
        pos = firsts[0]
        seen = set()
        while pos not in seen and 0 <= pos < len(self.topicbuf):
            seen.add(pos)
            hdr = self.read_at(pos, 21)
            if len(hdr) < 21:
                break
            bsize, dlen2, prev, nxt, dlen1, rtype = struct.unpack_from('<iiiiiB', hdr, 0)
            if bsize <= 0:
                break
            rec = self.read_at(pos, bsize)
            ld1 = rec[21:dlen1]
            ld2 = rec[dlen1:bsize]
            if dlen2 > bsize - dlen1:
                ld2 = self.expand(ld2)
            yield rtype, ld1, ld2[:dlen2] if dlen2 else ld2
            if nxt <= 0 or nxt == pos:
                break
            pos = nxt

    # ---- разбор форматированного текста ----
    @staticmethod
    def _cl(b, p):   # compressed long
        v = struct.unpack_from('<I', b, p)[0] if b[p] & 1 else struct.unpack_from('<H', b, p)[0]
        return (v >> 1, p + (4 if b[p] & 1 else 2))

    @staticmethod
    def _cs(b, p):   # compressed short
        v = struct.unpack_from('<H', b, p)[0] if b[p] & 1 else b[p]
        return (v >> 1, p + (2 if b[p] & 1 else 1))

    def render(self, rtype, ld1, ld2):
        strings = ld2.split(b'\0')
        p = 0
        _, p = self._cl(ld1, p)
        if rtype in (0x20, 0x23):
            _, p = self._cs(ld1, p)
        ncols = 1
        if rtype == 0x23:
            ncols = ld1[p]; ttype = ld1[p + 1]; p += 2
            if ttype in (0, 2):
                p += 2
            p += 4 * ncols
        out = []; si = 0
        cell = 0
        while p < len(ld1):
            if rtype == 0x23:
                col = struct.unpack_from('<h', ld1, p)[0]; p += 2
                if col == -1:
                    break
                if cell:
                    out.append(' | ')
                cell += 1
            p += 1                      # unknownUnsignedChar
            p += 1 if not (ld1[p] & 1) else 2  # biased short
            p += 2                      # id
            bits = struct.unpack_from('<H', ld1, p)[0]; p += 2
            if bits & 1: _, p = self._cl(ld1, p)
            for bb in (2, 4, 8, 0x10, 0x20, 0x40):
                if bits & bb: _, p = self._cs(ld1, p)
            if bits & 0x100: p += 3
            if bits & 0x200:
                nt, p = self._cs(ld1, p)
                for _ in range(nt):
                    ts, p = self._cs(ld1, p)
                    if ts & 0x4000: _, p = self._cs(ld1, p)
            while p < len(ld1):
                if si < len(strings):
                    out.append(strings[si].decode('cp1251', 'replace')); si += 1
                c = ld1[p]; p += 1
                if c == 0xFF:
                    break
                if c == 0x20: p += 4
                elif c == 0x21: p += 2
                elif c == 0x80: p += 2
                elif c == 0x81: out.append('\n')
                elif c == 0x82: out.append('\n\n')
                elif c == 0x83: out.append('\t')
                elif c in (0x86, 0x87, 0x88):
                    typ = ld1[p]; p += 1
                    sz, p = self._cl(ld1, p)
                    if typ == 0x22: _, p = self._cs(ld1, p)
                    pic = ld1[p:p + sz]
                    if typ == 0x22 or typ == 0x03:
                        try:
                            bmn = struct.unpack_from('<H', pic, 2 if typ == 0x22 else 0)[0]
                        except Exception:
                            bmn = -1
                        out.append('[рис. bm%d]' % bmn)
                    else:
                        out.append('[рис.]')
                    p += sz
                elif c in (0x89,): out.append('»')
                elif c == 0x8B: out.append(' ')
                elif c == 0x8C: out.append('-')
                elif c in (0xC8, 0xCC):
                    n = struct.unpack_from('<h', ld1, p)[0]; p += 2 + n; out.append('«')
                elif c in (0xE0, 0xE1, 0xE2, 0xE3, 0xE6, 0xE7):
                    p += 4; out.append('«')
                elif c in (0xEA, 0xEB, 0xEE, 0xEF):
                    n = struct.unpack_from('<h', ld1, p)[0]; p += 2 + n; out.append('«')
                else:
                    out.append('')
            if rtype != 0x23:
                break
        while si < len(strings):
            out.append(strings[si].decode('cp1251', 'replace')); si += 1
        return ''.join(out)

    def topics(self):
        """Список (заголовок, текст)."""
        res = []; cur = None
        for rtype, ld1, ld2 in self.links():
            if rtype == 2:
                title = ld2.split(b'\0')[0].decode('cp1251', 'replace')
                cur = [title, []]; res.append(cur)
            elif rtype in (0x20, 0x23):
                if cur is None:
                    cur = ['(без заголовка)', []]; res.append(cur)
                try:
                    cur[1].append(self.render(rtype, ld1, ld2))
                except Exception as e:
                    cur[1].append(ld2.replace(b'\0', b'\n').decode('cp1251', 'replace'))
        return [(t, re.sub(r'\n{3,}', '\n\n', ''.join(b)).strip()) for t, b in res]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('hlp'); ap.add_argument('--list', action='store_true'); ap.add_argument('--out')
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    h = Hlp(a.hlp)
    if a.list:
        print('title:', h.title, 'minor:', h.minor, 'flags:', h.flags, 'phrases:', len(h.phrases))
        for k, v in h.files.items():
            print(k, v)
        return
    tops = h.topics()
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        idx = ['# %s — оглавление тем\n' % h.title]
        for i, (t, txt) in enumerate(tops):
            safe = re.sub(r'[^\w\- ]+', '', t)[:50].strip().replace(' ', '_') or 'topic'
            fn = '%03d_%s.md' % (i, safe)
            open(os.path.join(a.out, fn), 'w', encoding='utf-8').write('# %s\n\n%s\n' % (t, txt))
            idx.append('- [%s](%s) — %d симв.' % (t, fn, len(txt)))
        open(os.path.join(a.out, 'index.md'), 'w', encoding='utf-8').write('\n'.join(idx) + '\n')
        print('%d тем -> %s' % (len(tops), a.out))
    else:
        for t, txt in tops:
            print('=' * 70 + '\n# ' + t + '\n' + txt + '\n')


if __name__ == '__main__':
    main()
