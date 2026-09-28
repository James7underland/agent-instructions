# -*- coding: utf-8 -*-
"""Смысловое сравнение двух версий FBD-программы Unimod PRO 2.

    python fbd_diff.py <старый prog.json> <новый prog.json>

save_id сравнивать бессмысленно — IDE перенумеровывает их при сохранении.
Блоки сопоставляются по шагам: та же клетка и имя → тот же блок; та же клетка
и тип, другое имя → переменная или константа заменена; то же имя и те же соседи
по связям (или единственный блок с таким именем) → блок переставлен. Печатает изменения блоков, связей, порядка выполнения и
построчный дифф «что делает схема» (как в fbd_dump.py).
"""
import difflib, io, json, sys, contextlib
import fbd_dump

MODE = {0: 'обычная', 1: 'закомментирована', 2: 'инверсия'}


def load(path):
    t = json.load(open(path, encoding='utf-8')).get('text', {})
    if 'Blocks' not in t:
        raise SystemExit('%s — не FBD-схема' % path)
    return t['Blocks'], t.get('Links', [])


def label(b):
    return '%s «%s» (%s,%s)' % (fbd_dump.KIND.get(b.get('type'), b.get('type')),
                               b.get('name'), b.get('column'), b.get('line'))


def signature(b, blocks, links):
    """Тип, имя и соседи по связям — не зависит от положения и save_id."""
    by_id = {x['save_id']: x for x in blocks}
    nb = []
    for l in links:
        if l['dst_block'] == b['save_id'] and l['src_block'] in by_id:
            o = by_id[l['src_block']]
            nb.append(('in', l['dst_slot'], o.get('type'), o.get('name'), l['src_slot']))
        if l['src_block'] == b['save_id'] and l['dst_block'] in by_id:
            o = by_id[l['dst_block']]
            nb.append(('out', l['src_slot'], o.get('type'), o.get('name'), l['dst_slot']))
    return (b.get('type'), b.get('name'), tuple(sorted(nb, key=str)))


def match(ob, ol, nb, nl):
    """Словарь save_id старой версии -> (save_id новой, вид сопоставления)."""
    m = {}
    left_o = list(ob)
    left_n = list(nb)

    def take(pred, kind):
        for o in list(left_o):
            cands = [n for n in left_n if pred(o, n)]
            if len(cands) == 1:
                m[o['save_id']] = (cands[0]['save_id'], kind)
                left_o.remove(o)
                left_n.remove(cands[0])

    take(lambda o, n: (o.get('type'), o.get('name'), o.get('column'), o.get('line')) ==
                      (n.get('type'), n.get('name'), n.get('column'), n.get('line')), 'same')
    osig = {o['save_id']: signature(o, ob, ol) for o in ob}
    nsig = {n['save_id']: signature(n, nb, nl) for n in nb}
    take(lambda o, n: osig[o['save_id']] == nsig[n['save_id']], 'moved')
    take(lambda o, n: o.get('type') == n.get('type') and o.get('type') in (0, 1) and
                      (o.get('column'), o.get('line')) == (n.get('column'), n.get('line')), 'renamed')
    # переставлен и перекоммутирован одновременно: то же имя, единственный кандидат
    take(lambda o, n: (o.get('type'), o.get('name')) == (n.get('type'), n.get('name')), 'moved')
    return m, left_o, left_n


def expressions(path):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fbd_dump.dump(path)
    part = buf.getvalue().split('--- что делает схема (в порядке sequence) ---')[1].split('--- замечания ---')[0]
    return [l for l in part.splitlines() if l.strip()]


def diff(old_path, new_path):
    ob, ol = load(old_path)
    nb, nl = load(new_path)
    m, removed, added = match(ob, ol, nb, nl)
    oid = {b['save_id']: b for b in ob}
    nid = {b['save_id']: b for b in nb}

    print('=== блоки: было %d, стало %d' % (len(ob), len(nb)))
    for b in removed:
        print('  - удалён      ', label(b))
    for b in added:
        print('  + добавлен    ', label(b))
    for o_id, (n_id, kind) in m.items():
        o, n = oid[o_id], nid[n_id]
        if kind == 'moved':
            print('  ~ переставлен ', label(o), '-> (%s,%s)' % (n.get('column'), n.get('line')))
        elif kind == 'renamed':
            print('  ~ заменён     ', label(o), '->', '«%s»' % n.get('name'))

    def lkey(l, remap):
        return (remap(l['src_block']), l['src_slot'], remap(l['dst_block']), l['dst_slot'])
    old_links = {lkey(l, lambda i: m[i][0] if i in m else ('old', i)): l for l in ol}
    new_links = {lkey(l, lambda i: i): l for l in nl}
    print('=== связи: было %d, стало %d' % (len(ol), len(nl)))
    for k, l in old_links.items():
        if k not in new_links:
            print('  - %s -> %s' % (l['src_name'], l['dst_name']))
    for k, l in new_links.items():
        if k not in old_links:
            print('  + %s -> %s' % (l['src_name'], l['dst_name']))
        elif old_links[k].get('mode') != l.get('mode'):
            print('  ~ %s -> %s: %s -> %s' % (l['src_name'], l['dst_name'],
                  MODE.get(old_links[k].get('mode')), MODE.get(l.get('mode'))))

    pairs = [(oid[o], nid[n]) for o, (n, k) in m.items()
             if oid[o].get('sequence', -1) >= 0 and nid[n].get('sequence', -1) >= 0]
    o_order = [o['save_id'] for o, n in sorted(pairs, key=lambda p: p[0]['sequence'])]
    n_order = [o['save_id'] for o, n in sorted(pairs, key=lambda p: p[1]['sequence'])]
    print('=== порядок выполнения сохранившихся блоков: %s' % ('не изменился' if o_order == n_order else 'ИЗМЕНИЛСЯ'))
    if o_order != n_order:
        for i, (a, b) in enumerate(zip(o_order, n_order)):
            if a != b:
                print('  первое расхождение: было %s, стало %s' % (label(oid[a]), label(oid[b])))
                break

    print('=== что делает схема (дифф)')
    d = list(difflib.unified_diff(expressions(old_path), expressions(new_path), lineterm='', n=0))
    body = [x for x in d[2:] if not x.startswith('@@')]
    print('\n'.join('  ' + x for x in body) if body else '  без изменений')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__)
        raise SystemExit(1)
    diff(sys.argv[1], sys.argv[2])
