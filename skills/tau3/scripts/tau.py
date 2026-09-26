"""Драйвер GUI программ ТАУ-3 (Delphi, Win32) через pywinauto/pywin32. Печатает JSON.

Запуск: python tau.py <команда> [опции]   (Python 3 x64; pywinauto, pywin32, pillow)
Процесс держится между вызовами; команды находят его по --pid или сами (единственный запущенный процесс ТАУ-3).

  launch PROG [--prev yes|no] [--dir D]   запустить (из рабочей копии), закрыть заставку, ответить «Использовать данные
                                          предыдущего счета?» (по умолчанию yes); печатает pid и окна
  ps                                      запущенные процессы ТАУ-3
  ls [--all] [--controls]                 видимые окна процесса (hwnd, класс, заголовок, прямоугольник)
  menu [--win W]                          показать дерево всплывающего меню окна (пункты, id, disabled)
  menu [--win W] "Путь->Пункт"            выполнить пункт меню (можно часть названия, регистр не важен)
  click [--win W] (--ctl T | --xy X,Y | --wxy X,Y) [--right] [--double]
                                          щелчок по контролу, по точке клиентской области (--xy) или по точке снимка окна (--wxy)
  set [--win W] --ctl T VALUE [--nocommit]  щелчок в поле, текст, CM_EXIT (значение применяется по OnExit)
  select [--win W] --ctl T ITEM           выбрать строку в TListBox/TComboBox (текст или номер)
  radio [--win W] --ctl T N               выбрать N-ю кнопку (с 0) в TRadioGroup
  keys [--win W] [--ctl T] KEYS           послать клавиши (синтаксис pywinauto: {ENTER} {TAB} {DOWN} ^{HOME} {F1}…)
  grid [--win W] [--ctl T] R,C=VAL [R,C=VAL …]   ввод в TStringGrid (R,C с 0 от первой редактируемой ячейки, ^Home)
  fill [--win W] V1 V2 … [--ok OK]       значения построчно в окно-таблицу (Значения A от/до/шаг, Частоты, Xo, tрег);
                                          '-' — пропустить строку; --ok OK — нажать OK после ввода
  answer [BUTTON]                         нажать кнопку в сообщении (Yes/No/OK/Cancel…); без аргумента — только показать
  tofile [--win W] [append]              «В файл / на принтер» -> в файл -> OK; печатает текст <PROG>.tab (cp1251)
  shot [--win W|--all] OUT                PNG окна (PrintWindow; OUT — файл или папка при --all)
  wait [--win W] [--timeout S]            ждать появления окна
  close                                   завершить процесс
T (контрол): hwnd 0x.., Класс#N (N с 0 в порядке ls --controls), текст/подпись, @x,y — контрол под точкой клиента окна.
W: hwnd (0x..), класс (TGraForm), подстрока заголовка или «main» (TMForm); по умолчанию — активное верхнее окно.
"""
import ctypes, sys, os, time, json, argparse, re

ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-1))  # логические координаты, как у программ ТАУ-3
import warnings
warnings.filterwarnings('ignore')
import win32gui, win32con, win32api, win32process, win32ui
from pywinauto import Application
from pywinauto.controls.hwndwrapper import HwndWrapper

SKILL = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))  # realpath: the skill dir is a junction
DEF_DIR = os.path.join(os.path.dirname(SKILL), 'Работа', 'TAY_3')
PROGS = ['Anacon', 'Anacon2', 'Anacon3', 'Asympt', 'Cascad', 'Control', 'Galery', 'Identf', 'Impuls', 'Kalman',
         'Linsys', 'Linsys2', 'Linsys3', 'Mulpol', 'Mvacs2', 'Nlinsys', 'Optim', 'Optim2', 'Phaspl', 'Proni',
         'Qpol', 'Rtlz', 'Spectr', 'Tay_3', 'Watt']
SKIP = {'TApplication', 'TPUtilWindow', 'ComboLBox', 'MSCTFIME UI', 'IME', 'tooltips_class32', 'THintWindow'}
DIALOG_CLASSES = {'TMessageForm', '#32770'}
NL = chr(10)
CM_ENTER, CM_EXIT = 0xB01A, 0xB01B  # VCL: TWinControl.DoEnter/DoExit


def out(obj):
    sys.stdout.reconfigure(encoding='utf-8')
    lines = []
    for k, v in obj.items():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            lines.append(' "%s": [' % k + NL + '  ' + (',' + NL + '  ').join(
                json.dumps(x, ensure_ascii=False) for x in v) + NL + ' ]')
        else:
            lines.append(' "%s": %s' % (k, json.dumps(v, ensure_ascii=False)))
    print('{' + NL + (',' + NL).join(lines) + NL + '}')


