# -*- coding: utf-8 -*-
"""Сборка FBD-схемы Unimod PRO 2 записью prog.json (без мыши).

Проверено 2026-09-12 на версии 2.3.43.15: схема, записанная этим модулем,
открывается редактором, рисуется, даёт код на ST и собирается.

    from fbd_gen import Scheme
    s = Scheme(dict_csv='tasks/main/logic/prog.csv')   # словарь — для проверки имён
    s.chain('sum_real', '+', ['a_real', 'b_real'], line=5)
    s.save('tasks/main/logic/prog.json')               # проверит и запишет

Главное правило: IDE молча выбрасывает всё, что не смогла разобрать — блок без
обязательного поля, связь на несуществующий блок, неизвестный type. Ошибки не
показываются нигде, поэтому save() сначала валидирует, а после открытия проекта
схему надо сверить: «Сборка → Редактор → Вывести код на ST».
"""
import json, os, re

# код типа вывода = uid_type - 1
# буквы типов в словаре: BYTE — K, DOUBLE — N (проверено 2026-09-18 созданием
# переменных в редакторе словаря; Y и D роняют IDE при импорте)
TYPE = {'B': 0, 'I': 1, 'R': 2, 'T': 3, 'M': 4, 'K': 5, 'N': 6}
TYPE_NAME = {0: 'BOOL', 1: 'INT', 2: 'REAL', 3: 'TIMER', 4: 'MESSAGE',
             5: 'BYTE', 6: 'DOUBLE', -1: 'любой'}

# коды type блока
T_VAR, T_CONST, T_STRUCT_F, T_FB, T_OP = 0, 1, 2, 3, 4
T_BUS, T_COIL, T_CONTACT, T_LABEL, T_JUMP = 5, 7, 8, 9, 10
T_STRUCT, T_ENI, T_COMMENT, T_FUNC, T_CHILD = 12, 13, 14, 15, 16
KNOWN_TYPES = (0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 12, 13, 14, 15, 16)

# mode у связи: 0 — обычная, 1 — закомментирована (серая, как будто её нет),
# 2 — инвертирована (NOT над значением, кружок у приёмника).
# mode у блока: 4 — из словаря, 0 — встроенный, 1 — блок закомментирован (sequence -1).
LINK_NORMAL, LINK_COMMENTED, LINK_INVERTED = 0, 1, 2

# Стандарт расположения (клетки поля): каждый источник стоит на строке своего
# входа, результат — на строке выхода, поэтому все провода прямые. Строка
# вывода переменной и k-го вывода оператора/ФБ совпадают, если line равны.
COL_SRC, COL_OP, COL_DST = 2, 20, 34
ROW_STEP = 5            # шаг между цепочками по строкам
BAND_STEP = 43          # шаг между вертикальными полосами
# Раскладка выражений (Scheme.expr / fb_call): источники в колонке column,
# операторы уровнями правее, результат справа. Для одного уровня это ровно
# 2 / 20 / 34 стандарта.
EXPR_SRC_GAP = 18       # от колонки источников до первого (самого глубокого) уровня операторов
EXPR_OP_STEP = 12       # между уровнями операторов
EXPR_RES_GAP = 14       # от последнего оператора или ФБ до результата
LETTER = {v: k for k, v in TYPE.items()}
# строк заголовка над первым выводом (у переменной и константы заголовка нет)
TITLE_ROWS = {0: 0, 1: 0, 2: 1, 3: 1, 4: 1, 5: 0, 7: 0, 8: 0, 9: 0, 10: 0, 12: 1, 13: 0, 15: 1, 16: 1}
CMP_OPS = {'=', '<>', '<', '<=', '>', '>='}
CONV_LETTER = {'BOOL': 'B', 'INT': 'I', 'REAL': 'R', 'TIME': 'T', 'STRING': 'M', 'BYTE': 'Y', 'DOUBLE': 'D'}


# ---------- системная библиотека ФБ ----------
# Описания всех системных ФБ лежат в библиотеке IDE:
#   %APPDATA%\TREI\UnimodPRO2\library\types\types.json -> sys_struct_defs[]
# запись lib_struct_<ФБ>: programs[0].inputs/outputs — выводы метода,
# tags[] — поля (uid_type, attributes.inout 1 вход / 2 выход, hidden у служебных).
LIB_TYPES = os.path.expandvars(r'%APPDATA%\TREI\UnimodPRO2\library\types\types.json')
UID_LETTER = {'1': 'B', '2': 'I', '3': 'R', '4': 'T', '5': 'M', '6': 'K', '7': 'N'}
_CATALOG = None


def fb_catalog(path=LIB_TYPES):
    """{имя ФБ: {'comment', 'method', 'inputs': [(вывод, буква)], 'outputs': [...],
    'fields': [(поле, буква, inout, комментарий)]}} из библиотеки IDE (~1 с)."""
    global _CATALOG
    if _CATALOG is not None:
        return _CATALOG
    d = json.load(open(path, encoding='utf-8'))
    cat = {}
    for sd in d.get('sys_struct_defs', []):
        name = sd.get('name', '')
        if not name.startswith('lib_struct_') or not sd.get('programs'):
            continue
        tags = {t['name']: t for t in sd.get('tags', [])}
        pr = sd['programs'][0]
        letter = lambda n: UID_LETTER.get(tags[n]['uid_type'], '?') if n in tags else '?'
        cat[name[11:]] = {
            'comment': sd.get('comment', ''),
            'method': pr.get('name'),
            'inputs': [(n, letter(n)) for n in pr.get('inputs', [])],
            'outputs': [(n, letter(n)) for n in pr.get('outputs', [])],
            'fields': [(t['name'], UID_LETTER.get(t['uid_type'], '?'), t['attributes'].get('inout', 0),
                        t.get('comment', '')) for t in sd.get('tags', []) if not t.get('hidden')],
        }
    _CATALOG = cat
    return cat


FB_LIBRARY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fb_library.json')
_LIBRARY = None


def fb_info(name=None, path=FB_LIBRARY):
    """Что известно про системный ФБ: назначение, семейство, нужен ли контроллер,
    страница руководства, вердикт сборки и проверки в эмуляции — плюс выводы из
    библиотеки IDE. Без имени возвращает весь каталог {имя: сведения}.

    Сведения из руководства и опытов лежат в assets/fb_library.json, выводы и их
    комментарии берутся в рантайме из types.json (fb_catalog)."""
    global _LIBRARY
    if _LIBRARY is None:
        try:
            _LIBRARY = json.load(open(path, encoding='utf-8'))
        except (OSError, ValueError):
            _LIBRARY = {}
    cat = fb_catalog()
    if name is None:
        return {k: fb_info(k) for k in cat}
    d = dict(_LIBRARY.get(name, {}))
    fb = cat.get(name)
    if fb:
        d.update({'comment': fb['comment'], 'method': fb['method'],
                  'inputs': fb['inputs'], 'outputs': fb['outputs'], 'fields': fb['fields']})
    return d


def fb_find(text):
    """Поиск блока по словам в назначении и комментарии: fb_find('гистерезис')."""
    text = text.lower()
    out = []
    for name, d in fb_info().items():
        hay = ' '.join(str(d.get(k, '')) for k in ('purpose', 'comment', 'family', 'emul')).lower()
        if text in hay or text in name.lower():
            out.append((name, d.get('purpose') or d.get('comment', '')))
    return sorted(out)


def struct_catalog(root):
    """Структуры проекта из types/structs.json:
    {имя: {'fields': [(поле, буква, inout)], 'methods': [имя метода]}}.
    inout 1 — поле-вход (идёт во входы блока метода), 2 — выход."""
    path = os.path.join(root, 'types', 'structs.json')
    if not os.path.exists(path):
        return {}
    cat = {}
    for sd in json.load(open(path, encoding='utf-8')).get('struct_defs', []):
        cat[sd['name']] = {
            'fields': [(t['name'], UID_LETTER.get(t.get('uid_type'), '?'), t.get('attributes', {}).get('inout', 0))
                       for t in sd.get('tags', [])],
            'methods': [pr.get('name') for pr in sd.get('programs', [])],
        }
    return cat


def func_catalog(root):
    """Функции проекта из functions/functions.json:
    {имя: {'inputs': [(параметр, буква)], 'out': буква, 'comment': …}}.
    Тег с именем самой функции (inout 2) — возвращаемое значение, остальные
    (inout 1) — параметры в порядке объявления."""
    path = os.path.join(root, 'functions', 'functions.json')
    if not os.path.exists(path):
        return {}
    cat = {}
    for pr in json.load(open(path, encoding='utf-8')).get('programs', []):
        name = pr.get('name')
        ins, out = [], None
        for t in pr.get('tags', []):
            letter = UID_LETTER.get(t.get('uid_type'), '?')
            if t['name'] == name:
                out = letter
            elif t.get('attributes', {}).get('inout') == 1:
                ins.append((t['name'], letter))
        cat[name] = {'inputs': ins, 'out': out, 'comment': pr.get('comment', '')}
    return cat


