# -*- coding: utf-8 -*-
"""Справочник ТРЭИ под рукой: раздел руководства по имени функции или ФБ.

    python manual.py TON              # раздел про TON
    python manual.py TON,PWM 1500     # несколько разделов, ограничение по символам
    python manual.py --list 6         # что есть в главе 6 (функциональные блоки)
    python manual.py --example LIMITR # только «Пример синтаксиса на языке ST»

Источник — `C:\\Program Files\\UnimodPRO2\\doc\\Unimod_PRO_2_Programming_Manual.pdf`:
глава 4 — операторы, глава 5 — стандартные функции (в том числе 39 подфункций
SYSTEM), глава 6 — 165 функциональных блоков, глава 7 — диагностические блоки,
глава 9 — зарезервированные слова.

Текст вынимается `pdftotext -layout -enc UTF-8` (без -enc кириллица теряется) и
кладётся в кэш рядом с временными файлами. Оглавление извлекается без кириллицы,
но латинские имена и номера страниц целы — этого хватает для нарезки; страницы
PDF совпадают с печатными.
"""
import os
import re
import subprocess
import sys
import tempfile

PDF = r'C:\Program Files\UnimodPRO2\doc\Unimod_PRO_2_Programming_Manual.pdf'
CACHE = os.path.join(tempfile.gettempdir(), 'unimod_prog_manual.txt')
TOC_RE = re.compile(r'^\s*(\d+(?:\.\d+)*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*[-–]?.*?(\d+)\s*$')
ALIAS = {'MB_R_C': 'MB_R_', 'MB_W_C': 'MB_W_'}      # в оглавлении потерян кириллический суффикс


def pages(pdf=PDF, cache=CACHE):
    if not os.path.exists(cache) or os.path.getmtime(cache) < os.path.getmtime(pdf):
        subprocess.run(['pdftotext', '-layout', '-enc', 'UTF-8', pdf, cache], check=True)
    return open(cache, encoding='utf-8').read().split('\f')


def index(pg=None):
    """{имя: (номер раздела, первая страница, последняя)} по главам 4-7."""
    pg = pg or pages()
    rows = []
    for p in pg[1:12]:
        for line in p.splitlines():
            m = TOC_RE.match(line)
            if m and m.group(1).startswith(('4.', '5.', '6.', '7.')):
                page = int(m.group(3))
                if 90 <= page <= len(pg):
                    rows.append((m.group(1), m.group(2), page))
    rows.sort(key=lambda r: r[2])
    out = {}
    for i, (num, name, page) in enumerate(rows):
        last = rows[i + 1][2] - 1 if i + 1 < len(rows) else page + 2
        out[name] = (num, page, max(last, page))
    return out


def section(name, limit=2500, only_example=False):
    pg = pages()
    idx = index(pg)
    key = ALIAS.get(name, name)
    if key not in idx:
        return '%s: раздела в руководстве нет' % name
    num, first, last = idx[key]
    t = '\n'.join(pg[first - 1:last])
    t = re.sub(r'\n\s*\n+', '\n', t)
    t = re.sub(r'[ \t]{3,}', '  ', t)
    if only_example:
        i = t.find('Пример синтаксиса')
        t = t[i:] if i >= 0 else '(примера на ST в разделе нет)'
    return '%s — раздел %s, стр. %d-%d\n%s' % (name, num, first, last, t[:limit])


def main(argv):
    if not argv:
        print(__doc__)
        return
    if argv[0] == '--list':
        ch = argv[1] if len(argv) > 1 else None
        idx = index()
        rows = [(v[0], k, v[1]) for k, v in idx.items() if not ch or v[0].startswith(ch + '.')]
        for num, name, page in sorted(rows, key=lambda r: r[2]):
            print('%-8s %-22s стр. %d' % (num, name, page))
        print('разделов:', len(rows))
        return
    only_example = argv[0] == '--example'
    if only_example:
        argv = argv[1:]
    limit = int(argv[1]) if len(argv) > 1 else 2500
    for name in argv[0].split(','):
        print('=' * 70)
        print(section(name.strip(), limit, only_example))


if __name__ == '__main__':
    main(sys.argv[1:])