class TauError(Exception):
    pass


QUIET = False


def die(msg, **kw):
    if QUIET:
        raise TauError(msg)
    out(dict(ok=False, error=msg, **kw)); sys.exit(1)


# ---------- процессы и окна ----------
def tau_pids():
    import subprocess
    r = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True, text=True, encoding='cp866', errors='replace')
    res = []
    for ln in r.stdout.splitlines():
        parts = [p.strip('"') for p in ln.split('","')]
        if parts and parts[0].lower().replace('.exe', '') in [p.lower() for p in PROGS]:
            res.append((int(parts[1]), parts[0]))
    return res


def get_pid(a):
    if getattr(a, 'pid', None):
        return a.pid
    ps = tau_pids()
    if not ps:
        die('нет запущенных программ ТАУ-3 (сначала launch)')
    if len(ps) > 1:
        die('запущено несколько программ ТАУ-3 — укажите --pid', running=ps)
    return ps[0][0]


def top_windows(pid, visible=True):
    res = []
    def cb(h, _):
        if win32process.GetWindowThreadProcessId(h)[1] == pid:
            if (not visible or win32gui.IsWindowVisible(h)) and win32gui.GetClassName(h) not in SKIP:
                res.append(h)
    win32gui.EnumWindows(cb, None)
    return res  # в Z-порядке: первое — самое верхнее


def gettext(h):
    n = win32gui.SendMessage(h, win32con.WM_GETTEXTLENGTH, 0, 0)
    if n <= 0:
        return ''
    buf = ctypes.create_unicode_buffer(n + 2)
    ctypes.windll.user32.SendMessageW(h, win32con.WM_GETTEXT, n + 1, buf)
    return buf.value


def winfo(h, controls=False):
    l, t, r, b = win32gui.GetWindowRect(h)
    d = dict(hwnd=hex(h), cls=win32gui.GetClassName(h), title=win32gui.GetWindowText(h), rect=[l, t, r - l, b - t],
             enabled=bool(win32gui.IsWindowEnabled(h)))
    if controls:
        cs = []
        idx = {}
        def cb(c, _):
            if not win32gui.IsWindowVisible(c):
                return
            cl = win32gui.GetClassName(c)
            idx[cl] = idx.get(cl, -1) + 1
            cl_l, cl_t, cl_r, cl_b = win32gui.GetWindowRect(c)
            px, py = win32gui.ScreenToClient(h, (cl_l, cl_t))
            cs.append(dict(hwnd=hex(c), cls=cl, n=idx[cl], text=gettext(c)[:200],
                           xy=[px, py], wh=[cl_r - cl_l, cl_b - cl_t]))
        win32gui.EnumChildWindows(h, cb, None)
        d['controls'] = cs
    return d


def find_win(pid, spec):
    ws = top_windows(pid)
    if not ws:
        die('у процесса нет видимых окон', pid=pid)
    if not spec:
        # модальный диалог/верхнее окно
        return ws[0]
    if spec.lower().startswith('0x'):
        return int(spec, 16)
    if spec == 'main':
        spec = 'TMForm'
    for h in ws:
        if win32gui.GetClassName(h) == spec:
            return h
    for h in ws:
        if spec.lower() in win32gui.GetWindowText(h).lower():
            return h
    die('окно не найдено: %s' % spec, windows=[winfo(h) for h in ws])


def find_ctl(hwin, spec):
    """spec: hwnd 0x.., 'Класс#N' (N с 0 в порядке EnumChildWindows), точный/частичный текст."""
    if spec.lower().startswith('0x'):
        return int(spec, 16)
    if spec.startswith('@'):  # контрол под точкой клиента окна: @x,y
        x, y = map(int, spec[1:].split(','))
        return child_at(hwin, x, y)[0]
    kids = []
    win32gui.EnumChildWindows(hwin, lambda c, _: kids.append(c) if win32gui.IsWindowVisible(c) else None, None)
    m = re.match(r'^(\w+)#(\d+)$', spec)
    if m:
        same = [c for c in kids if win32gui.GetClassName(c) == m.group(1)]
        if int(m.group(2)) < len(same):
            return same[int(m.group(2))]
    elif spec in [win32gui.GetClassName(c) for c in kids]:
        return [c for c in kids if win32gui.GetClassName(c) == spec][0]
    norm = lambda s: s.replace('&', '').strip().lower()
    for c in kids:
        if norm(gettext(c)) == norm(spec):
            return c
    for c in kids:
        if norm(spec) in norm(gettext(c)):
            return c
    die('контрол не найден: %s' % spec, window=winfo(hwin, True))