def instance_csv_rows(inst, fbname, comment=None):
    """Строки словаря (для <программа>.import.csv) под экземпляр системного ФБ."""
    fb = fb_catalog()[fbname]
    rows = ['%s;U;;%s;%d;;0;;false;0;;;;;;false;;;;;%s'
            % (inst, fbname, len(fb['fields']), comment if comment is not None else fb['comment'])]
    for n, t, inout, com in fb['fields']:
        rows.append('%s.%s;%s;;;;0;%d;;false;0;0;0;;;;false;0;0;0; ;%s' % (inst, n, t, inout, com))
    return rows


ST_WORDS = {'IF', 'THEN', 'ELSE', 'ELSIF', 'END_IF', 'CASE', 'OF', 'END_CASE', 'FOR', 'TO', 'BY', 'DO',
            'END_FOR', 'WHILE', 'END_WHILE', 'REPEAT', 'UNTIL', 'END_REPEAT', 'EXIT', 'RETURN',
            'AND', 'OR', 'XOR', 'NOT', 'MOD', 'TRUE', 'FALSE', 'VAR', 'END_VAR'}
LETTERS_OK = ('B', 'I', 'R', 'T', 'M', 'K', 'N')   # K — байт, N — дв.точности; Y и D роняют IDE


def var_csv_row(name, t, value='0', comment=''):
    """Строка словаря для <программа>.import.csv с проверкой имени и типа.
    Имя, совпадающее с системным ФБ (TON, CRC, …) без учёта регистра, импорт
    молча пропускает — переменной просто не будет (проверено 2026-09-13)."""
    if t not in LETTERS_OK:
        raise SchemeError('буква типа %r не проверена: с неизвестной буквой IDE падает при открытии проекта' % t)
    up = name.upper()
    if up in ST_WORDS:
        raise SchemeError('имя %r — служебное слово ST' % name)
    try:
        fbs = {k.upper() for k in fb_catalog()}
    except (OSError, ValueError):
        fbs = set()
    if up in fbs:
        raise SchemeError('имя %r совпадает с системным ФБ — импорт словаря молча пропустит переменную' % name)
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name):
        raise SchemeError('имя %r: только латиница, цифры и подчёркивание, не с цифры' % name)
    return '%s;%s;;;;%s;0;;false;0;0;0;;;;false;0;0;0; ;%s' % (name, t, value, comment)


