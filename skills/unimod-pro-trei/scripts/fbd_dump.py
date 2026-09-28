# -*- coding: utf-8 -*-
"""Читает FBD-программу Unimod PRO 2 (prog.json) и печатает её по-человечески.

    python fbd_dump.py <путь к prog.json> [--blocks] [--links]
    python fbd_dump.py <путь к prog.json> --check-st <текст «Вывести код на ST»>

Печатает выражения в порядке выполнения (как их соберёт генератор ST), список
блоков и замечания: неподключённые входы, висящие связи, расхождение Define.
Нужен, чтобы разбирать чужие схемы, не открывая IDE, и чтобы сверять свою
схему после генерации.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fbd_gen import order_remarks, block_box, struct_catalog, _project_root, Scheme

TYPE_NAME = {0: 'BOOL', 1: 'INT', 2: 'REAL', 3: 'TIMER', 4: 'MESSAGE',
             5: 'BYTE', 6: 'DOUBLE', -1: 'любой'}
KIND = {0: 'переменная', 1: 'константа', 2: 'структура с полями', 3: 'ФБ',
        4: 'оператор', 5: 'шина', 7: 'виток', 8: 'контакт', 9: 'метка',
        10: 'прыжок', 12: 'структура', 13: 'eni/eno', 14: 'комментарий',
        15: 'функция', 16: 'дочерняя программа'}
# операторы, которые ST печатает как функцию: SQRT( x ), MOD( a,b ), а не инфиксно
# (проверено 2026-09-18 сборкой: так их печатает «Вывести код на ST»)
FUNC_OPS = {'SQRT', 'ABS', 'SIN', 'COS', 'TAN', 'ASIN', 'ACOS', 'ATAN',
            'LN', 'LOG', 'EXP', 'TRUNC', 'NOT', 'MOD', 'POW', 'EXPT', 'RAND', 'ODD',
            'SHL', 'SHR', 'ROL', 'ROR', 'GETBIT', 'GETBYTE', 'AND_MASK', 'OR_MASK',
            'XOR_MASK', 'NOT_MASK', 'BYTE_AND_MASK', 'BYTE_OR_MASK', 'BYTE_XOR_MASK',
            'BYTE_NOT_MASK'}
# у контактов и витков по фронту/спаду IDE заводит скрытую переменную (_temp_front_N),
# точный текст не воспроизвести — такие строки сверка пропускает с обеих сторон
EDGE_MARK = '<фронт/спад>'


def load(path):
    d = json.load(open(path, encoding='utf-8'))
    t = d.get('text', {})
    if 'Blocks' not in t:
        raise SystemExit('%s — не FBD-программа (в text нет Blocks)' % path)
    return d, t


def src_expr(link, blocks, incoming, seen=None):
    """Выражение на конце связи: учитывает, с какого вывода она идёт."""
    sb = blocks.get(link['src_block'])
    if sb is None:
        return '<нет блока %s>' % link['src_block']
    if sb.get('type') == 3:                  # выход ФБ читается как поле экземпляра
        return '%s.%s' % (sb['name'].split('.')[0], sb.get('out%d_name' % (link['src_slot'] + 1)))
    if sb.get('type') == 2:                  # структура с полями: <экземпляр>.<поле>
        return '%s.%s' % (sb['name'], sb.get('out%d_name' % (link['src_slot'] + 1)))
    if sb.get('type') == 5:                  # левая силовая шина LD — это TRUE
        return 'TRUE'
    return expr(sb, blocks, incoming, seen)


def expr(b, blocks, incoming, seen=None):
    """Строит выражение, которое даёт выход блока b (рекурсивно по связям)."""
    seen = seen or set()
    if b['save_id'] in seen:
        return '<цикл>'
    seen = seen | {b['save_id']}
    kind = b.get('type')
    if kind in (0, 1):                       # переменная, константа
        return b['name']
    if kind == 8:                            # контакт LD
        src = incoming.get((b['save_id'], 0))
        left = src_expr(src, blocks, incoming, seen) if src else '<не присоединён>'
        if b.get('subtype') in (2, 3):       # (N) и (P) — со скрытой переменной фронта
            return EDGE_MARK
        return '( %s AND %s%s )' % (left, 'NOT ' if b.get('subtype') == 1 else '', b['name'])
    if kind in (4, 15, 16):                  # оператор, функция проекта или дочерняя программа
        args = []
        for slot in range(b.get('inp_count', 0)):
            src = incoming.get((b['save_id'], slot))
            a = src_expr(src, blocks, incoming, seen) if src else '<не присоединён>'
            if src and src.get('mode') == 2:
                a = 'NOT %s' % a             # инвертированная связь
            args.append(a)
        if b['name'] == 'NEG':               # унарный минус печатается знаком
            return '(- %s )' % args[0]
        if kind in (15, 16):                 # функция или дочерняя программа: name( a, b )
            return '%s( %s )' % (b['name'], ', '.join(args))
        if b['name'] == ':=':                # присваивание прозрачно
            return args[0]
        if b['name'] in FUNC_OPS or len(args) == 1:
            return '%s( %s )' % (b['name'], ', '.join(args))
        return '( %s )' % ((' %s ' % b['name']).join(args))
    return '%s[%s]' % (b['name'], KIND.get(kind, kind))


def struct_fields_of(path):
    """{экземпляр структуры: [поля]} для программы — нужно блокам «структура»
    (type 12): связь между двумя такими блоками IDE разворачивает в присваивание
    всех полей по очереди."""
    if not path:
        return {}
    csv = os.path.join(os.path.dirname(os.path.abspath(path)), 'prog.csv')
    root = _project_root(path)
    if not root or not os.path.exists(csv):
        return {}
    cat = struct_catalog(root)
    inst = Scheme(dict_csv=csv).instances
    return {i: [f[0] for f in cat[st]['fields']] for i, st in inst.items() if st in cat}


def statements(t, path=None):
    """Операторы ST, которые даст схема, в порядке sequence (с отступами у eni)."""
    blocks = {b['save_id']: b for b in t['Blocks']}
    links = [l for l in t.get('Links', []) if l.get('mode') != 1]
    incoming = {(l['dst_block'], l['dst_slot']): l for l in links}
    eni_of = {b['block']: b for b in t['Blocks'] if b.get('type') == 13 and 'block' in b}
    live = [b for b in t['Blocks'] if b.get('type') != 14 and not (b.get('mode') == 1 and b.get('sequence') == -1)]
    out = []
    fields = struct_fields_of(path)
    for b in sorted(live, key=lambda b: b.get('sequence', 0)):
        if b.get('type') == 9:               # метка
            out.append('%s:' % b['name'])
            continue
        if b.get('type') == 10:              # прыжок по условию
            src = incoming.get((b['save_id'], 0))
            cond = src_expr(src, blocks, incoming) if src else '<не присоединён>'
            out.append('if %s then goto %s; end_if;' % (cond, b['name']))
            continue
        if b.get('type') == 7:               # виток LD
            src = incoming.get((b['save_id'], 0))
            e = src_expr(src, blocks, incoming) if src else '<не присоединён>'
            st = b.get('subtype', 0)
            if EDGE_MARK in e or st in (2, 3):
                out.append(EDGE_MARK)
            elif st == 4:
                out.append('if %s then %s := FALSE; end_if;' % (e, b['name']))
            elif st == 5:
                out.append('if %s then %s := TRUE; end_if;' % (e, b['name']))
            elif st == 1:
                out.append('%s := NOT %s;' % (b['name'], e))
            else:
                out.append('%s := %s;' % (b['name'], e))
            continue
        if b.get('type') == 12:              # структура целиком: копирование поле за полем
            src = incoming.get((b['save_id'], 0))
            if src:
                sb = blocks.get(src['src_block'], {})
                for f in fields.get(b['name'], []):
                    out.append('%s.%s := %s.%s;' % (b['name'], f, sb.get('name'), f))
            continue
        if b.get('type') == 2:               # структура с полями: запись полей
            for slot in range(b.get('inp_count', 0)):
                src = incoming.get((b['save_id'], slot))
                if src:
                    rhs = src_expr(src, blocks, incoming)
                    if src.get('mode') == 2:
                        rhs = 'NOT %s' % rhs
                    out.append('%s.%s := %s;' % (b['name'], b.get('inp%d_name' % (slot + 1)), rhs))
            continue
        if b.get('type') == 3:               # вызов ФБ
            inst = b['name'].split('.')[0]
            en = eni_of.get(b['save_id'])
            cond = incoming.get((en['save_id'], 0)) if en else None
            pad = ''
            if cond:
                out.append('if (%s) then' % src_expr(cond, blocks, incoming))
                pad = '  '
            for slot in range(b.get('inp_count', 0)):
                src = incoming.get((b['save_id'], slot))
                if src:
                    rhs = src_expr(src, blocks, incoming)
                    if src.get('mode') == 2:
                        rhs = 'NOT %s' % rhs
                    out.append('%s%s.%s := %s;' % (pad, inst, b.get('inp%d_name' % (slot + 1)), rhs))
            out.append('%s%s();' % (pad, b['name']))
            if cond:
                out.append('end_if;')
            continue
        if b.get('type') == 0 and (b['save_id'], 0) in incoming:
            src = incoming[(b['save_id'], 0)]
            rhs = src_expr(src, blocks, incoming)
            if src.get('mode') == 2:
                rhs = 'NOT %s' % rhs
            out.append('%s := %s;' % (b['name'], rhs))
    return out


def _norm(line):
    """Сравнение без пробелов, скобок и регистра: «( a OR b ) AND (NOT c )» == «(a OR b) AND NOT c»."""
    return re.sub(r'[\s()]', '', line).upper().rstrip(';')


def check_st(path, ide_text):
    """Сверка схемы с текстом «Сборка → Редактор → Вывести код на ST» (строки «N. код»).
    Ловит то, что IDE молча не прочла: пропавшие цепочки, урезанные операторы,
    другой порядок. Возвращает список расхождений."""
    _, t = load(path)
    want = [_norm(x) for x in statements(t, path) if EDGE_MARK not in x]
    got = []
    for raw in ide_text.splitlines():
        m = re.match(r'^\s*\d+\.\s?(.*)$', raw)
        if m and m.group(1).strip() and '_temp_front' not in raw and '_temp_back' not in raw:
            got.append(_norm(m.group(1)))
    bad = []
    if len(got) != len(want):
        bad.append('операторов в выводе IDE %d, в файле %d' % (len(got), len(want)))
    for i in range(max(len(got), len(want))):
        g = got[i] if i < len(got) else '<нет>'
        w = want[i] if i < len(want) else '<нет>'
        if g != w:
            bad.append('№%d: IDE %s | файл %s' % (i + 1, g, w))
            if len(bad) > 10:
                bad.append('… дальше не сравниваю')
                break
    return bad


def dump(path, show_blocks=False, show_links=False):
    d, t = load(path)
    all_links = t.get('Links', [])
    blocks = {b['save_id']: b for b in t['Blocks']}
    # закомментированные блоки (mode 1) и связи (mode 1) для IDE не существуют
    links = [l for l in all_links if l.get('mode') != 1]
    incoming = {(l['dst_block'], l['dst_slot']): l for l in links}
    outgoing = {}
    for l in links:
        outgoing.setdefault((l['src_block'], l['src_slot']), []).append(l)
    df = (t.get('Define') or [{}])[0]
    eni_of = {b['block']: b for b in t['Blocks'] if b.get('type') == 13 and 'block' in b}
    comments = [b for b in t['Blocks'] if b.get('type') == 14]
    live = [b for b in t['Blocks'] if b.get('type') != 14 and not (b.get('mode') == 1 and b.get('sequence') == -1)]

    print('программа %s (%s), блоков %d, связей %d'
          % (d.get('name'), d.get('lang'), len(blocks), len(all_links)))
    for c in comments:
        print('  комментарий (%s,%s): %s' % (c.get('column'), c.get('line'), c.get('name')))

    print('\n--- что делает схема (в порядке sequence) ---')
    for line in statements(t, path):
        print('  ' + line)

    if show_blocks:
        print('\n--- блоки ---')
        for b in sorted(t['Blocks'], key=lambda b: b.get('sequence', 0)):
            pins = []
            for i in range(1, b.get('inp_count', 0) + 1):
                pins.append('in%d %s:%s' % (i, b.get('inp%d_name' % i, ''),
                                            TYPE_NAME.get(b.get('inp%d_type' % i))))
            for i in range(1, b.get('out_count', 0) + 1):
                pins.append('out%d %s:%s' % (i, b.get('out%d_name' % i, ''),
                                             TYPE_NAME.get(b.get('out%d_type' % i))))
            flags = ' [закомментирован]' if b.get('mode') == 1 and b.get('type') != 14 else ''
            print('  id=%-3s seq=%-3s (%3s,%3s) %-22s %-12s %s%s'
                  % (b.get('save_id'), b.get('sequence'), b.get('column'), b.get('line'),
                     b.get('name'), KIND.get(b.get('type'), b.get('type')), ' · '.join(pins), flags))

    if show_links:
        print('\n--- связи ---')
        for l in all_links:
            mark = {1: ' [закомментирована]', 2: ' [инверсия]'}.get(l.get('mode'), '')
            print('  %-26s -> %-26s %s%s' % (l['src_name'], l['dst_name'], TYPE_NAME.get(l['src_type']), mark))

    print('\n--- замечания ---')
    bad = []
    if df.get('block_count') != len(blocks):
        bad.append('Define.block_count=%s, блоков %d — лишнее IDE не покажет'
                   % (df.get('block_count'), len(blocks)))
    if df.get('track_count') != len(all_links):
        bad.append('Define.track_count=%s, связей %d' % (df.get('track_count'), len(all_links)))
    seqs = [b.get('sequence') for b in live]
    if len(set(seqs)) != len(seqs):
        bad.append('повторяющийся sequence — код на ST исказится, сборка упадёт')
    fbn = [b['name'] for b in t['Blocks'] if b.get('type') == 3]
    for n in sorted(set(fbn)):
        if fbn.count(n) > 1:
            bad.append('экземпляр ФБ %r стоит на схеме %d раза — при сохранении IDE теряет ВСЕ связи программы'
                       % (n, fbn.count(n)))
    for l in all_links:
        for end in ('src', 'dst'):
            if l[end + '_block'] not in blocks:
                bad.append('связь %s -> %s ссылается на несуществующий блок %s'
                           % (l['src_name'], l['dst_name'], l[end + '_block']))
        src_const = blocks.get(l['src_block'], {}).get('type') == 1   # у константы IDE пишет тип 0
        if l['src_type'] != l['dst_type'] and not src_const:
            bad.append('связь %s -> %s: разные типы — «Ошибка 29»' % (l['src_name'], l['dst_name']))
    for b in live:
        if b.get('type') == 4 and b.get('inp_count', 0) > 2 and b.get('args') != b.get('inp_count'):
            bad.append('оператор %r на %s входа без args — IDE при сохранении обрежет до двух входов'
                       % (b['name'], b.get('inp_count')))
        if b.get('type') in (3, 4, 15):
            for slot in range(b.get('inp_count', 0)):
                if (b['save_id'], slot) not in incoming:
                    bad.append('вход №%d блока %r не присоединён — сборка упадёт'
                               % (slot, b['name']))
        if b.get('type') == 4 and not any(k[0] == b['save_id'] for k in outgoing):
            bad.append('выход оператора %r не присоединён — «проверить» даёт ошибку' % b['name'])
        # связь, пусть и закомментированная, блок «подключает» — код на ST выводится
        if b.get('type') == 0 and not any(b['save_id'] in (l['src_block'], l['dst_block']) for l in all_links):
            bad.append('блок %r ни к чему не подключён — код на ST не выведется'
                       % b['name'])
    # цикл по связям — IDE падает на «Вывести код на ST»
    srcs = {}
    for l in links:
        srcs.setdefault(l['dst_block'], []).append(l['src_block'])
    state = {}
    def cyc(x):
        if state.get(x) == 1:
            return True
        if state.get(x) == 2:
            return False
        state[x] = 1
        r = any(cyc(y) for y in srcs.get(x, []))
        state[x] = 2
        return r
    if any(cyc(b['save_id']) for b in live):
        bad.append('в схеме цикл по связям — IDE падает при генерации кода ST')
    else:
        bad += order_remarks(t['Blocks'], all_links)
    cols, lines = df.get('column_max', 500), df.get('line_max', 500)
    for b in t['Blocks']:
        if b.get('type') != 14 and (b.get('column', 0) < 0 or b.get('line', 0) < 0
                                    or b.get('column', 0) >= cols or b.get('line', 0) >= lines):
            bad.append('блок %r (%s,%s) вне поля %dx%d — в коде есть, на экране не виден'
                       % (b.get('name'), b.get('column'), b.get('line'), cols, lines))
    print('  ок' if not bad else '\n'.join('  - ' + x for x in bad))
    return bad


if __name__ == '__main__':
    argv = sys.argv[1:]
    if '--check-st' in argv:
        i = argv.index('--check-st')
        text = open(argv[i + 1], encoding='utf-8-sig').read()
        prog = [a for j, a in enumerate(argv) if not a.startswith('--') and j != i + 1][0]
        res = check_st(prog, text)
        print('%s: %s' % (prog, 'код IDE совпадает со схемой в файле (%d операторов)' % len(statements(load(prog)[1], prog))
                          if not res else 'РАСХОЖДЕНИЯ:'))
        for r in res:
            print('  -', r)
        raise SystemExit(1 if res else 0)
    args = [a for a in argv if not a.startswith('--')]
    if not args:
        print(__doc__)
        raise SystemExit(1)
    dump(args[0], '--blocks' in argv, '--links' in argv)