# ---------- меню ----------
def menu_tree(hm, path=''):
    res = []
    for i in range(win32gui.GetMenuItemCount(hm)):
        buf = ctypes.create_unicode_buffer(256)
        ctypes.windll.user32.GetMenuStringW(hm, i, buf, 256, 0x400)
        sub = win32gui.GetSubMenu(hm, i)
        st = win32gui.GetMenuState(hm, i, 0x400)
        text = buf.value.split('\t')[0].replace('&', '')
        if st & win32con.MF_SEPARATOR:
            continue
        item = dict(path=path + text, id=None if sub else win32gui.GetMenuItemID(hm, i),
                    disabled=bool(st & (win32con.MF_GRAYED | win32con.MF_DISABLED)), checked=bool(st & win32con.MF_CHECKED))
        res.append(item)
        if sub:
            res += menu_tree(sub, path + text + '->')
    return res


def util_window(pid):
    res = []
    def cb(h, _):
        if win32process.GetWindowThreadProcessId(h)[1] == pid and win32gui.GetClassName(h) == 'TPUtilWindow':
            res.append(h)
    win32gui.EnumWindows(cb, None)
    return res


def popup_items(pid, hwin):
    """Вызвать контекстное меню окна (WM_CONTEXTMENU), прочитать пункты и закрыть. Меню главного окна Delphi, если есть,
    тоже возвращается (source=mainmenu)."""
    hm_main = win32gui.GetMenu(hwin)
    if hm_main:
        return menu_tree(hm_main), 'mainmenu'
    l, t, r, b = win32gui.GetWindowRect(hwin)
    win32gui.PostMessage(hwin, win32con.WM_CONTEXTMENU, hwin, win32api.MAKELONG((l + 40) & 0xFFFF, (t + 60) & 0xFFFF))
    items = None
    for _ in range(30):
        time.sleep(0.1)
        ms = []
        win32gui.EnumWindows(lambda h, _: ms.append(h) if (win32gui.GetClassName(h) == '#32768' and
                             win32gui.IsWindowVisible(h) and win32process.GetWindowThreadProcessId(h)[1] == pid) else None, None)
        if ms:
            hm = win32gui.SendMessage(ms[0], 0x01E1, 0, 0)  # MN_GETHMENU
            items = menu_tree(hm) if hm else []
            for mw in ms:
                win32gui.PostMessage(mw, win32con.WM_KEYDOWN, win32con.VK_ESCAPE, 0)
            time.sleep(0.3)
            # подменю тоже закрыть
            for _ in range(3):
                ms2 = []
                win32gui.EnumWindows(lambda h, _: ms2.append(h) if (win32gui.GetClassName(h) == '#32768' and
                                     win32gui.IsWindowVisible(h) and win32process.GetWindowThreadProcessId(h)[1] == pid) else None, None)
                if not ms2:
                    break
                for mw in ms2:
                    win32gui.PostMessage(mw, win32con.WM_KEYDOWN, win32con.VK_ESCAPE, 0)
                time.sleep(0.2)
            break
    if items is None:
        die('у окна нет контекстного меню (или оно не открылось)', window=winfo(hwin))
    return items, 'popup'


def run_menu(pid, hwin, path):
    items, src = popup_items(pid, hwin)
    want = [p.strip().lower() for p in re.split(r'->|/|>', path)]
    def match(it):
        parts = [p.strip().lower() for p in it['path'].split('->')]
        if len(want) > len(parts):
            return False
        tail = parts[-len(want):]  # можно указывать только конец пути: «Корневой годограф»
        return all(w == p or w in p for w, p in zip(want, tail))
    cands = [it for it in items if it['id'] is not None and match(it)]
    exact = [it for it in cands if it['path'].lower() == '->'.join(want) or it['path'].lower().split('->')[-1] == want[-1]]
    if exact:
        cands = exact
    if not cands:
        die('пункт меню не найден: %s' % path, items=[i['path'] for i in items])
    if len(cands) > 1:
        die('неоднозначно: %s' % path, candidates=[c['path'] for c in cands])
    it = cands[0]
    if it['disabled']:
        die('пункт меню недоступен (серый): %s' % it['path'])
    target = hwin if src == 'mainmenu' else util_window(pid)[0]
    win32gui.PostMessage(target, win32con.WM_COMMAND, it['id'], 0)
    return it


