"""Каталог библиотеки звеньев программы со структурной схемой (CONTROL, CASCAD, IMPULS, LINSYS2/3, NLINSYS …).

python elements.py PROG "W=343,101" "R=226,101" ... [--pid PID] [--out DIR] [--max 30]
  Буква=X,Y — координаты буквы звена на СНИМКЕ главного окна (tau.py shot --win main).
Для каждой буквы: «Формирование элементов схемы» → щелчок по букве → перебор типов стрелкой ▶ окна «Элемент схемы»
до повтора; для каждого типа — PNG (формула + окно «Параметры»). Номер типа = номер в VRT (второе поле строки
звена): отсчёт от выбранного (*) типа из VRT. Итог: DIR/<prog>/<буква>_NN.png и index.md.
После перебора программа НЕ сохраняет изменения (процесс убивается, выбор типа не подтверждался OK).
"""
import sys, os, time, argparse, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tau
from tau import win32gui, top_windows, shot, run_menu, click_xy, child_at
import vrt as V
tau.QUIET = True


def win(pid, cls):
    return next((h for h in top_windows(pid) if win32gui.GetClassName(h) == cls), None)


def click_w(h, x, y):
    l, t, _, _ = win32gui.GetWindowRect(h); ox, oy = win32gui.ClientToScreen(h, (0, 0))
    hc, cx, cy = child_at(h, x - (ox - l), y - (oy - t)); click_xy(hc, cx, cy)


def combo(a, b, fn):
    from PIL import Image
    A, B = Image.open(a), Image.open(b) if b else None
    W = A.width + (B.width if B else 0); H = max(A.height, B.height if B else 0)
    c = Image.new('RGB', (W, H), 'white'); c.paste(A, (0, 0))
    if B: c.paste(B, (A.width, 0))
    c.save(fn)
    # сравниваем только область формулы (без нижней панели с OK/«Вариант выбран»/стрелками)
    return hashlib.md5(A.crop((0, 0, A.width, int(A.height * 0.7))).tobytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('prog'); ap.add_argument('letters', nargs='+')
    ap.add_argument('--pid', type=int); ap.add_argument('--max', type=int, default=30)
    ap.add_argument('--out', default=os.path.join(tau.SKILL, 'references', 'elements'))
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    pid = a.pid or tau.launch(a.prog)['pid']
    main_w = next(h for h in top_windows(pid) if win32gui.GetClassName(h) == 'TMForm')
    d = os.path.join(a.out, a.prog.lower()); os.makedirs(d, exist_ok=True)
    # выбранные типы из VRT
    sel, codes = {}, {}
    vp = [os.path.join(tau.DEF_DIR, f) for f in os.listdir(tau.DEF_DIR) if f.lower() == a.prog.lower() + '.vrt']
    if vp:
        nw = V.NAME_WIDTH.get(a.prog.lower(), 1)
        for e in V.parse_elem(V.read(vp[0]), nw):
            nm = e['name'].replace('\\_', '')
            if e['type'].isdigit():
                codes.setdefault(nm, set()).add(int(e['type']))
            if e['selected']:
                sel[nm] = int(e['type'])
    run_menu(pid, main_w, 'Формирование элементов схемы'); time.sleep(0.8)
    idx = ['# Библиотека звеньев %s' % a.prog.upper(), '',
           'Тип N — номер в VRT (поле после имени звена). Слева — формула/график звена, справа — окно «Параметры»',
           '(порядок строк = порядок полей VRT).', '']
    tmp = os.path.join(tau.SHOTDIR, 'el')
    os.makedirs(tmp, exist_ok=True)
    for spec in a.letters:
        name, xy = spec.split('=')
        x, y = map(int, xy.split(','))
        click_w(main_w, x, y); time.sleep(0.8)
        he = win(pid, 'TElemForm')
        if not he:
            idx.append('- %s: окно «Элемент схемы» не открылось' % name); continue
        hp = win(pid, 'TParamForm') or win(pid, 'TParmForm')
        t0 = sel.get(name, 1)
        seen = []
        for k in range(a.max):
            e_png = shot(he, os.path.join(tmp, 'e.png'))
            p_png = shot(hp, os.path.join(tmp, 'p.png')) if hp and win32gui.IsWindowVisible(hp) else None
            fn = os.path.join(d, '_tmp.png')
            hsh = combo(e_png, p_png, fn)
            if hsh in seen:
                os.remove(fn); break
            seen.append(hsh)
            n = len(seen)
            os.replace(fn, os.path.join(d, '%s_k%02d.png' % (name, n - 1)))
            # стрелка ▶ — правая половина TUpDown
            try:
                ud = tau.find_ctl(he, 'TUpDown')
            except tau.TauError:
                break  # единственный тип — стрелок нет
            l, t, r, b = win32gui.GetClientRect(ud)
            click_xy(ud, r * 3 // 4, b // 2); time.sleep(0.5)
            hp = win(pid, 'TParamForm') or win(pid, 'TParmForm')
        N = len(seen)
        # коды типов в VRT — непрерывный диапазон [c0, c0+N-1]; c0=1, если туда попадают все коды из VRT, иначе min
        cs = codes.get(name, {t0})
        c0 = 1 if max(cs) <= N else min(cs)
        # k-й снимок (листаем ▶ от выбранного) = код c0 + ((t0 - c0 + k) mod N)
        files = []
        for k in range(N):
            typ = c0 + (t0 - c0 + k) % N
            src = os.path.join(d, '%s_k%02d.png' % (name, k)); dst = os.path.join(d, '%s_%02d.png' % (name, typ))
            os.replace(src, dst); files.append((typ, dst))
        idx.append('## %s — %d типов, коды VRT %d…%d (выбран в штатном VRT: %s; коды в VRT: %s)' % (
            name, N, c0, c0 + N - 1, sel.get(name, '?'), sorted(cs)))
        for typ, f in sorted(files):
            idx.append('- тип %d: ![](%s)' % (typ, os.path.basename(f)))
        idx.append('')
        print(name, N, 'типов')
    open(os.path.join(d, 'index.md'), 'w', encoding='utf-8').write('\n'.join(idx) + '\n')
    if not a.pid:
        os.kill(pid, 9)
    print('ok', d)


if __name__ == '__main__':
    main()
