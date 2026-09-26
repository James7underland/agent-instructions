"""Автообход программы ТАУ-3: вызвать каждый пункт главного меню, принять диалоги по умолчанию, снять все окна.

python crawl.py PROG [--out DIR] [--only "подстрока"] [--skip "a|b"] [--prev yes|no] [--keep]
Результат: DIR/PROG/NN_<пункт>/*.png, DIR/PROG/report.json, DIR/PROG/sheet.png (контактный лист миниатюр).
Не нажимает «Выход», «на принтер», «Запомнить вариант» (если не --only). Процесс в конце убивается (--keep — оставить).
"""
import sys, os, time, json, re, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tau
tau.QUIET = True
from tau import (win32gui, win32con, top_windows, winfo, dialogs, dialog_info, press_button, find_ctl, shot,
                 popup_items, run_menu, launch, gettext)

BLACK = re.compile(r'выход|принтер|печат', re.I)
# формы-таблицы, которые заполняем, чтобы графики были содержательными (буквы A,B,L,K…=1; X°=1; tрег=10)
FILL = {'TValForm': '1', 'TXForm': '1', 'TTimForm': '10'}
MODAL_OK = ('OK', 'Ok', '&OK', 'Да', '&Yes', 'Yes', 'Продолжить')


def safe(s):
    return re.sub(r'[^\w\-]+', '_', s).strip('_')[:40]


def handle_modals(pid, main, d, log, maxsteps=10):
    """Пока есть модальное окно — снять и нажать OK/Да. Возвращает список снятых окон."""
    seen = []
    pressed = set()
    for step in range(maxsteps):
        time.sleep(0.6)
        ws = top_windows(pid)
        if not ws:
            break
        top = ws[0]
        cls = win32gui.GetClassName(top)
        main_disabled = not win32gui.IsWindowEnabled(main)
        if top in pressed:
            break  # окно не закрылось по OK — это рабочая форма, а не диалог
        if cls in tau.DIALOG_CLASSES or (main_disabled and top != main and cls not in ('TGraForm',)):
            pressed.add(top)
            filled = None
            if cls in FILL:
                try:
                    rows = tau.table_rows(top)
                    vals = [FILL[cls]] * len(rows)
                    tau.fill_form(top, vals, pid); filled = vals
                except Exception as e:
                    filled = repr(e)
            fn = shot(top, os.path.join(d, 'm%02d_%s.png' % (step, safe(cls + '_' + win32gui.GetWindowText(top)))))
            info = winfo(top, True)
            btns = [c for c in info['controls'] if c['cls'] in ('TButton', 'Button', 'TBitBtn')]
            pick = None
            for want in MODAL_OK:
                pick = next((b for b in btns if b['text'].replace('&', '') == want.replace('&', '')), None)
                if pick:
                    break
            seen.append(dict(cls=cls, title=win32gui.GetWindowText(top), shot=fn,
                             buttons=[b['text'] for b in btns], pressed=pick['text'] if pick else None, filled=filled,
                             edits=[c['text'] for c in info['controls'] if c['cls'] in ('TEdit', 'TComboBox')]))
            if pick:
                press_button(int(pick['hwnd'], 16))
                continue
            # нет OK: закрыть окно
            win32gui.PostMessage(top, win32con.WM_CLOSE, 0, 0)
            continue
        break
    return seen


def close_extra(pid, main, keep):
    for _ in range(3):
        extra = [h for h in top_windows(pid) if h != main and h not in keep]
        if not extra:
            return
        for h in extra:
            if win32gui.GetClassName(h) in tau.DIALOG_CLASSES:
                info = dialog_info(h)
                b = next((c for c in info['controls'] if c['text'].replace('&', '') in ('OK', 'Yes', 'Да', 'No', 'Нет')), None)
                if b:
                    press_button(int(b['hwnd'], 16)); continue
            win32gui.PostMessage(h, win32con.WM_CLOSE, 0, 0)
        time.sleep(0.6)
        # закрытие могло вызвать вопрос
        for h in dialogs(pid):
            info = dialog_info(h)
            b = next((c for c in info['controls'] if c['text'].replace('&', '') in ('OK', 'Yes', 'Да')), None)
            if b:
                press_button(int(b['hwnd'], 16))
        time.sleep(0.3)