# ---------- снимки ----------
def shot(h, fn):
    from PIL import Image
    l, t, r, b = win32gui.GetWindowRect(h); w, hh = r - l, b - t
    hdc = win32gui.GetWindowDC(h); mdc = win32ui.CreateDCFromHandle(hdc); sdc = mdc.CreateCompatibleDC()
    bmp = win32ui.CreateBitmap(); bmp.CreateCompatibleBitmap(mdc, w, hh); sdc.SelectObject(bmp)
    ctypes.windll.user32.PrintWindow(h, sdc.GetSafeHdc(), 2)
    info = bmp.GetInfo()
    im = Image.frombuffer('RGB', (info['bmWidth'], info['bmHeight']), bmp.GetBitmapBits(True), 'raw', 'BGRX', 0, 1)
    os.makedirs(os.path.dirname(os.path.abspath(fn)), exist_ok=True)
    im.save(fn)
    win32gui.DeleteObject(bmp.GetHandle()); sdc.DeleteDC(); mdc.DeleteDC(); win32gui.ReleaseDC(h, hdc)
    return fn


# ---------- ввод ----------
def click_xy(h, x, y, right=False, double=False):
    lp = win32api.MAKELONG(x & 0xFFFF, y & 0xFFFF)
    down, up, flag = (win32con.WM_RBUTTONDOWN, win32con.WM_RBUTTONUP, win32con.MK_RBUTTON) if right else \
                     (win32con.WM_LBUTTONDOWN, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON)
    win32gui.PostMessage(h, win32con.WM_MOUSEMOVE, 0, lp)
    win32gui.PostMessage(h, down, flag, lp)
    win32gui.PostMessage(h, up, 0, lp)
    if double:
        win32gui.PostMessage(h, win32con.WM_LBUTTONDBLCLK, flag, lp)
        win32gui.PostMessage(h, up, 0, lp)


def child_at(h, x, y):
    """Самый глубокий видимый дочерний контрол под клиентской точкой окна h -> (hwnd, x, y в его координатах)."""
    sx, sy = win32gui.ClientToScreen(h, (x, y))
    cur = h
    while True:
        cx, cy = win32gui.ScreenToClient(cur, (sx, sy))
        c = win32gui.ChildWindowFromPointEx(cur, (cx, cy), 1 | 2)  # skip invisible|disabled
        if not c or c == cur:
            return cur, cx, cy
        cur = c


def press_button(hbtn):
    win32gui.PostMessage(hbtn, win32con.BM_CLICK, 0, 0)


def wait_idle(pid, t=0.4):
    time.sleep(t)


def dialogs(pid):
    return [h for h in top_windows(pid) if win32gui.GetClassName(h) in DIALOG_CLASSES]


SHOTDIR = os.path.join(os.environ.get('TEMP', '.'), 'tau3_shots')


def dialog_info(h):
    d = winfo(h, True)
    try:  # текст сообщения Delphi — в TLabel без окна: только картинка
        d['shot'] = shot(h, os.path.join(SHOTDIR, 'dlg_%x.png' % h))
    except Exception:
        pass
    d['buttons'] = [c['text'].replace('&', '') for c in d['controls'] if c['cls'] in ('TButton', 'Button', 'TBitBtn')]
    return d


def launch(prog, prev='yes', wd=None):
    wd = wd or DEF_DIR
    exe = os.path.join(wd, prog if prog.lower().endswith('.exe') else prog + '.exe')
    if not os.path.exists(exe):
        cand = [p for p in PROGS if p.lower() == prog.lower().replace('.exe', '')]
        if cand:
            exe = os.path.join(wd, cand[0] + '.exe')
    if not os.path.exists(exe):
        die('нет файла %s' % exe)
    app = Application(backend='win32').start('"%s"' % exe, work_dir=wd)
    pid = app.process
    log = []
    # заставка TAboutForm -> OK; далее возможен вопрос «Использовать данные предыдущего счета?»
    t0 = time.time()
    while time.time() - t0 < 15:
        time.sleep(0.3)
        ws = top_windows(pid)
        cls = [win32gui.GetClassName(h) for h in ws]
        if 'TAboutForm' in cls:
            h = ws[cls.index('TAboutForm')]
            press_button(find_ctl(h, 'OK')); log.append('splash OK'); time.sleep(0.5); continue
        dl = dialogs(pid)
        if dl:
            info = dialog_info(dl[0])
            btns = {b.lower(): c for b, c in zip(info['buttons'],
                    [c for c in info['controls'] if c['cls'] in ('TButton', 'Button', 'TBitBtn')])}
            want = {'yes': ['yes', 'да'], 'no': ['no', 'нет']}[prev]
            hit = [btns[b] for b in btns if b in want] or [btns[b] for b in btns if b in ('ok',)]
            if hit:
                press_button(int(hit[0]['hwnd'], 16)); log.append('dialog -> %s' % hit[0]['text']); time.sleep(0.5)
                continue
            break
        if 'TMForm' in cls or 'TMenuForm' in cls:
            time.sleep(0.5)
            if not dialogs(pid):
                break
    return dict(ok=True, pid=pid, exe=exe, steps=log, windows=[winfo(h) for h in top_windows(pid)])


