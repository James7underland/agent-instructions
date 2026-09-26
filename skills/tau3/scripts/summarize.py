"""Свести отчёты crawl.py в Markdown: меню каждой программы, какие окна/диалоги открывает каждый пункт, меню окон.

python summarize.py CRAWL_DIR OUT.md
"""
import json, glob, os, sys

src, dst = sys.argv[1], sys.argv[2]
out = ['# Интерфейс программ ТАУ-3 (снято обходчиком crawl.py)', '',
       'Для каждой программы: пункты главного (всплывающего) меню; что открывает каждый пункт — окна (в фигурных',
       'скобках — меню окна) и модальные диалоги (класс: заголовок). [серый] — пункт недоступен в текущем режиме.', '']
for f in sorted(glob.glob(os.path.join(src, '*', 'report.json'))):
    d = json.load(open(f, encoding='utf-8'))
    out.append('## %s' % d['prog'].upper())
    menu = [i['path'] + (' [серый]' if i['disabled'] else '') for i in d.get('menu', []) if i['id'] is not None]
    out.append('Меню: ' + ' · '.join(menu))
    out.append('')
    for it in d['items']:
        ws = ['«%s»%s' % (w['title'].strip(), ' {' + ', '.join(w['menu']) + '}' if w.get('menu') else '')
              for w in it.get('windows', [])]
        ms = []
        for m in it.get('modals', []):
            s = '%s «%s»' % (m['cls'], m['title'].strip())
            if m.get('filled'):
                s += ' (заполнено %s)' % m['filled']
            ms.append(s)
        line = '- **%s** → окна: %s' % (it['path'], ', '.join(ws) or '—')
        if ms:
            line += '; диалоги: ' + ', '.join(ms)
        if it.get('error'):
            line += '; ОШИБКА: ' + it['error']
        out.append(line)
    out.append('')
open(dst, 'w', encoding='utf-8').write('\n'.join(out))
print('ok', dst)