def sheet(files, out, cols=4, tw=420):
    from PIL import Image, ImageDraw, ImageFont
    ims = []
    for f in files:
        try:
            im = Image.open(f).convert('RGB')
            im.thumbnail((tw, tw))
            ims.append((os.path.relpath(f, os.path.dirname(out)), im))
        except Exception:
            pass
    if not ims:
        return None
    rows = (len(ims) + cols - 1) // cols
    ch = max(i.size[1] for _, i in ims) + 18
    S = Image.new('RGB', (cols * (tw + 8), rows * ch), 'white')
    dr = ImageDraw.Draw(S)
    try:
        font = ImageFont.truetype('arial.ttf', 12)
    except Exception:
        font = None
    for k, (name, im) in enumerate(ims):
        x, y = (k % cols) * (tw + 8), (k // cols) * ch
        S.paste(im, (x, y + 16))
        dr.text((x + 2, y + 1), name[-60:], fill='black', font=font)
    S.save(out)
    return out


def crawl(prog, outdir, only=None, skip=None, prev='yes', keep=False):
    d0 = os.path.join(outdir, prog.lower())
    os.makedirs(d0, exist_ok=True)
    L = launch(prog, prev)
    pid = L['pid']
    rep = dict(prog=prog, launch=L, items=[])
    time.sleep(0.5)
    mains = [h for h in top_windows(pid) if win32gui.GetClassName(h) in ('TMForm', 'TMenuForm')]
    if not mains:
        rep['error'] = 'нет главного окна'; json.dump(rep, open(os.path.join(d0, 'report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        return rep
    main = mains[0]
    files = [shot(main, os.path.join(d0, '00_main.png'))]
    items, src = popup_items(pid, main)
    rep['menu'] = items; rep['menu_source'] = src
    n = 0
    for it in items:
        if it['id'] is None or it['disabled']:
            continue
        if only and not re.search(only, it['path'], re.I):
            continue
        if (not only and BLACK.search(it['path'])) or (skip and re.search(skip, it['path'], re.I)):
            continue
        n += 1
        d = os.path.join(d0, '%02d_%s' % (n, safe(it['path'])))
        os.makedirs(d, exist_ok=True)
        rec = dict(path=it['path'])
        before = set(top_windows(pid))
        try:
            win32gui.PostMessage(tau.util_window(pid)[0] if src == 'popup' else main, win32con.WM_COMMAND, it['id'], 0)
            rec['modals'] = handle_modals(pid, main, d, [])
            time.sleep(1.0)
            rec['modals'] += handle_modals(pid, main, d, [])
            new = [h for h in top_windows(pid) if h not in before]
            rec['windows'] = []
            for k, h in enumerate(new):
                w = winfo(h, True)
                w['shot'] = shot(h, os.path.join(d, 'w%02d_%s.png' % (k, safe(w['title'] or w['cls']))))
                files.append(w['shot'])
                try:
                    w['menu'] = [x['path'] for x in popup_items(pid, h)[0]]
                except (SystemExit, tau.TauError):
                    w['menu'] = None
                w['controls'] = [dict(cls=c['cls'], text=c['text']) for c in w['controls'] if c['text']][:40]
                rec['windows'].append(w)
            files += [m['shot'] for m in rec['modals']]
            # главное окно могло измениться (схема)
            rec['main_after'] = shot(main, os.path.join(d, 'main_after.png'))
        except (SystemExit, tau.TauError):
            rec['error'] = 'SystemExit (меню/окно не найдено)'
        except Exception as e:
            rec['error'] = repr(e)
        close_extra(pid, main, before)
        rep['items'].append(rec)
        if not win32gui.IsWindow(main):
            rep['crashed_after'] = it['path']; break
    rep['sheet'] = sheet(files, os.path.join(d0, 'sheet.png'))
    json.dump(rep, open(os.path.join(d0, 'report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
    if not keep:
        try:
            os.kill(pid, 9)
        except Exception:
            pass
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('prog')
    ap.add_argument('--out', default=os.path.join(os.path.dirname(tau.DEF_DIR), 'crawl'))
    ap.add_argument('--only'); ap.add_argument('--skip'); ap.add_argument('--prev', default='yes')
    ap.add_argument('--keep', action='store_true')
    a = ap.parse_args()
    rep = crawl(a.prog, a.out, a.only, a.skip, a.prev, a.keep)
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(dict(prog=rep['prog'], items=[(i['path'], [w['title'] for w in i.get('windows', [])],
                                                     [m['title'] for m in i.get('modals', [])], i.get('error'))
                                                    for i in rep['items']], sheet=rep.get('sheet'),
                          crashed=rep.get('crashed_after')), ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