# ---------- TStringGrid ----------
def grid_geometry(hgrid):
    """Столбцы и строки TStringGrid по линиям на снимке: {'cols': [(x0,x1)], 'rows': [(y0,y1)]} в координатах сетки."""
    from PIL import Image
    fn = shot(hgrid, os.path.join(SHOTDIR, 'grid_%x.png' % hgrid))
    im = Image.open(fn).convert('RGB'); W, H = im.size; px = im.load()
    dark = lambda p: sum(p) < 600
    cols = [x for x in range(W) if sum(dark(px[x, y]) for y in range(H)) > 0.6 * H]
    rows = [y for y in range(H) if sum(dark(px[x, y]) for x in range(W)) > 0.6 * W]
    def cells(lines, size):
        bounds = []
        for v in lines:
            if bounds and v - bounds[-1][1] <= 2:
                bounds[-1][1] = v
            else:
                bounds.append([v, v])
        cuts = [0] + [b for pair in bounds for b in pair] + [size - 1]
        out_ = []
        # промежутки между линиями
        prev = 0
        for b0, b1 in bounds:
            if b0 - prev >= 6:
                out_.append((prev, b0))
            prev = b1 + 1
        if size - prev >= 6:
            out_.append((prev, size))
        return out_
    return dict(cols=cells(cols, W), rows=cells(rows, H), size=[W, H])