def block_box(b):
    """Прямоугольник блока в клетках (x1, y1, x2, y2) — оценка по длине подписей.
    Замерено на экране (Scale=2): переменная «flag1» 3 клетки, «copy_real» 5,
    «local_var_0001» 8; оператор «:=» 5, «TON» 5, «blink1.BLINK» 7, «GET_CRC_FB» 8.
    Высота: переменная и константа — строка line, оператор и ФБ — заголовок над line
    и по строке на вывод. Оценка грубая (±1 клетка у длинных имён выводов)."""
    t = b.get('type')
    name = str(b.get('name', ''))
    if t in (T_VAR, T_CONST, T_COIL, T_CONTACT):
        w = max(3, -(-len(name) // 2) + 1)
        return (b['column'], b['line'] - 0.5, b['column'] + w, b['line'] + 0.5)
    if t == T_COMMENT:
        return (b['column'], b['line'] - 0.5, b['column'] + max(4, len(name) // 2 + 1), b['line'] + 0.5)
    ni, no = b.get('inp_count', 0), b.get('out_count', 0)
    li = max([len(str(b.get('inp%d_name' % i, ''))) for i in range(1, ni + 1)] + [0])
    lo = max([len(str(b.get('out%d_name' % i, ''))) for i in range(1, no + 1)] + [0])
    # у ФБ с автоматическим именем экземпляра (_TON_1) в заголовке только имя ФБ, у своих (cnt1) — полностью
    title = name.split('.')[-1] if (t == T_FB and name.startswith('_')) else name
    w = max(5, -(-len(title) // 2) + 1, -(-(li + lo) // 2) + 2)
    rows = max(ni, no, 1)
    top = b['line'] - (0.5 if t == T_ENI else 1.5)
    return (b['column'], top, b['column'] + w, b['line'] + rows - 0.5)


class SchemeError(Exception):
    pass


def _live(blocks):
    return [b for b in blocks if b.get('type') != T_COMMENT and b.get('mode') != 1 and 'save_id' in b]


def ide_order(blocks, links):
    """Порядок выполнения, который IDE назначает после ЛЮБОЙ правки схемы мышью.
    Проверено 2026-09-14 номер в номер на схемах, перенумерованных IDE: блоки-результаты
    (без исходящих связей) идут по ВЕРХНЕМУ КРАЮ блока — у переменной и константы это
    line, у оператора, ФБ, функции строкой выше (заголовок), — при равенстве по column;
    перед каждым результатом — его источники обходом в глубину по номерам входов, у ФБ
    после обычных входов — eni/eno. Положение источников значения не имеет. -> save_id."""
    live = _live(blocks)
    by_id = {b['save_id']: b for b in live}
    srcs, has_out = {}, set()
    for l in links:
        if l.get('mode') == LINK_COMMENTED or l['src_block'] not in by_id or l['dst_block'] not in by_id:
            continue
        srcs.setdefault(l['dst_block'], []).append((l['dst_slot'], l['src_block']))
        has_out.add(l['src_block'])
    eni_of = {b['block']: b['save_id'] for b in live if b.get('type') == T_ENI and b.get('block') in by_id}
    order, state = [], {}

    def visit(bid, path):
        if state.get(bid) == 2:
            return
        if state.get(bid) == 1:
            raise SchemeError('в схеме цикл по связям (IDE падает на «Вывести код на ST»): %s'
                              % [by_id[x]['name'] for x in path])
        state[bid] = 1
        for _, sb in sorted(srcs.get(bid, [])):
            visit(sb, path + [sb])
        if bid in eni_of:
            visit(eni_of[bid], path + [eni_of[bid]])
        state[bid] = 2
        order.append(bid)

    top = lambda b: (b.get('line', 0) - TITLE_ROWS.get(b.get('type'), 1), b.get('column', 0))
    sinks = [b for b in live if b['save_id'] not in has_out and b.get('type') != T_ENI]
    for b in sorted(sinks, key=top):
        visit(b['save_id'], [b['save_id']])
    for b in sorted(live, key=lambda b: (b.get('line', 0), b.get('column', 0))):
        visit(b['save_id'], [b['save_id']])      # висящее без результата (eni без ФБ и т.п.)
    return order


def order_remarks(blocks, links, limit=5):
    """Предупреждения о порядке выполнения (не ошибки сборки):
    1) порядок в файле не совпадает с тем, что IDE назначит после первой правки мышью;
    2) цепочка читает переменную раньше, чем её пишет другая цепочка этой схемы
       (значение прошлого цикла)."""
    live = _live(blocks)
    by_id = {b['save_id']: b for b in live}
    seq = {b['save_id']: b.get('sequence', -1) for b in live}
    lk = [l for l in links if l.get('mode') != LINK_COMMENTED and l['src_block'] in by_id and l['dst_block'] in by_id]
    outs, ins = {}, {}
    for l in lk:
        outs.setdefault(l['src_block'], []).append(l['dst_block'])
        ins.setdefault(l['dst_block'], []).append(l['src_block'])
    sinks = [i for i in by_id if i not in outs and by_id[i].get('type') != T_ENI]
    res = []
    try:
        ide = ide_order(blocks, links)
    except SchemeError as e:
        return [str(e)]
    rank = {i: n for n, i in enumerate(ide)}
    now = sorted(sinks, key=lambda i: seq[i])
    want = sorted(sinks, key=lambda i: rank[i])
    if now != want:
        swaps = []
        for a in range(len(now)):
            for b in range(a + 1, len(now)):
                if rank[now[a]] > rank[now[b]]:
                    swaps.append('«%s» (%s,%s) станет выполняться раньше «%s» (%s,%s)' % (
                        by_id[now[b]]['name'], by_id[now[b]]['column'], by_id[now[b]]['line'],
                        by_id[now[a]]['name'], by_id[now[a]]['column'], by_id[now[a]]['line']))
                    if len(swaps) >= limit:
                        break
            if len(swaps) >= limit:
                break
        res.append('порядок в файле не тот, что IDE назначит после первой правки мышью (по положению '
                   'результатов сверху вниз): ' + '; '.join(swaps))

    def sink_of(i, seen=()):
        if i not in outs or i in seen:
            return i
        return min((sink_of(d, seen + (i,)) for d in outs[i]), key=lambda x: seq.get(x, 0))

    writers = {}
    for i, b in by_id.items():
        if b.get('type') == T_VAR and i in ins:
            writers.setdefault((b['name'], b.get('dict', 0)), []).append(sink_of(i))
    n = 0
    for i, b in by_id.items():
        if b.get('type') != T_VAR or i in ins or i not in outs:
            continue
        r = sink_of(i)
        for w in writers.get((b['name'], b.get('dict', 0)), []):
            if w != r and seq.get(r, -1) < seq.get(w, -1):
                res.append('«%s» читает %s раньше, чем её пишет цепочка «%s» — значение прошлого цикла; '
                           'поставить читающую цепочку ниже' % (by_id[r]['name'], b['name'], by_id[w]['name']))
                n += 1
        if n >= limit:
            break
    return res


def _project_root(path):
    d = os.path.dirname(os.path.abspath(path))
    for _ in range(6):
        if os.path.exists(os.path.join(d, 'project.uprj')):
            return d
        d = os.path.dirname(d)
    return None


# ---------- операнды выражений ----------
class K:
    """Константа в выражении: K('90.0', 'R'). Кортеж ('90.0', 'R') — то же самое."""
    def __init__(self, value, t):
        self.value, self.t = str(value), t


class Pin:
    """Выход уже поставленного блока как операнд: Pin(ton, 'Q'), Pin(op_block).
    Нового блока не создаёт — провод идёт прямо от вывода."""
    def __init__(self, block, out=0):
        self.block, self.out = block, out


class Inv:
    """Инвертированная связь к родителю (mode 2, в коде NOT): Inv('ack') или '!ack'."""
    def __init__(self, node):
        self.node = node


class Op:
    """Оператор с явными типами выводов: Op('INT_TO_REAL', 'cnt', in_t='I', out_t='R').
    Обычно хватает кортежа ('AND', 'a', 'b')."""
    def __init__(self, name, *args, in_t=None, out_t=None):
        self.name, self.args, self.in_t, self.out_t = name, list(args), in_t, out_t


class Scheme:
    def __init__(self, dict_csv=None, global_csv=None):
        self.blocks = []
        self.links = []
        self.vars = {}          # имя -> буква типа (из словаря программы)
        self.instances = {}     # имя экземпляра ФБ -> имя ФБ
        self.globals = {}       # имя -> буква типа (глобальный словарь, tags/global.csv)
        self.next_line = 3      # строка для следующего expr()/fb_call()
        self.next_column = COL_SRC
        self.columns, self.lines = 500, 500     # размер поля (Define): IDE принимает и 1000, и 5000
        self.root = None        # каталог проекта — для глобального словаря и чужих программ
        self.progdir = None     # каталог программы — для словарей дочерних программ
        self._other = {}        # программа -> {имя: буква} для ссылок «программа.переменная»
        if dict_csv:
            self.load_dict(dict_csv)
            self.progdir = os.path.dirname(os.path.abspath(dict_csv))
            root = self.root = _project_root(dict_csv)
            if global_csv is None and root and os.path.exists(os.path.join(root, 'tags', 'global.csv')):
                global_csv = os.path.join(root, 'tags', 'global.csv')
        if global_csv:
            self.load_dict(global_csv, glob=True)

    # ---------- словарь программы ----------
    def load_dict(self, path, glob=False):
        """Читает prog.csv программы (UTF-8): переменные и экземпляры ФБ.
        glob=True — tags/global.csv (зеркало глобального словаря)."""
        with open(path, encoding='utf-8') as f:
            f.readline()
            for line in f:
                c = line.rstrip('\r\n').split(';')
                if len(c) < 5 or not c[0]:
                    continue
                name, t, lib = c[0], c[1], c[3]
                if glob:
                    if t != 'U' and '.' not in name:
                        self.globals[name] = t
                elif t == 'U':
                    self.instances[name] = lib
                else:
                    self.vars[name] = t
        return self

    def other_var(self, name):
        """Тип переменной другой программы по ссылке «программа.переменная» (или None).
        Проверено 2026-09-14: блок переменной с именем big60.any_alm (dict 0, mode 4) в
        программе big400 собирается и в эмуляции читает переменную big60. Без префикса
        чужая переменная даёт «Ошибка 19»."""
        if '.' not in name or not self.root:
            return None
        prog, var = name.split('.', 1)
        if prog not in self._other:
            self._other[prog] = {}
            tasks = os.path.join(self.root, 'tasks')
            for task in (os.listdir(tasks) if os.path.isdir(tasks) else []):
                csv = os.path.join(tasks, task, prog, 'prog.csv')
                if os.path.exists(csv):
                    self._other[prog] = Scheme().load_dict(csv).vars
                    break
        return self._other[prog].get(var)

    def elem_type(self, name):
        """Тип элемента массива с индексом-переменной: 'abuf[idx]', 'g_mat[i,j]'.
        Проверяет, что массив есть в словаре (по строке нулевого элемента), а каждый
        индекс — либо число, либо целая переменная. -> буква типа или None."""
        m = re.match(r'^([A-Za-z_]\w*)\[([^\]]+)\]$', name or '')
        if not m:
            return None
        base, idx = m.group(1), m.group(2)
        zero = '%s[%s]' % (base, ','.join(['0'] * len(idx.split(','))))
        t = self.vars.get(zero) or self.globals.get(zero)
        if not t:
            return None
        for part in idx.split(','):
            part = part.strip()
            if part.isdigit():
                continue
            it = self.vars.get(part) or self.globals.get(part)
            if it != 'I':
                raise SchemeError('индекс %r в %r — не целая переменная словаря' % (part, name))
        return t

    def vtype(self, name):
        if name in self.vars:
            return self.vars[name]
        if name in self.globals:
            return self.globals[name]
        t = self.other_var(name) or self.elem_type(name)
        if t:
            return t
        raise SchemeError('переменной %r нет ни в словаре программы, ни в глобальном, ни в другой программе '
                          '(«программа.переменная»)' % name)

    # ---------- блоки ----------
    def _add(self, **kw):
        kw['save_id'] = max([b['save_id'] for b in self.blocks] + [-1]) + 1
        kw.setdefault('_new', True)
        self.blocks.append(kw)
        return kw

    # ---------- правка готовой (в том числе чужой) схемы ----------
    @classmethod
    def load(cls, prog_json, dict_csv=None):
        """Загрузить схему из prog.json как есть — все поля блоков сохраняются
        (args, block, slots, …). Словарь по умолчанию — prog.csv рядом."""
        if dict_csv is None:
            cand = os.path.join(os.path.dirname(prog_json), 'prog.csv')
            dict_csv = cand if os.path.exists(cand) else None
        s = cls(dict_csv=dict_csv)
        t = json.load(open(prog_json, encoding='utf-8')).get('text', {})
        if 'Blocks' not in t:
            raise SchemeError('%s — не FBD-схема (в text нет Blocks)' % prog_json)
        s.blocks = t['Blocks']
        s.links = t.get('Links', [])
        df = (t.get('Define') or [{}])[0]
        s.columns, s.lines = df.get('column_max', 500), df.get('line_max', 500)
        return s

    def find(self, name=None, column=None, line=None, type=None):
        """Блоки по имени и/или клетке. save_id для поиска не годится: IDE
        перенумеровывает его при каждом сохранении."""
        return [b for b in self.blocks
                if (name is None or b.get('name') == name) and (column is None or b.get('column') == column)
                and (line is None or b.get('line') == line) and (type is None or b.get('type') == type)]

    def one(self, name=None, column=None, line=None, type=None):
        hit = self.find(name, column, line, type)
        if len(hit) != 1:
            raise SchemeError('ожидался один блок (name=%r column=%r line=%r type=%r), найдено %d'
                              % (name, column, line, type, len(hit)))
        return hit[0]

    def links_of(self, block, into=None, out=None):
        """Связи блока: into=True — входящие, out=True — исходящие, без флагов — все."""
        i = block['save_id']
        return [l for l in self.links
                if (into is None and out is None and i in (l['src_block'], l['dst_block']))
                or (into and l['dst_block'] == i) or (out and l['src_block'] == i)]

    def source(self, block, slot=0):
        """Связь, входящая во вход slot блока (или None)."""
        for l in self.links:
            if l['dst_block'] == block['save_id'] and l['dst_slot'] == slot:
                return l
        return None

    def unlink(self, link):
        self.links.remove(link)

    def delete(self, block):
        """Удалить блок со всеми его связями (и eni/eno этого ФБ). Как делает IDE."""
        victims = [block] + [b for b in self.blocks if b.get('type') == T_ENI and b.get('block') == block['save_id']]
        ids = {b['save_id'] for b in victims}
        self.links = [l for l in self.links if l['src_block'] not in ids and l['dst_block'] not in ids]
        self.blocks = [b for b in self.blocks if b['save_id'] not in ids]
        return self

    def move(self, block, column=None, line=None, dcol=0, dline=0):
        """Переставить блок; трассы IDE проложит сама. eni/eno ФБ едет вместе с ним."""
        nc = column if column is not None else block['column'] + dcol
        nl = line if line is not None else block['line'] + dline
        for e in self.blocks:
            if e.get('type') == T_ENI and e.get('block') == block['save_id']:
                e['column'] += nc - block['column']; e['line'] += nl - block['line']
        block['column'], block['line'] = nc, nl
        return block

    def rename(self, block, new_name, t=None):
        """Сменить переменную в блоке (тип должен совпасть) и имена концов связей."""
        if block.get('type') != T_VAR:
            raise SchemeError('переименовать можно только блок переменной')
        nt = t or self.vars.get(new_name)
        if nt and TYPE[nt] != block.get('out1_type'):
            raise SchemeError('тип %r (%s) не совпадает с блоком %r' % (new_name, nt, block['name']))
        block['name'] = new_name
        for l in self.links:
            if l['src_block'] == block['save_id']:
                l['src_name'] = self.pin_name(block, l['src_slot'], True)
            if l['dst_block'] == block['save_id']:
                l['dst_name'] = self.pin_name(block, l['dst_slot'], False)
        return block

    def insert(self, link, block, in_slot=0, out_slot=0, t=None):
        """Врезать блок в связь src -> dst: src -> block.in_slot, block.out_slot -> dst.
        Инверсия связи (mode 2) остаётся на участке к приёмнику."""
        src = [b for b in self.blocks if b['save_id'] == link['src_block']][0]
        dst = [b for b in self.blocks if b['save_id'] == link['dst_block']][0]
        c = link['src_type'] if t is None else (TYPE[t] if isinstance(t, str) else t)
        mode = link.get('mode', 0)
        self.links.remove(link)
        self.link(src, block, c, src_slot=link['src_slot'], dst_slot=in_slot)
        tail = self.link(block, dst, link['dst_type'] if t is None else c, src_slot=out_slot, dst_slot=link['dst_slot'])
        tail['mode'] = mode
        return block

    def compact_ids(self):
        """save_id подряд с нуля в порядке списка блоков; связи и eni/eno пересчитываются."""
        remap = {b['save_id']: n for n, b in enumerate(self.blocks)}
        for b in self.blocks:
            b['save_id'] = remap[b['save_id']]
            if b.get('type') == T_ENI and 'block' in b and b['block'] in remap:
                b['block'] = remap[b['block']]
        self.links = [l for l in self.links if l['src_block'] in remap and l['dst_block'] in remap]
        for l in self.links:
            l['src_block'] = remap[l['src_block']]
            l['dst_block'] = remap[l['dst_block']]
        return self

    def resequence(self):
        """Порядок для правленой схемы: у старых блоков сохраняется прежний
        относительный порядок (перенумеровывать чужую схему «для красоты» —
        значит менять её логику), новые встают сразу после своих источников.
        Номера сжимаются в 0..N-1."""
        live = [b for b in self.blocks if b['type'] != T_COMMENT and b.get('mode') != 1]
        key = {}
        for b in live:
            if b.get('sequence') is not None and b.get('sequence', -1) >= 0 and not b.get('_new'):
                key[b['save_id']] = float(b['sequence'])
        by_id = {b['save_id']: b for b in live}
        srcs, dsts = {}, {}
        for l in self.links:
            if l['src_block'] in by_id and l['dst_block'] in by_id and l.get('mode') != 1:
                srcs.setdefault(l['dst_block'], []).append(l['src_block'])
                dsts.setdefault(l['src_block'], []).append(l['dst_block'])
        # ключ нового блока: чуть после самого позднего источника (или перед приёмником)
        for _ in range(len(live) + 1):
            changed = False
            for b in live:
                i = b['save_id']
                if i in key and not b.get('_new'):
                    continue
                ks = [key[x] for x in srcs.get(i, []) if x in key]
                kd = [key[x] for x in dsts.get(i, []) if x in key]
                if ks:
                    k = max(ks) + 0.001
                elif kd:
                    k = min(kd) - 0.001
                else:
                    k = 1e9 + b['line'] * 1000 + b['column']
                if key.get(i) != k:
                    key[i] = k; changed = True
            if not changed:
                break
        # топологическая сортировка с приоритетом по ключу
        indeg = {i: len([x for x in srcs.get(i, []) if x in by_id]) for i in by_id}
        ready = sorted([i for i, d in indeg.items() if d == 0], key=lambda i: key[i])
        order = []
        while ready:
            i = ready.pop(0)
            order.append(i)
            for d in dsts.get(i, []):
                indeg[d] -= 1
                if indeg[d] == 0:
                    ready.append(d)
            ready.sort(key=lambda i: key[i])
        if len(order) != len(by_id):
            raise SchemeError('в схеме цикл по связям (IDE падает на «Вывести код на ST»)')
        for n, i in enumerate(order):
            by_id[i]['sequence'] = n
            by_id[i].pop('_new', None)
        for b in self.blocks:
            if b not in live:
                b['sequence'] = -1
        return self

    def var(self, name, column, line, t=None, glob=None):
        """Блок переменной. Локальная (словарь программы): dict 0, mode 4.
        Глобальная (глобальный словарь): dict 1, mode 0 — так её пишет IDE, проверено
        2026-09-14. glob=None — глобальная, если имени нет в словаре программы, но
        есть в глобальном; обмен между программами идёт только через глобальные."""
        if glob is None:
            glob = name not in self.vars and name in self.globals
        t = t or (self.globals.get(name) if glob else
                  (self.vars.get(name) or self.other_var(name) or self.elem_type(name)))
        if t is None:
            raise SchemeError('не известен тип переменной %r: передай t= или словарь' % name)
        c = TYPE[t]
        return self._add(type=T_VAR, dict=1 if glob else 0, mode=0 if glob else 4, name=name,
                         column=column, line=line, inp_count=1, inp1_name='', inp1_type=c,
                         out_count=1, out1_name='', out1_type=c)

    def const(self, value, t, column, line):
        """Константа: name — литерал ST, генератор кода печатает его как есть.
        Проверено компиляцией: REAL только с точкой ('2.0', не '2' и не '2,5');
        экспонента с мантиссой ('1.0E3', не '1e3'); BOOL — TRUE/FALSE, не 1/0;
        строка в апострофах ("'abc'"); отрицательное число на входе оператора —
        в скобках ('(-1.5)'), иначе «a + -1.5» не компилируется."""
        value = str(value)
        if t == 'R':
            if ',' in value or not any(ch in value for ch in '.'):
                raise SchemeError('REAL-константа %r: нужна точка (2.0), запятая и целая запись не компилируются' % value)
            if re.match(r'^-?\d+[eE]', value.strip('()')):
                raise SchemeError('REAL-константа %r: экспонента пишется с мантиссой: 1.0E3' % value)
        if t == 'B' and value.upper() not in ('TRUE', 'FALSE'):
            raise SchemeError('BOOL-константа %r: только TRUE или FALSE' % value)
        if t == 'K' and not value.lower().startswith('b#'):
            raise SchemeError('BYTE-константа пишется как b#7 (проверено: так её пишет IDE), а не %r' % value)
        if t == 'N' and not value.lower().startswith('d#'):
            raise SchemeError('DOUBLE-константа пишется как d#1.5, а не %r' % value)
        if value.startswith('-'):
            value = '(%s)' % value
        return self._add(type=T_CONST, subtype=TYPE[t], dict=3, mode=0, name=value,
                         column=column, line=line,
                         inp_count=0, out_count=1, out1_name='', out1_type=TYPE[t])

    def op(self, name, n_in, column, line, in_t=None, out_t=None):
        """Встроенный оператор. Опознаётся ПО ИМЕНИ, имя — это ST-токен:
        := + - * / MOD · AND OR XOR NOT · = <> < <= > >= · SQRT ABS …
        subtype: 0 — один вход, 1 — два и больше. Оператор на 3+ входа (AND, OR, +, *)
        хранит число входов в поле args; без args IDE при первом сохранении обрежет
        оператор до двух входов и молча выбросит лишние связи.
        Преобразования типов — <ИЗ>_TO_<В>: INT_TO_REAL, REAL_TO_INT, REAL_TO_BOOL…
        (REAL(x), INT(x) не компилируются); передай in_t/out_t."""
        b = self._add(type=T_OP, subtype=(1 if n_in > 1 else 0), dict=3, mode=0,
                      name=name, column=column, line=line, inp_count=n_in,
                      out_count=1, out1_name='out', out1_type=-1)
        for i in range(1, n_in + 1):
            b['inp%d_name' % i] = 'in%d' % i
            b['inp%d_type' % i] = TYPE[in_t] if in_t else -1
        if n_in > 2:
            b['args'] = n_in
        if out_t:
            b['out1_type'] = TYPE[out_t]
        return b

    def eni(self, fb_block):
        """Вход разрешения eni / выход eno у ФБ: отдельный блок type 13 над ФБ
        (line ФБ − 2). Вызов ФБ оборачивается в «if (eni) then … end_if»."""
        return self._add(type=T_ENI, subtype=0, dict=0, mode=4, block=fb_block['save_id'],
                         name=fb_block['name'], column=fb_block['column'], line=fb_block['line'] - 2,
                         inp_count=1, inp1_name='eni', inp1_type=0,
                         out_count=1, out1_name='eno', out1_type=0)

    # ---------- LD: шина, контакт, виток; метка и прыжок ----------
    BUS_SIDE = {'left': 0, 'right': 1}
    CONTACT_KIND = {'direct': 0, 'inv': 1, 'N': 2, 'P': 3}
    COIL_KIND = {'direct': 0, 'inv': 1, 'N': 2, 'P': 3, 'R': 4, 'S': 5}

    def bus(self, side, line, column, slots=3):
        """Силовая шина LD: 'left' — 3 выхода (питание цепей), 'right' — 3 входа.
        Поле `slots` — сколько цепей к ней подключается (IDE пишет 3)."""
        if side not in self.BUS_SIDE:
            raise SchemeError('сторона шины: left или right')
        b = self._add(type=T_BUS, subtype=self.BUS_SIDE[side], dict=3, mode=0, name='',
                      column=column, line=line, slots=slots,
                      inp_count=slots if side == 'right' else 0,
                      out_count=slots if side == 'left' else 0)
        for i in range(1, slots + 1):
            b['%s%d_name' % ('inp' if side == 'right' else 'out', i)] = ''
            b['%s%d_type' % ('inp' if side == 'right' else 'out', i)] = 0
        return b

    def contact(self, name, line, column, kind='direct'):
        """Контакт LD: 'direct', 'inv', 'N' (по спаду), 'P' (по фронту).
        Имя — булевская переменная словаря; один вход и один выход BOOL."""
        t = self.vars.get(name) or self.globals.get(name)
        if t and t != 'B':
            raise SchemeError('контакт принимает только булевскую переменную, а %r — %s' % (name, t))
        return self._add(type=T_CONTACT, subtype=self.CONTACT_KIND[kind], dict=0, mode=4, name=name,
                         column=column, line=line, inp_count=1, inp1_name='', inp1_type=0,
                         out_count=1, out1_name='', out1_type=0)

    def coil(self, name, line, column, kind='direct'):
        """Виток LD: 'direct', 'inv', 'N', 'P', 'R' (сброс), 'S' (установка)."""
        t = self.vars.get(name) or self.globals.get(name)
        if t and t != 'B':
            raise SchemeError('виток принимает только булевскую переменную, а %r — %s' % (name, t))
        return self._add(type=T_COIL, subtype=self.COIL_KIND[kind], dict=0, mode=4, name=name,
                         column=column, line=line, inp_count=1, inp1_name='', inp1_type=0,
                         out_count=1, out1_name='', out1_type=0)

    def label(self, name, line, column):
        """Метка (type 9): выводов нет, имя — цель прыжка."""
        return self._add(type=T_LABEL, dict=3, mode=0, name=name, column=column, line=line,
                         inp_count=0, out_count=0)

    def jump(self, target, line, column):
        """Прыжок (type 10): один вход BOOL — условие; имя — метка или 'Return'."""
        return self._add(type=T_JUMP, dict=3, mode=0, name=target, column=column, line=line,
                         inp_count=1, inp1_name='', inp1_type=0, out_count=0)

    def comment(self, text, column, line):
        """Комментарий на поле: type 14, текст в name (перевод строки рисуется пробелом)."""
        return self._add(type=T_COMMENT, dict=3, mode=1, name=text, column=column, line=line,
                         inp_count=0, out_count=0, sequence=-1)

    def fb(self, inst, fbname, ins, outs, column, line):
        """Экземпляр ФБ: ins/outs — [(имя вывода, буква типа), ...].
        Экземпляр и его поля должны быть в словаре программы (строка Type=U)."""
        b = self._add(type=T_FB, dict=0, mode=4, name='%s.%s' % (inst, fbname),
                      column=column, line=line, inp_count=len(ins), out_count=len(outs))
        for i, (n, t) in enumerate(ins, 1):
            b['inp%d_name' % i] = n
            b['inp%d_type' % i] = TYPE[t]
        for i, (n, t) in enumerate(outs, 1):
            b['out%d_name' % i] = n
            b['out%d_type' % i] = TYPE[t]
        return b

    def fb_lib(self, inst, fbname, column, line):
        """Экземпляр системного ФБ: выводы и типы берутся из библиотеки IDE."""
        fb = fb_catalog()[fbname]
        bad = [n for n, t in fb['inputs'] + fb['outputs'] if t not in TYPE]
        if bad:
            raise SchemeError('у %s выводы нестандартного типа: %s' % (fbname, bad))
        return self.fb(inst, fb['method'], fb['inputs'], fb['outputs'], column, line)

    # ---------- связи ----------
    def pin_name(self, b, slot, is_out):
        """Имя вывода в связи: у переменной и константы — имя блока, у оператора
        и ФБ — <имя блока>.<имя вывода> (':=.in1', '_TON_1.TON.IN')."""
        key = ('out%d_name' if is_out else 'inp%d_name') % (slot + 1)
        pn = b.get(key, '')
        return b['name'] if not pn else '%s.%s' % (b['name'], pn)

    def pin_type(self, b, slot, is_out):
        return b.get(('out%d_type' if is_out else 'inp%d_type') % (slot + 1), -1)

    def link(self, src, dst, t=None, src_slot=0, dst_slot=0, invert=False):
        """Связь. У операторов тип вывода -1 («любой»), поэтому конкретный тип
        берётся со второго конца или передаётся явно. invert=True — mode 2, в коде
        NOT над значением связи (только BOOL)."""
        c = TYPE[t] if isinstance(t, str) else t
        if c is None:
            c = self.pin_type(src, src_slot, True)
            if c == -1:
                c = self.pin_type(dst, dst_slot, False)
            if c == -1:
                raise SchemeError('тип связи не выводится: укажи t=')
        self.links.append(dict(src_block=src['save_id'], src_slot=src_slot,
                               src_name=self.pin_name(src, src_slot, True), src_type=c,
                               dst_block=dst['save_id'], dst_slot=dst_slot,
                               dst_name=self.pin_name(dst, dst_slot, False), dst_type=c,
                               mode=LINK_INVERTED if invert else LINK_NORMAL))
        return self.links[-1]

    # ---------- готовая цепочка ----------
    def chain(self, result, opname, args, line, band=0, types=None):
        """result := op(args...) по стандарту расположения.
        args — имена переменных либо (значение, буква типа) для констант."""
        types = types or {}
        col = COL_SRC + band * BAND_STEP
        srcs = []
        for i, a in enumerate(args):
            if isinstance(a, tuple):
                srcs.append((self.const(a[0], a[1], col, line + i), a[1]))
            else:
                t = types.get(a) or self.vtype(a)
                srcs.append((self.var(a, col, line + i, t), t))
        o = self.op(opname, len(args), COL_OP + band * BAND_STEP, line)
        rt = types.get(result) or self.vtype(result)
        r = self.var(result, COL_DST + band * BAND_STEP, line, rt)
        for i, (sv, t) in enumerate(srcs):
            self.link(sv, o, t, dst_slot=i)
        self.link(o, r, rt)
        return o

    # ---------- выражения с автоматической раскладкой ----------
    def _node(self, tree):
        """Операнд выражения -> K / Pin / Inv / Op / имя переменной."""
        if isinstance(tree, (K, Pin, Inv, Op)):
            return tree
        if isinstance(tree, str):
            return Inv(tree[1:]) if tree.startswith('!') else tree
        if isinstance(tree, tuple) and tree:
            head = str(tree[0])
            if len(tree) == 2 and isinstance(tree[1], str) and tree[1] in TYPE and \
                    (head.upper() in ('TRUE', 'FALSE') or head[:1] in "0123456789-.('"):
                return K(tree[0], tree[1])
            return Op(head, *tree[1:])
        raise SchemeError('не понимаю операнд %r' % (tree,))

    def _depth(self, tree):
        n = self._node(tree)
        while isinstance(n, Inv):
            n = self._node(n.node)
        if isinstance(n, Op):
            return 1 + max([self._depth(a) for a in n.args] + [0])
        return 0

    def _out_slot(self, block, out):
        if isinstance(out, int):
            return out
        for i in range(1, block.get('out_count', 0) + 1):
            if block.get('out%d_name' % i) == out:
                return i - 1
        raise SchemeError('у блока %r нет выхода %r' % (block.get('name'), out))

    @staticmethod
    def _op_letter(op, letters):
        """Тип выхода оператора по типам входов; разные типы — «Ошибка 29» ещё до IDE."""
        m = re.match(r'^([A-Z]+)_TO_([A-Z]+)$', op.name)
        known = [x for x in letters if x]
        if m and m.group(1) in CONV_LETTER and m.group(2) in CONV_LETTER:
            want = CONV_LETTER[m.group(1)]
            if known and known[0] != want:
                raise SchemeError('%s получает %s — сборка даст «Ошибка 29»' % (op.name, known[0]))
            return op.out_t or CONV_LETTER[m.group(2)]
        if len(set(known)) > 1 and not op.out_t:
            # у сервисных операторов входы разных типов — норма (SETBIT(i, bit, b));
            # явный out_t означает «тип знаю сам», и проверку пропускаем
            raise SchemeError('оператор %s: входы разных типов %s — неявных преобразований нет, '
                              'сборка даст «Ошибка 29»' % (op.name, known))
        if op.out_t:
            return op.out_t
        if op.name in CMP_OPS:
            return 'B'
        return known[0] if known else None

    def _place(self, tree, row, level, depth, col0, types):
        """Ставит поддерево; -> (блок, вывод, буква типа, инверсия, занято строк)."""
        n, inv = self._node(tree), False
        while isinstance(n, Inv):
            inv, n = not inv, self._node(n.node)
        if isinstance(n, Pin):
            slot = self._out_slot(n.block, n.out)
            return n.block, slot, LETTER.get(self.pin_type(n.block, slot, True)), inv, 1
        if isinstance(n, K):
            return self.const(n.value, n.t, col0, row), 0, n.t, inv, 1
        if isinstance(n, str):
            t = types.get(n) or self.vtype(n)
            return self.var(n, col0, row, t), 0, t, inv, 1
        col = col0 + EXPR_SRC_GAP + (depth - level) * EXPR_OP_STEP
        kids, nxt = [], row
        for k, a in enumerate(n.args):
            # заголовок оператора — строкой выше его первого вывода; под предыдущим
            # соседом оставляем ещё одну пустую строку, чтобы блоки не стояли вплотную
            r = max(row + k, nxt + (2 if k and self._depth(a) > 0 else 0))
            kid = self._place(a, r, level + 1, depth, col0, types)
            kids.append(kid)
            nxt = r + kid[4]
        letter = self._op_letter(n, [kd[2] for kd in kids])
        b = self.op(n.name, len(n.args), col, row, in_t=n.in_t, out_t=n.out_t)
        # конкретные типы выводов — как их пишет сама IDE при сохранении
        known = [kd[2] for kd in kids if kd[2]]
        if known and n.in_t is None:
            for i in range(1, len(n.args) + 1):
                b['inp%d_type' % i] = TYPE[known[0]]
        if letter and n.out_t is None:
            b['out1_type'] = TYPE[letter]
        for k, (kb, ks, kl, kinv, _) in enumerate(kids):
            if kinv and kl != 'B':
                raise SchemeError('инверсия связи возможна только у BOOL, а %r — %s' % (kb['name'], kl))
            c = TYPE[kl] if kl else None
            self.link(kb, b, c if c is not None else (TYPE[letter] if letter else None),
                      src_slot=ks, dst_slot=k, invert=kinv)
        return b, 0, letter, inv, max(nxt - row, len(n.args))

    def expr(self, result, tree, line, column=COL_SRC, gap=2, types=None):
        """result := выражение, разложенное по клеткам без ручных координат.

            s.expr('hi_1', ('>', 'lvl_1', K('90.0', 'R')), line=3)
            s.expr('lat_1', ('AND', ('OR', 'alm_1', 'lat_1'), '!ack'), line=s.next_line)

        Операнды: имя переменной, '!имя' (инверсия связи), K(значение, буква) или
        ('2.0', 'R'), (оператор, операнд, ...), Op(...) с явными типами, Pin(блок, выход).
        Источники — в колонке column, операторы — уровнями правее, результат — справа.
        У каждого поддерева свои строки, поэтому блоки не накладываются, а провода от
        источников прямые. Типы проверяются сразу: смешение типов, результат не того
        типа — SchemeError. Возвращает корневой оператор; s.next_line — строка для
        следующего выражения (с отступом gap пустых строк)."""
        types = types or {}
        n = self._node(tree)
        if not isinstance(n, Op) or isinstance(n, Inv):
            tree = Op(':=', tree)
        depth = self._depth(tree)
        root, _, letter, inv, rows = self._place(tree, line, 1, depth, column, types)
        rt = types.get(result) or self.vtype(result)
        if letter and letter != rt:
            raise SchemeError('%s := выражение типа %s, а переменная типа %s — «Ошибка 29»'
                              % (result, TYPE_NAME[TYPE[letter]], TYPE_NAME[TYPE[rt]]))
        col = column + EXPR_SRC_GAP + (depth - 1) * EXPR_OP_STEP + EXPR_RES_GAP
        rv = self.var(result, col, line, rt)
        self.link(root, rv, rt)
        self.next_line = line + rows + gap
        self.next_column = int(block_box(rv)[2]) + 3
        return root

    def fb_call(self, inst, fbname, line, column=COL_SRC, ins=None, outs=None, gap=2, types=None):
        """Вызов системного ФБ с раскладкой: входы — выражения, выходы — переменные.

            ton = s.fb_call('dly_1', 'TON', line=3, ins={'IN': 'hi_1', 'PT': K('3000', 'I')},
                            outs={'Q': 'alm_1'})
            s.expr('x', ('AND', Pin(ton, 'Q'), 'en'), line=s.next_line)

        Все входы обязательны (неподключённый вход — ошибка сборки). Выход можно не
        подключать; в outs значение — имя переменной или список имён."""
        types, ins, outs = types or {}, ins or {}, outs or {}
        fb = fb_catalog()[fbname]
        in_names = [x for x, _ in fb['inputs']]
        out_names = [x for x, _ in fb['outputs']]
        miss = [x for x in in_names if x not in ins]
        extra = [x for x in list(ins) + list(outs) if x not in in_names + out_names]
        if miss or extra:
            raise SchemeError('%s %s: %s%s' % (fbname, inst, 'не подключены входы %s — сборка упадёт; ' % miss if miss else '',
                                               'нет выводов %s' % extra if extra else ''))
        depth = 1 + max([self._depth(ins[x]) for x in in_names] + [0])
        col = column + EXPR_SRC_GAP + (depth - 1) * EXPR_OP_STEP
        kids, nxt = [], line
        for k, x in enumerate(in_names):
            r = max(line + k, nxt + (2 if k and self._depth(ins[x]) > 0 else 0))
            kid = self._place(ins[x], r, 2, depth, column, types)
            kids.append(kid)
            nxt = r + kid[4]
        b = self.fb_lib(inst, fbname, col, line)
        for k, (kb, ks, kl, kinv, _) in enumerate(kids):
            want = LETTER[self.pin_type(b, k, False)]
            if kl and kl != want:
                raise SchemeError('%s.%s ждёт %s, а подано %s — «Ошибка 29»' % (inst, in_names[k], want, kl))
            self.link(kb, b, want, src_slot=ks, dst_slot=k, invert=kinv)
        for x, names in outs.items():
            slot = out_names.index(x)
            want = LETTER[self.pin_type(b, slot, True)]
            for j, v in enumerate([names] if isinstance(names, str) else names):
                vt = types.get(v) or self.vtype(v)
                if vt != want:
                    raise SchemeError('%s.%s типа %s, а %r — %s' % (inst, x, want, v, vt))
                self.link(b, self.var(v, col + EXPR_RES_GAP + 4 * j, line + slot, vt), want, src_slot=slot)
        rows = max(nxt - line, len(in_names), len(out_names))
        self.next_line = line + rows + gap
        right = [block_box(x)[2] for x in self.blocks if x.get('_new') and x['line'] >= line - 1
                 and x['line'] < line + rows and x['column'] >= column]
        self.next_column = int(max(right + [block_box(b)[2]])) + 3
        return b

    def func_call(self, fname, line, column=COL_SRC, ins=None, out=None, gap=2, types=None):
        """Вызов функции проекта: блок type 15 (dict 3, mode 0), входы — параметры
        функции, выход — её возвращаемое значение. Раскладка как у fb_call.

            s.func_call('norm_pct', line=3, ins={'x': 'sim_main.h_sim_m',
                        'xmin': K('0.0', 'R'), 'xmax': K('5.0', 'R')}, out='pct')

        Проверено 2026-09-18: даёт `pct := norm_pct( h, 0.0, 5.0 ) ;`, собирается и
        в эмуляции считает то же, что вызов этой функции из ST."""
        types, ins = types or {}, ins or {}
        fn = func_catalog(self.root or '')[fname]
        in_names = [x for x, _ in fn['inputs']]
        miss = [x for x in in_names if x not in ins]
        extra = [x for x in ins if x not in in_names]
        if miss or extra:
            raise SchemeError('функция %s: %s%s' % (fname, 'не подключены параметры %s; ' % miss if miss else '',
                                                    'нет параметров %s' % extra if extra else ''))
        depth = 1 + max([self._depth(ins[x]) for x in in_names] + [0])
        col = column + EXPR_SRC_GAP + (depth - 1) * EXPR_OP_STEP
        kids, nxt = [], line
        for k, x in enumerate(in_names):
            r = max(line + k, nxt + (2 if k and self._depth(ins[x]) > 0 else 0))
            kid = self._place(ins[x], r, 2, depth, column, types)
            kids.append(kid)
            nxt = r + kid[4]
        b = self._add(type=T_FUNC, dict=3, mode=0, name=fname, column=col, line=line,
                      inp_count=len(in_names), out_count=1,
                      out1_name=fname, out1_type=TYPE[fn['out']])
        for i, (n, t) in enumerate(fn['inputs'], 1):
            b['inp%d_name' % i] = n
            b['inp%d_type' % i] = TYPE[t]
        for k, (kb, ks, kl, kinv, _) in enumerate(kids):
            want = fn['inputs'][k][1]
            if kl and kl != want:
                raise SchemeError('%s.%s ждёт %s, а подано %s — «Ошибка 29»' % (fname, in_names[k], want, kl))
            self.link(kb, b, want, src_slot=ks, dst_slot=k, invert=kinv)
        if out:
            vt = types.get(out) or self.vtype(out)
            if vt != fn['out']:
                raise SchemeError('%s возвращает %s, а %r — %s' % (fname, fn['out'], out, vt))
            self.link(b, self.var(out, col + EXPR_RES_GAP, line, vt), vt)
        rows = max(nxt - line, len(in_names), 1)
        self.next_line = line + rows + gap
        return b

    def struct_type(self, inst):
        """Имя структуры по экземпляру из словаря программы (строка Type=U)."""
        if inst not in self.instances:
            raise SchemeError('экземпляра %r нет в словаре программы' % inst)
        return self.instances[inst]

    def struct_call(self, inst, method, line, column=COL_SRC, ins=None, outs=None, gap=2, types=None):
        """Вызов метода структуры проекта: блок ФБ (type 3) с именем <экземпляр>.<метод>.
        Входы — поля структуры с inout 1, выходы — поля с inout 2 (как у системного ФБ).

            s.struct_call('t2', 'calc', line=3, ins={'Level_pct': 'pct', 'Area_m2': K('3.0','R'), …},
                          outs={'Volume_m3': 'vol', 'Alarm_hi': 'alm'})
        """
        st = struct_catalog(self.root or '')[self.struct_type(inst)]
        fb_ins = [(n, t) for n, t, io in st['fields'] if io == 1]
        fb_outs = [(n, t) for n, t, io in st['fields'] if io == 2]
        if method not in st['methods']:
            raise SchemeError('у структуры %r нет метода %r' % (self.struct_type(inst), method))
        return self._call_block(
            lambda col: self.fb(inst, method, fb_ins, fb_outs, col, line),
            fb_ins, fb_outs, line, column, ins, outs, gap, types,
            title='%s.%s' % (inst, method))

    def struct_fields(self, inst, line, column=COL_SRC):
        """Блок «структура с полями» (type 2): все поля экземпляра и на входах, и на
        выходах — можно записать поле и тут же прочитать. Ставится как есть, без
        раскладки; экземпляр должен быть в словаре программы."""
        st = struct_catalog(self.root or '')[self.struct_type(inst)]
        b = self._add(type=T_STRUCT_F, dict=0, mode=4, name=inst, column=column, line=line,
                      inp_count=len(st['fields']), out_count=len(st['fields']))
        for i, (n, t, _) in enumerate(st['fields'], 1):
            b['inp%d_name' % i] = n
            b['inp%d_type' % i] = TYPE[t]
            b['out%d_name' % i] = n
            b['out%d_type' % i] = TYPE[t]
        return b

    def struct_pin(self, inst, line, column=COL_SRC):
        """Блок «структура» (type 12): один вход и один выход типа 32 — структура
        целиком. Соединяется только с таким же выводом структуры."""
        self.struct_type(inst)
        return self._add(type=T_STRUCT, dict=0, mode=4, name=inst, column=column, line=line,
                         inp_count=1, inp1_name='', inp1_type=32,
                         out_count=1, out1_name='', out1_type=32)

    def child_params(self, name):
        """Параметры дочерней программы: [(имя, буква)] по строкам с Attribute 1
        её словаря, плюс буква возвращаемого значения (строка с именем программы)."""
        csv = os.path.join(self.progdir or '', name, 'prog.csv')
        if not os.path.exists(csv):
            raise SchemeError('нет словаря дочерней программы %r (%s)' % (name, csv))
        ins, out = [], None
        with open(csv, encoding='utf-8') as f:
            f.readline()
            for line in f:
                c = line.rstrip('\r\n').split(';')
                if len(c) < 7 or not c[0]:
                    continue
                if c[0] == name:
                    out = c[1]
                elif c[6] == '1':
                    ins.append((c[0], c[1]))
        return ins, out

    def child_call(self, name, line, column=COL_SRC, ins=None, out=None, gap=2, types=None):
        """Вызов дочерней программы: блок type 16 (dict 3, mode 0). Входы — параметры
        (строки словаря дочерней с Attribute 1), единственный выход назван её именем.
        В коде — `y := ch_lim( x ) ;`, как вызов функции."""
        params, ret = self.child_params(name)
        if ret is None:
            raise SchemeError('в словаре дочерней %r нет строки возвращаемого значения' % name)

        def make(col):
            b = self._add(type=T_CHILD, dict=3, mode=0, name=name, column=col, line=line,
                          inp_count=len(params), out_count=1, out1_name=name, out1_type=TYPE[ret])
            for i, (n, t) in enumerate(params, 1):
                b['inp%d_name' % i] = n
                b['inp%d_type' % i] = TYPE[t]
            return b

        return self._call_block(make, params, [(name, ret)], line, column, ins,
                                {name: out} if out else None, gap, types, title=name)

    def _call_block(self, make, pin_ins, pin_outs, line, column, ins, outs, gap, types, title):
        """Общая раскладка вызова (ФБ структуры, дочерняя программа): входные
        выражения слева, блок, результаты справа."""
        types, ins, outs = types or {}, ins or {}, outs or {}
        in_names = [n for n, _ in pin_ins]
        out_names = [n for n, _ in pin_outs]
        miss = [x for x in in_names if x not in ins]
        extra = [x for x in list(ins) + list(outs) if x not in in_names + out_names]
        if miss or extra:
            raise SchemeError('%s: %s%s' % (title, 'не подключены входы %s; ' % miss if miss else '',
                                            'нет выводов %s' % extra if extra else ''))
        depth = 1 + max([self._depth(ins[x]) for x in in_names] + [0])
        col = column + EXPR_SRC_GAP + (depth - 1) * EXPR_OP_STEP
        kids, nxt = [], line
        for k, x in enumerate(in_names):
            r = max(line + k, nxt + (2 if k and self._depth(ins[x]) > 0 else 0))
            kid = self._place(ins[x], r, 2, depth, column, types)
            kids.append(kid)
            nxt = r + kid[4]
        b = make(col)
        for k, (kb, ks, kl, kinv, _) in enumerate(kids):
            want = pin_ins[k][1]
            if kl and kl != want:
                raise SchemeError('%s.%s ждёт %s, а подано %s — «Ошибка 29»' % (title, in_names[k], want, kl))
            self.link(kb, b, want, src_slot=ks, dst_slot=k, invert=kinv)
        for x, names in outs.items():
            slot = out_names.index(x)
            want = pin_outs[slot][1]
            for j, v in enumerate([names] if isinstance(names, str) else names):
                vt = types.get(v) or self.vtype(v)
                if vt != want:
                    raise SchemeError('%s.%s типа %s, а %r — %s' % (title, x, want, v, vt))
                self.link(b, self.var(v, col + EXPR_RES_GAP + 4 * j, line + slot, vt), want, src_slot=slot)
        rows = max(nxt - line, len(in_names), len(out_names))
        self.next_line = line + rows + gap
        return b

    # ---------- порядок выполнения ----------
    def sequence(self):
        """Проставляет sequence ровно так, как это делает IDE после любой правки
        мышью (ide_order): результаты сверху вниз, перед каждым — его источники.
        Поэтому правка сгенерированной схемы в редакторе порядок не меняет.
        Порядок выполнения задаёт ИМЕННО sequence; дубликаты дают «Ошибка 19»."""
        by_id = {b['save_id']: b for b in self.blocks}
        order = ide_order(self.blocks, self.links)
        for i, bid in enumerate(order):
            by_id[bid]['sequence'] = i
            by_id[bid].pop('_new', None)
        live = set(order)
        for blk in self.blocks:
            if blk['save_id'] not in live:
                blk['sequence'] = -1
            blk.pop('_new', None)
        return self

    # ---------- проверка ----------
    REQUIRED = ('save_id', 'sequence', 'column', 'line', 'type', 'name',
                'dict', 'mode', 'inp_count', 'out_count')

    def validate(self):
        """Список проблем. Пусто — схему можно писать на диск."""
        bad = []
        ids = {}
        for b in self.blocks:
            for f in self.REQUIRED:
                if f not in b:
                    bad.append('блок %r: нет поля %s — IDE выбросит блок молча'
                               % (b.get('name'), f))
            if b.get('type') not in KNOWN_TYPES:
                bad.append('блок %r: неизвестный type=%s — IDE выбросит блок молча'
                           % (b.get('name'), b.get('type')))
            if b.get('type') in (T_CONST, T_OP) and 'subtype' not in b:
                bad.append('блок %r: у константы и оператора обязателен subtype' % b.get('name'))
            if b.get('type') == T_OP and b.get('inp_count', 0) > 2 and b.get('args') != b['inp_count']:
                bad.append('оператор %r на %s входа без args=%s — IDE при сохранении обрежет его до двух '
                           'входов и выбросит связи' % (b.get('name'), b['inp_count'], b['inp_count']))
            for i in range(1, b.get('inp_count', 0) + 1):
                if 'inp%d_type' % i not in b:
                    bad.append('блок %r: нет inp%d_type' % (b.get('name'), i))
            for i in range(1, b.get('out_count', 0) + 1):
                if 'out%d_type' % i not in b:
                    bad.append('блок %r: нет out%d_type' % (b.get('name'), i))
            ids.setdefault(b.get('save_id'), []).append(b)
            if b.get('type') == T_VAR and b.get('dict', 0) == 0 and self.vars and b['name'] not in self.vars \
                    and not self.other_var(b['name']) and not self.elem_type(b['name']):
                bad.append('переменной %r нет в словаре программы — сборка даст «Ошибка 19»%s'
                           % (b['name'], ' (она глобальная: блоку нужны dict 1, mode 0)' if b['name'] in self.globals else ''))
            if b.get('type') == T_VAR and b.get('dict') == 1 and self.globals is not None and self.vars \
                    and b['name'] not in self.globals:
                bad.append('глобальной переменной %r нет в глобальном словаре (tags/global.csv)' % b['name'])
            if all(k in b for k in ('column', 'line', 'type')) and b['type'] != T_COMMENT:
                x1, y1, x2, y2 = block_box(b)
                if b['column'] < 0 or b['line'] < 0 or b['column'] >= self.columns or b['line'] >= self.lines:
                    bad.append('блок %r (%s,%s) вне поля %dx%d: в коде он есть, но на экране не виден и мышью '
                               'недоступен' % (b.get('name'), b['column'], b['line'], self.columns, self.lines))
                elif y1 < 0 or x2 > self.columns:
                    bad.append('блок %r (%s,%s) обрезан краем поля' % (b.get('name'), b['column'], b['line']))
            if b.get('type') in (T_FB, T_STRUCT_F, T_STRUCT) and self.instances:
                inst = b['name'].split('.')[0]
                if inst not in self.instances:
                    bad.append('экземпляра %r нет в словаре программы (строка Type=U)' % inst)
        for i, bl in ids.items():
            if len(bl) > 1:
                bad.append('save_id %s занят %d блоками' % (i, len(bl)))
        fbs = {}
        for b in self.blocks:
            if b.get('type') == T_FB:
                fbs.setdefault(b.get('name'), []).append(b)
        for n, bl in fbs.items():
            if len(bl) > 1:
                bad.append('экземпляр ФБ %r стоит на схеме %d раза — при сохранении из программы '
                           'пропадут ВСЕ связи; нужен отдельный экземпляр на каждый блок' % (n, len(bl)))
        seqs = [b.get('sequence') for b in self.blocks if 'sequence' in b and b.get('sequence') != -1]
        if len(set(seqs)) != len(seqs):
            bad.append('повторяющийся sequence — код на ST выйдет искажённым, сборка упадёт')
        # наложение и касание: IDE подсвечивает такие блоки жёлтым
        boxed = [b for b in self.blocks if all(k in b for k in ('column', 'line', 'type'))]
        for i, a in enumerate(boxed):
            ax1, ay1, ax2, ay2 = block_box(a)
            for c in boxed[i + 1:]:
                if (a.get('type') == T_ENI and a.get('block') == c.get('save_id')) or \
                   (c.get('type') == T_ENI and c.get('block') == a.get('save_id')):
                    continue
                cx1, cy1, cx2, cy2 = block_box(c)
                if ax1 < cx2 + 0.5 and cx1 < ax2 + 0.5 and ay1 < cy2 and cy1 < ay2:
                    bad.append('блоки %r (%s,%s) и %r (%s,%s) по оценке ширины стоят вплотную или внахлёст — '
                               'наложенные блоки IDE заливает жёлтым (на сборку не влияет); оставить клетку'
                               % (a.get('name'), a.get('column'), a.get('line'), c.get('name'), c.get('column'), c.get('line')))
        seen_in = set()
        by_id = {b['save_id']: b for b in self.blocks if 'save_id' in b}
        for l in self.links:
            ok_ends = True
            for end in ('src', 'dst'):
                bid = l[end + '_block']
                if bid not in by_id:
                    bad.append('связь на несуществующий блок %s — IDE выбросит связь молча' % bid)
                    ok_ends = False
                    continue
                b = by_id[bid]
                cnt = b['out_count'] if end == 'src' else b['inp_count']
                if l[end + '_slot'] >= cnt:
                    bad.append('связь: у блока %r нет вывода №%d' % (b['name'], l[end + '_slot']))
            # у константы IDE сама пишет out1_type 0 и src_type 0 — тип берётся из приёмника
            src_is_const = by_id.get(l['src_block'], {}).get('type') == T_CONST
            if l['src_type'] != l['dst_type'] and not src_is_const:
                bad.append('связь %s -> %s: разные типы — сборка даст «Ошибка 29»; неявных '
                           'преобразований нет, нужен оператор вроде INT_TO_REAL' % (l['src_name'], l['dst_name']))
            if l.get('mode') == LINK_COMMENTED:
                bad.append('связь %s -> %s закомментирована (mode 1) — для IDE её нет' % (l['src_name'], l['dst_name']))
            elif l.get('mode') not in (LINK_NORMAL, LINK_INVERTED):
                bad.append('связь %s -> %s: неизвестный mode=%s' % (l['src_name'], l['dst_name'], l.get('mode')))
            key = (l['dst_block'], l['dst_slot'])
            if key in seen_in:
                bad.append('на вход %s заведено больше одной связи' % l['dst_name'])
            seen_in.add(key)
            if ok_ends:
                s, d = by_id[l['src_block']], by_id[l['dst_block']]
                if s.get('sequence', -1) >= 0 and d.get('sequence', -1) >= 0 and s['sequence'] >= d['sequence']:
                    bad.append('порядок: %r (seq %s) должен идти до %r (seq %s)'
                               % (s['name'], s['sequence'], d['name'], d['sequence']))
        live_links = [l for l in self.links if l.get('mode') != LINK_COMMENTED]
        for b in self.blocks:
            if b.get('mode') == 1 or b.get('type') not in (T_OP, T_FB, T_FUNC, T_CHILD, T_COIL, T_JUMP):
                continue
            for slot in range(b.get('inp_count', 0)):
                if not any(l['dst_block'] == b['save_id'] and l['dst_slot'] == slot for l in live_links):
                    bad.append('вход №%d блока %r не присоединён — сборка упадёт' % (slot, b['name']))
            if b['type'] == T_OP and not any(l['src_block'] == b['save_id'] for l in live_links):
                bad.append('выход оператора %r не присоединён — «проверить» и сборка дают ошибку' % b['name'])
        return bad

    # ---------- запись ----------
    def text(self):
        return {'Define': [{'block_count': len(self.blocks), 'column_max': self.columns,
                            'line_max': self.lines, 'track_count': len(self.links), 'version': 0}],
                'Blocks': self.blocks, 'Links': self.links}

    def save(self, prog_json, force=False):
        """Кладёт схему в существующий prog.json программы (lang/name/uid сохраняются).
        Ошибки (validate) — исключение, если не force. Возвращает список
        предупреждений: ошибки при force и замечания о порядке (order_remarks)."""
        # новая схема нумеруется по правилу IDE; у правленой сохраняется её порядок
        # (комментарии с sequence -1 за «уже пронумерованную» не считать)
        if not any(b.get('sequence', -1) >= 0 and not b.get('_new') for b in self.blocks):
            self.sequence()
        elif any(b.get('_new') for b in self.blocks):
            self.resequence()
        for b in self.blocks:
            b.pop('_new', None)
        self.compact_ids()
        bad = self.validate()
        if bad and not force:
            raise SchemeError('схема не прошла проверку:\n  - ' + '\n  - '.join(bad))
        bad = bad + order_remarks(self.blocks, self.links)
        d = json.load(open(prog_json, encoding='utf-8'))
        d['lang'] = 'fbd'
        d['text'] = self.text()
        open(prog_json, 'w', encoding='utf-8', newline='\n').write(
            json.dumps(d, indent=4, sort_keys=True, ensure_ascii=False) + '\n')
        return bad


def check_file(prog_json):
    """Проверяет уже записанный prog.json, в том числе чужой."""
    d = json.load(open(prog_json, encoding='utf-8'))
    t = d.get('text', {})
    if 'Blocks' not in t:
        return ['это не FBD-программа (в text нет Blocks)']
    csv = os.path.join(os.path.dirname(prog_json), 'prog.csv')
    s = Scheme(dict_csv=csv) if os.path.exists(csv) else Scheme()
    s.blocks = t['Blocks']
    s.links = t.get('Links', [])
    df = (t.get('Define') or [{}])[0]
    s.columns, s.lines = df.get('column_max', 500), df.get('line_max', 500)
    bad = s.validate() + order_remarks(s.blocks, s.links)
    df = (t.get('Define') or [{}])[0]
    if df.get('block_count') != len(s.blocks):
        bad.append('Define.block_count=%s, а блоков %d — лишние блоки IDE не покажет'
                   % (df.get('block_count'), len(s.blocks)))
    if df.get('track_count') != len(s.links):
        bad.append('Define.track_count=%s, а связей %d' % (df.get('track_count'), len(s.links)))
    return bad


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print(__doc__)
    else:
        for p in sys.argv[1:]:
            bad = check_file(p)
            print('=== %s: %s' % (p, 'ок' if not bad else '%d замечаний' % len(bad)))
            for b in bad:
                print('   -', b)