def table_rows(h):
    """Строки нарисованной таблицы ввода (TValForm, TXForm, TWForm, TTimForm…) по линиям на снимке окна.
    Возвращает [(y_центр, x_центр столбца значений)] в координатах снимка окна."""
    from PIL import Image
    fn = shot(h, os.path.join(SHOTDIR, 'form_%x.png' % h))
    im = Image.open(fn).convert('RGB'); W, H = im.size; px = im.load()
    dark = lambda p: sum(p) < 450
    l, t, _, _ = win32gui.GetWindowRect(h); ox, oy = win32gui.ClientToScreen(h, (0, 0))
    top = oy - t
    # вертикальный разделитель «подпись | значение»: самый «тёмный» столбец в средней части
    score = [(sum(dark(px[x, y]) for y in range(top, H)), x) for x in range(int(W * 0.15), int(W * 0.75))]
    xsep = max(score)[1]
    ys = [y for y in range(top, H) if sum(dark(px[x, y]) for x in range(xsep + 3, W - 3)) > 0.8 * (W - xsep - 6)]
    lines = [[top, top]]
    for y in ys:
        if y - lines[-1][1] <= 2:
            lines[-1][1] = y
        else:
            lines.append([y, y])
    rows = []
    for (a0, a1), (b0, b1) in zip(lines, lines[1:]):
        yc = (a1 + b0) // 2
        if b0 - a1 >= 12 and dark(px[xsep, yc]) or (b0 - a1 >= 12 and any(dark(px[xsep + d, yc]) for d in (-1, 1))):
            rows.append(yc)
    xr = next((x for x in range(xsep + 10, W) if dark(px[x, rows[0]])), W - 5) if rows else W - 5
    return [(y, (xsep + xr) // 2) for y in rows]


def fill_form(h, values, pid):
    """Ввести значения построчно в нарисованную таблицу окна h (пустая строка '' — пропустить)."""
    rows = table_rows(h)
    l, t, _, _ = win32gui.GetWindowRect(h); ox, oy = win32gui.ClientToScreen(h, (0, 0))
    done = []
    for (y, x), v in zip(rows, values):
        if v is None or v == '-':
            continue
        cx, cy = x - (ox - l), y - (oy - t)
        hc, px_, py_ = child_at(h, cx, cy)
        click_xy(hc, px_, py_)
        e = None
        for _ in range(10):
            time.sleep(0.08)
            cand = []
            win32gui.EnumChildWindows(h, lambda c, _: cand.append(c) if (win32gui.IsWindowVisible(c) and
                                      win32gui.GetClassName(c) in ('TEdit', 'TMaskEdit')) else None, None)
            for c in cand:
                el, et, er, eb = win32gui.GetWindowRect(c)
                if et - 4 <= t + y <= eb + 4:
                    e = c
            if e:
                break
        if not e:
            done.append([y, v, 'no edit']); continue
        win32gui.SendMessage(e, win32con.WM_SETTEXT, 0, str(v))
        done.append([y, v])
    # зафиксировать последнее значение — щелчок в первую строку
    if rows:
        y, x = rows[0]; hc, px_, py_ = child_at(h, x - (ox - l), y - (oy - t)); click_xy(hc, px_, py_)
        time.sleep(0.1)
    return rows, done


def overlay_edit(hform, hgrid):
    """Видимый редактор (TEdit/TInplaceEdit/TMaskEdit) поверх сетки."""
    gl, gt, gr, gb = win32gui.GetWindowRect(hgrid)
    res = []
    def cb(c, _):
        if win32gui.IsWindowVisible(c) and win32gui.GetClassName(c) in ('TEdit', 'TInplaceEdit', 'TMaskEdit', 'TComboBox'):
            l, t, r, b = win32gui.GetWindowRect(c)
            if l >= gl - 2 and t >= gt - 2 and r <= gr + 2 and b <= gb + 2:
                res.append(c)
    win32gui.EnumChildWindows(hform, cb, None)
    return res[0] if res else None


def grid_input(hform, hgrid, cells):
    """cells: [((row, col), value)]; row/col — номера строк/столбцов сетки как на экране (с 0, включая столбец-номер)."""
    geo = grid_geometry(hgrid)
    done = []
    for (r, c), v in cells:
        if r >= len(geo['rows']) or c >= len(geo['cols']):
            die('ячейка %d,%d вне сетки' % (r, c), geometry=geo)
        x = (geo['cols'][c][0] + geo['cols'][c][1]) // 2
        y = (geo['rows'][r][0] + geo['rows'][r][1]) // 2
        click_xy(hgrid, x, y)
        e = None
        for _ in range(15):
            time.sleep(0.1)
            e = overlay_edit(hform, hgrid)
            if e:
                el, et, er, eb = win32gui.GetWindowRect(e)
                gx, gy = win32gui.ScreenToClient(hgrid, ((el + er) // 2, (et + eb) // 2))
                if abs(gy - y) <= 14 and geo['cols'][c][0] - 4 <= gx <= geo['cols'][c][1] + 4:
                    break
                e = None
        if not e:
            die('ячейка %d,%d не открылась для ввода (не та строка/порядок не подтверждён?)' % (r, c), geometry=geo, done=done)
        win32gui.SendMessage(e, win32con.WM_SETTEXT, 0, str(v))
        done.append([r, c, str(v)])
    return geo, done


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd')
    ap.add_argument('args', nargs='*')
    ap.add_argument('--pid', type=int)
    ap.add_argument('--win')
    ap.add_argument('--ctl')
    ap.add_argument('--xy')
    ap.add_argument('--wxy', help='X,Y в пикселях снимка окна (shot), а не клиентской области')
    ap.add_argument('--right', action='store_true')
    ap.add_argument('--double', action='store_true')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--controls', action='store_true')
    ap.add_argument('--prev', default='yes', choices=['yes', 'no'])
    ap.add_argument('--dir')
    ap.add_argument('--timeout', type=float, default=10)
    ap.add_argument('--nocommit', action='store_true', help='set: не нажимать Tab после ввода')
    ap.add_argument('--ok', help='после ввода нажать кнопку (текст/класс#N/hwnd)')
    ap.add_argument('--delay', type=float, default=0.8, help='пауза после действия перед выводом окон')
    a = ap.parse_args()
    c = a.cmd

    if c == 'launch':
        out(launch(a.args[0], a.prev, a.dir)); return
    if c == 'ps':
        out(dict(ok=True, running=[dict(pid=p, exe=n) for p, n in tau_pids()])); return

    pid = get_pid(a)
    after = lambda extra=None: out(dict(ok=True, **(extra or {}), windows=[winfo(h) for h in top_windows(pid)],
                                        dialogs=[dialog_info(h) for h in dialogs(pid)]))

    if c == 'ls':
        out(dict(ok=True, pid=pid, windows=[winfo(h, a.controls) for h in top_windows(pid, not a.all)])); return
    if c == 'menu':
        h = find_win(pid, a.win)
        if not a.args:
            items, src = popup_items(pid, h)
            out(dict(ok=True, window=winfo(h), source=src, items=items)); return
        it = run_menu(pid, h, a.args[0]); time.sleep(a.delay); after(dict(done=it['path'])); return
    if c == 'click':
        h = find_win(pid, a.win)
        if a.ctl:
            hc = find_ctl(h, a.ctl)
            if win32gui.GetClassName(hc) in ('TButton', 'TBitBtn', 'Button', 'TCheckBox', 'TRadioButton') and not a.right:
                press_button(hc)
            else:
                l, t, r, b = win32gui.GetClientRect(hc); click_xy(hc, r // 2, b // 2, a.right, a.double)
        else:
            x, y = map(int, (a.xy or a.wxy).split(','))
            if a.wxy:  # координаты по снимку окна (shot включает рамку и заголовок)
                l, t, _, _ = win32gui.GetWindowRect(h); ox, oy = win32gui.ClientToScreen(h, (0, 0))
                x, y = x - (ox - l), y - (oy - t)
            hc, cx, cy = child_at(h, x, y)
            click_xy(hc, cx, cy, a.right, a.double)
        time.sleep(a.delay); after(); return
    if c == 'set':
        h = find_win(pid, a.win); hc = find_ctl(h, a.ctl)
        HwndWrapper(hc).set_edit_text(a.args[0]) if win32gui.GetClassName(hc) != 'TComboBox' else \
            win32gui.SendMessage(hc, win32con.WM_SETTEXT, 0, a.args[0])
        time.sleep(0.2); out(dict(ok=True, text=gettext(hc))); return
    if c == 'select':
        h = find_win(pid, a.win); hc = find_ctl(h, a.ctl); w = HwndWrapper(hc)
        cl = win32gui.GetClassName(hc)
        from pywinauto.controls.win32_controls import ListBoxWrapper, ComboBoxWrapper
        ww = ComboBoxWrapper(hc) if 'Combo' in cl else ListBoxWrapper(hc)
        item = int(a.args[0]) if a.args[0].isdigit() and a.args[0] not in ww.item_texts() else a.args[0]
        ww.select(item)
        # уведомить Delphi (OnClick/OnChange)
        code = 1  # LBN_SELCHANGE / CBN_SELCHANGE
        win32gui.SendMessage(win32gui.GetParent(hc), win32con.WM_COMMAND,
                             win32api.MAKELONG(win32gui.GetDlgCtrlID(hc) & 0xFFFF, code), hc)
        time.sleep(a.delay); after(dict(items=ww.item_texts())); return
    if c == 'radio':
        h = find_win(pid, a.win); hg = find_ctl(h, a.ctl)
        btns = []
        win32gui.EnumChildWindows(hg, lambda x, _: btns.append(x) if win32gui.GetClassName(x) in ('TGroupButton', 'TRadioButton') else None, None)
        btns.sort(key=lambda x: (win32gui.GetWindowRect(x)[1], win32gui.GetWindowRect(x)[0]))
        press_button(btns[int(a.args[0])])
        time.sleep(a.delay); after(dict(buttons=[win32gui.GetWindowText(b) for b in btns])); return
    if c == 'keys':
        h = find_win(pid, a.win); hc = find_ctl(h, a.ctl) if a.ctl else h
        HwndWrapper(hc).send_keystrokes(a.args[0]); time.sleep(a.delay); after(); return
    if c == 'grid':
        h = find_win(pid, a.win); hc = find_ctl(h, a.ctl or 'TStringGrid')
        cells = []
        for arg in a.args:  # "R,C=значение"
            rc, v = arg.split('=', 1)
            r_, c_ = map(int, rc.split(','))
            cells.append(((r_, c_), v))
        geo, done = grid_input(h, hc, cells)
        if a.ok:
            press_button(find_ctl(h, a.ok))
        time.sleep(a.delay); after(dict(entered=done, geometry=geo)); return
    if c == 'fill':
        # значения построчно в нарисованную таблицу (Значения, Частоты, Нач. значение Xo, Время регулирования …)
        h = find_win(pid, a.win)
        rows, done = fill_form(h, a.args, pid)
        if a.ok:
            press_button(find_ctl(h, a.ok))
        time.sleep(a.delay); after(dict(rows=rows, entered=done)); return
    if c == 'geometry':
        h = find_win(pid, a.win); hc = find_ctl(h, a.ctl or 'TStringGrid')
        out(dict(ok=True, grid=hex(hc), geometry=grid_geometry(hc))); return
    if c == 'answer':
        dl = dialogs(pid)
        if not dl:
            out(dict(ok=True, dialogs=[])); return
        info = dialog_info(dl[0])
        if not a.args:
            out(dict(ok=True, dialogs=[dialog_info(h) for h in dl])); return
        lat = str.maketrans('ОКАВСЕНМРТХокавсенмртх', 'OKABCEHMPTXokabcehmptx')  # «ОК» кириллицей в системных окнах
        want = a.args[0].lower().replace('&', '').translate(lat)
        syn = {'yes': 'да', 'no': 'нет', 'cancel': 'отмена', 'да': 'yes', 'нет': 'no', 'отмена': 'cancel'}
        for ctl in info['controls']:
            t = ctl['text'].replace('&', '').lower().translate(lat)
            if ctl['cls'] in ('TButton', 'Button', 'TBitBtn') and (t == want or t == syn.get(want)):
                press_button(int(ctl['hwnd'], 16)); time.sleep(a.delay); after(dict(pressed=ctl['text'])); return
        die('кнопка не найдена: %s' % a.args[0], dialog=info)
    if c == 'shot':
        target = a.args[0]
        if a.all:
            os.makedirs(target, exist_ok=True)
            files = []
            for i, h in enumerate(top_windows(pid)):
                nm = re.sub(r'[^\w\-]+', '_', win32gui.GetWindowText(h) or win32gui.GetClassName(h)).strip('_')[:40]
                files.append(shot(h, os.path.join(target, '%02d_%s.png' % (i, nm))))
            out(dict(ok=True, files=files)); return
        h = find_win(pid, a.win); out(dict(ok=True, file=shot(h, target), window=winfo(h))); return
    if c == 'tofile':
        # в окне-таблице/формуле: меню «В файл / на принтер» -> «в файл» + «перезаписать|дописать» -> OK; прочитать <PROG>.tab
        h = find_win(pid, a.win)
        run_menu(pid, h, 'В файл')
        t0 = time.time(); hu = None
        while time.time() - t0 < 5 and not hu:
            time.sleep(0.2)
            hu = next((x for x in top_windows(pid) if win32gui.GetClassName(x) == 'TUstForm'), None)
        if not hu:
            die('не появилось окно «Проверьте установки»', windows=[winfo(x) for x in top_windows(pid)])
        press_button(find_ctl(hu, 'в файл')); time.sleep(0.1)
        press_button(find_ctl(hu, 'дописать' if a.args and a.args[0] == 'append' else 'перезаписать')); time.sleep(0.1)
        exe = win32process.GetModuleFileNameEx(win32api.OpenProcess(0x0410, False, pid), 0)
        tab = os.path.splitext(exe)[0] + '.tab'
        m0 = os.path.getmtime(tab) if os.path.exists(tab) else 0
        press_button(find_ctl(hu, 'OK'))
        t0 = time.time()
        while time.time() - t0 < 5 and (not os.path.exists(tab) or os.path.getmtime(tab) == m0):
            time.sleep(0.2)
        time.sleep(a.delay)
        # информационное сообщение «записано в файл» — закрыть
        for dl in dialogs(pid):
            ok = [x for x in dialog_info(dl)['controls'] if x['text'].replace('&', '') == 'OK']
            if ok and win32gui.GetWindowText(dl) == 'Information':
                press_button(int(ok[0]['hwnd'], 16)); time.sleep(0.3)
        text = open(tab, encoding='cp1251', errors='replace').read() if os.path.exists(tab) else None
        out(dict(ok=text is not None, file=tab, text=text, dialogs=[dialog_info(x) for x in dialogs(pid)])); return
    if c == 'wait':
        t0 = time.time()
        while time.time() - t0 < a.timeout:
            for h in top_windows(pid):
                if a.win in (win32gui.GetClassName(h),) or a.win.lower() in win32gui.GetWindowText(h).lower():
                    out(dict(ok=True, window=winfo(h))); return
            time.sleep(0.2)
        die('не дождались окна %s' % a.win, windows=[winfo(h) for h in top_windows(pid)])
    if c == 'close':
        os.kill(pid, 9); out(dict(ok=True, killed=pid)); return
    die('неизвестная команда %s' % c)


if __name__ == '__main__':
    main()
