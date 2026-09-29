#!/usr/bin/env python3
"""gui.py — управление GUI Symmetry (UI64\\Symmetry.exe): запуск с HTTP-сервером, команды через REST,
сохранение, снимки окна/PFD, UI Automation (WPF) без мыши и без фокуса.

  launch [CASE.vsym] [--port 18686] [--size max|ШxВ]  запустить свой экземпляр (лицензия + --HTTPServer),
                                                  окно — НА ВЕСЬ ЭКРАН (по умолчанию max); состояние
                                                  в %TEMP%\\symmetry_gui.json (pid, port)
  eval CMD [CMD ...] [--no-solve]                 команды языка Symmetry в живой GUI (JSON API Eval, solve=1);
                                                  печатает ответ движка (msg) — для запросов вида "/S1.Out"
  run FILE.tst [--no-solve]                       то же построчно из файла (пересчёт после каждой команды)
  get PATH [PATH ...]                             /api/values/<path> (числа в единицах GUI)
  case OUT.json                                   весь кейс JSON (/api/case): объекты, переменные, координаты PFD
  recall CASE.vsym                                открыть кейс в работающем GUI
  save                                            Сохранить (кнопка Save + «Yes» на перезапись) — в тот же файл
  shot OUT.png [--pfd] [--size max|ШxВ]          снимок главного окна (PrintWindow) или только области PFD
  popups [OUTDIR]                                 все окна процесса: заголовки + снимки (диалоги, сообщения)
  answer TEXT                                     нажать кнопку TEXT (Yes/No/OK/…) в диалоге процесса
  ui [--depth 6] [--win TITLE]                    дерево UI Automation главного окна (или окна по заголовку)
  click NAME [--nth 0] [--type Button]            Invoke/Select/Toggle элемента по имени или automation_id
  close [--force]                                 закрыть только свой экземпляр (по pid из состояния)
  build MODEL.tst OUT.vsym [--shot pfd.png]       кейс с настоящей PFD: аппараты строятся в GUI (координаты —
                                                  visio_layout), динамика (после /ActiveEngine = 2) — движком
Порт по умолчанию 18686. Из Git Bash пути вида /S1.Out портятся — скрипт их чинит сам.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sym import unmangle  # noqa: E402

EXE = r"C:\Program Files\VMG\Symmetry\UI64\Symmetry.exe"
STATE = os.path.join(tempfile.gettempdir(), "symmetry_gui.json")
LICENSE = os.environ.get("SLBSLS_LICENSE_FILE", "27000@localhost")


# ---------- состояние ----------
def load_state():
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except Exception:
        return {}


def save_state(st):
    json.dump(st, open(STATE, "w", encoding="utf-8"))


def base_url(st=None):
    st = st or load_state()
    return f"http://localhost:{st.get('port', 18686)}/api"


def http(method, path, body=None, ctype="application/json", timeout=600):
    data = None
    if body is not None:
        data = body if isinstance(body, bytes) else (json.dumps(body) if ctype == "application/json" else body).encode("utf-8")
    req = urllib.request.Request(base_url() + path, data=data, method=method, headers={"Content-Type": ctype})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def api_eval(cmd, solve=True):
    args = {"cmd": cmd}
    if solve:
        args["solve"] = 1
    return http("POST", "/actions/json", {"call": "Eval", "args": args})


# ---------- окна ----------
def _pid():
    st = load_state()
    if not st.get("pid"):
        sys.exit("GUI не запущен через gui.py launch (нет pid в состоянии)")
    return int(st["pid"])


def proc_windows(pid):
    import win32gui
    import win32process
    res = []

    def cb(h, _):
        if win32gui.IsWindowVisible(h) and win32process.GetWindowThreadProcessId(h)[1] == pid:
            t = win32gui.GetWindowText(h)
            if t != "GlowWindow":
                res.append((h, t))
    win32gui.EnumWindows(cb, None)
    return res


def main_hwnd(pid):
    for h, t in proc_windows(pid):
        if t.startswith("Symmetry"):
            return h
    return None


def set_size(hwnd, size):
    """size = "max" (развернуть на весь экран — так по умолчанию открываем Symmetry) или "ШxВ"."""
    import win32con
    import win32gui
    ctypes.windll.user32.SetProcessDPIAware()
    if str(size).lower() in ("max", "full", "maximize"):
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
    else:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        W, H = map(int, str(size).lower().split("x"))
        win32gui.MoveWindow(hwnd, 0, 0, W, H, True)


def print_window(hwnd, out, crop=None):
    import win32gui
    import win32ui
    from PIL import Image
    ctypes.windll.user32.SetProcessDPIAware()
    l, t, r, b = win32gui.GetWindowRect(hwnd)
    w, h = r - l, b - t
    hdc = win32gui.GetWindowDC(hwnd)
    dc = win32ui.CreateDCFromHandle(hdc)
    m = dc.CreateCompatibleDC()
    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(dc, w, h)
    m.SelectObject(bmp)
    ctypes.windll.user32.PrintWindow(hwnd, m.GetSafeHdc(), 2)
    info = bmp.GetInfo()
    im = Image.frombuffer("RGB", (info["bmWidth"], info["bmHeight"]), bmp.GetBitmapBits(True), "raw", "BGRX", 0, 1)
    win32gui.DeleteObject(bmp.GetHandle()); m.DeleteDC(); dc.DeleteDC(); win32gui.ReleaseDC(hwnd, hdc)
    if crop:
        x0, y0, x1, y1 = crop
        im = im.crop((x0 - l, y0 - t, x1 - l, y1 - t))
    im.save(out)
    return im.size


def uia_main(pid):
    from pywinauto import Desktop
    for w in Desktop(backend="uia").windows(process=pid):
        if w.window_text().startswith("Symmetry"):
            return w
    raise SystemExit("главное окно не найдено")


def uia_all_windows(pid):
    from pywinauto import Desktop
    res = []
    for w in Desktop(backend="uia").windows(process=pid):
        res.append(w)
        for c in w.children(control_type="Window"):
            if c.window_text() != "GlowWindow":
                res.append(c)
    return res


def walk(el, depth=12):
    """Рекурсивный обход через children() — descendants() в этом WPF-окне теряет часть узлов (VisioHost)."""
    yield el
    if depth <= 0:
        return
    try:
        kids = el.children()
    except Exception:
        return
    for c in kids:
        yield from walk(c, depth - 1)


def activate(el):
    for fn in ("invoke", "select", "toggle", "expand"):
        try:
            getattr(el, fn)()
            return fn
        except Exception:
            continue
    for iface, meth in (("iface_invoke", "Invoke"), ("iface_toggle", "Toggle"),
                        ("iface_selection_item", "Select"), ("iface_expand_collapse", "Expand")):
        try:
            getattr(getattr(el, iface), meth)()
            return f"{iface}.{meth}"
        except Exception:
            continue
    raise RuntimeError("элемент не поддерживает Invoke/Select/Toggle/Expand")


def dump(el, depth, d=0, out=None):
    ei = el.element_info
    name = (ei.name or "").replace("\n", " ")[:70]
    line = "  " * d + f"{ei.control_type} '{name}' id={ei.automation_id!r} cls={ei.class_name}"
    print(line)
    if d < depth:
        for c in el.children():
            dump(c, depth, d + 1)


# ---------- команды ----------
def cmd_launch(a):
    st = load_state()
    if st.get("pid") and main_hwnd(int(st["pid"])):
        print(json.dumps({"already": st}, ensure_ascii=False)); return
    env = dict(os.environ, SLBSLS_LICENSE_FILE=LICENSE)
    args = [EXE] + ([os.path.abspath(a.case)] if a.case else []) + ["--HTTPServer", "2", "--HTTPServer_Port", str(a.port)]
    p = subprocess.Popen(args, env=env, cwd=os.path.dirname(EXE))
    st = {"pid": p.pid, "port": a.port, "case": os.path.abspath(a.case) if a.case else None, "t": time.time()}
    save_state(st)
    t0 = time.time()
    ok_http = False
    while time.time() - t0 < a.wait:
        time.sleep(2)
        if p.poll() is not None:
            sys.exit(f"Symmetry завершился (код {p.returncode}) — лицензия? см. known-issues")
        titles = [t for _, t in proc_windows(p.pid)]
        if any(t.startswith("Symmetry License") or "License" in t for t in titles):
            print("!! окно лицензии:", titles)
        if main_hwnd(p.pid):
            try:
                http("GET", "/values/ActiveEngine", timeout=5)
                ok_http = True
                break
            except Exception:
                pass
    h = main_hwnd(p.pid)
    if h and a.size:
        set_size(h, a.size)
    print(json.dumps({"pid": p.pid, "port": a.port, "window": bool(h), "http": ok_http,
                      "sec": round(time.time() - t0, 1)}, ensure_ascii=False))


def cmd_eval(a):
    for c in a.cmds:
        c = unmangle(c)
        r = api_eval(c, solve=not a.no_solve)
        msg = r.get("msg")
        print(f"> {c}" + ("" if r.get("status") == 0 else f"   !! status={r.get('status')} {msg}"))
        if msg and r.get("status") == 0:
            print(str(msg).replace("\\n", "\n").rstrip())


def cmd_run(a):
    lines = [l.rstrip("\r\n") for l in open(a.file, encoding="utf-8-sig")]
    n = 0
    for l in lines:
        c = l.strip()
        if not c or c.startswith("#"):
            continue
        r = api_eval(c, solve=not a.no_solve)   # без solve GUI может не применить часть команд (напр. units)
        n += 1
        if r.get("status") != 0:
            print(f"!! {c}: {r.get('msg')}")
        elif r.get("msg"):
            print(f"> {c}\n{r['msg']}")
    print(f"# команд: {n}")


def cmd_get(a):
    out = {}
    for p in a.paths:
        p = unmangle(p).lstrip("/")
        try:
            r = http("GET", "/values/" + urllib.request.quote(p))
            out["/" + p] = r.get("resp") if r.get("status") == 0 else {"error": r.get("msg")}
        except Exception as ex:
            out["/" + p] = {"error": str(ex)}
    print(json.dumps(out, ensure_ascii=False, indent=1))


def cmd_case(a):
    r = http("GET", "/case")
    json.dump(r.get("resp"), open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"case -> {a.out}")


def cmd_recall(a):
    r = http("POST", "/actions/recall", os.path.abspath(a.case), ctype="text/plain")
    print(r)


def cmd_save(a):
    pid = _pid()
    w = uia_main(pid)
    btns = [c for c in w.children() if c.element_info.class_name == "RibbonButton"
            and c.element_info.control_type == "Button"]
    if not btns:
        sys.exit("кнопка Save не найдена")
    st = load_state()
    f = st.get("case")
    m0 = os.path.getmtime(f) if f and os.path.exists(f) else None
    btns[0].invoke()
    for _ in range(20):
        time.sleep(0.5)
        for win in uia_all_windows(pid):
            if win.window_text() in ("Save Project",):
                for b in win.descendants(control_type="Button"):
                    if b.window_text() == "Yes":
                        b.invoke()
        if f and os.path.exists(f) and os.path.getmtime(f) != m0:
            print(f"saved -> {f}"); return
    print("!! не удалось подтвердить сохранение (новый кейс без имени? см. popups)")


def cmd_shot(a):
    pid = _pid()
    h = main_hwnd(pid)
    if not h:
        sys.exit("нет главного окна")
    if a.size:
        set_size(h, a.size)
        time.sleep(1.5)
    crop = None
    if a.pfd:
        ctypes.windll.user32.SetProcessDPIAware()
        w = uia_main(pid)
        hosts = [c for c in walk(w) if c.element_info.automation_id == "VisioHost"]
        if hosts:
            r = hosts[0].rectangle()
            crop = (r.left, r.top, r.right, r.bottom)
    size = print_window(h, a.out, crop)
    print(f"shot -> {a.out} {size}")


def cmd_popups(a):
    pid = _pid()
    outdir = a.outdir
    if outdir:
        os.makedirs(outdir, exist_ok=True)
    for i, (h, t) in enumerate(proc_windows(pid)):
        print(i, h, repr(t))
        if outdir:
            try:
                print_window(h, os.path.join(outdir, f"win{i}.png"))
            except Exception as ex:
                print("   shot err", ex)
    for win in uia_all_windows(pid):
        t = win.window_text()
        if not t.startswith("Symmetry |"):
            texts = [x.window_text() for x in win.descendants(control_type="Text") if x.window_text()][:10]
            btns = [x.window_text() for x in win.descendants(control_type="Button") if x.window_text()][:10]
            print(f"  dialog {t!r}: {texts} buttons={btns}")


def cmd_answer(a):
    pid = _pid()
    for win in uia_all_windows(pid):
        for b in win.descendants(control_type="Button"):
            if b.window_text() == a.text:
                activate(b)
                print(f"pressed {a.text!r} in {win.window_text()!r}")
                return
    sys.exit(f"кнопка {a.text!r} не найдена")


def cmd_ui(a):
    pid = _pid()
    if a.win:
        wins = [w for w in uia_all_windows(pid) if a.win in w.window_text()]
        if not wins:
            sys.exit("окно не найдено")
        dump(wins[0], a.depth)
    else:
        dump(uia_main(pid), a.depth)


def cmd_click(a):
    pid = _pid()
    cands = []
    for win in uia_all_windows(pid):
        for el in walk(win):
            ei = el.element_info
            if (ei.name == a.name or ei.automation_id == a.name) and (not a.type or ei.control_type == a.type):
                cands.append(el)
    if len(cands) <= a.nth:
        sys.exit(f"не найдено: {a.name!r} (найдено {len(cands)})")
    how = activate(cands[a.nth])
    print(f"{how}: {a.name!r} [{cands[a.nth].element_info.control_type}] из {len(cands)}")


def cmd_close(a):
    st = load_state()
    pid = st.get("pid")
    if not pid:
        print("нечего закрывать"); return
    r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True)
    if "symmetry.exe" not in r.stdout.lower():
        save_state({})
        print(f"pid {pid} уже не Symmetry.exe — ничего не закрываю"); return
    subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    save_state({})
    print(f"closed pid {pid}")


def cmd_build(a):
    """Скрипт .tst → кейс с настоящей PFD: шапка (units/thermo) — движком, аппараты — в GUI (рисуются фигуры и
    линии, координаты — visio_layout), динамика (с "/ActiveEngine = 2") — снова движком (PFD сохраняется)."""
    import re as _re
    import visio_layout
    lines = [l.rstrip("\r\n") for l in open(a.tst, encoding="utf-8-sig")]
    if not a.no_layout:
        lines = visio_layout.layout(lines)
    i_obj = next((i for i, l in enumerate(lines) if visio_layout.CREATE.match(l.strip())), len(lines))
    i_dyn = next((i for i, l in enumerate(lines) if _re.match(r"^\s*/?ActiveEngine\s*=\s*2", l.strip())), len(lines))
    head, body, dyn = lines[:i_obj], lines[i_obj:i_dyn], lines[i_dyn:]
    out = os.path.abspath(a.out)
    tmp = out + ".parts"
    os.makedirs(tmp, exist_ok=True)
    for name, part in (("head", head), ("body", ["units SI"] + body), ("dyn", dyn)):
        open(os.path.join(tmp, name + ".tst"), "w", encoding="utf-8").write("\n".join(part) + "\n")
    sym = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sym.py")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, sym, "run", os.path.join(tmp, "head.tst"), "--save", out],
                       capture_output=True, text=True, encoding="utf-8", env=env)
    print(f"# 1/3 шапка (термодинамика) движком -> {out}")
    a.case, a.port = out, a.port
    cmd_launch(a)
    n, bad = 0, 0
    for l in ["units SI"] + body:
        c = l.strip()
        if not c or c.startswith("#"):
            continue
        rr = api_eval(c, solve=True)
        n += 1
        if rr.get("status") != 0:
            bad += 1
            print(f"   !! {c}: {rr.get('msg')}")
    print(f"# 2/3 аппараты в GUI: команд {n}, ошибок {bad}")
    if a.shot:
        cmd_shot(argparse.Namespace(out=a.shot, pfd=True, size=None))
    cmd_save(a)
    cmd_close(argparse.Namespace(force=False))
    if any(l.strip() and not l.strip().startswith("#") for l in dyn):
        r = subprocess.run([sys.executable, sym, "run", "--recall", out, os.path.join(tmp, "dyn.tst"), "--save", out],
                           capture_output=True, text=True, encoding="utf-8", env=env)
        errs = [l for l in r.stdout.splitlines() if "!!" in l]
        print(f"# 3/3 динамика движком: {'ошибок ' + str(len(errs)) if errs else 'без ошибок'}")
        for e in errs[:10]:
            print("  ", e)
    print(f"# готово: {out}  (части скрипта — {tmp})")


def main():
    argv = [unmangle(x) for x in sys.argv[1:]]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("launch"); p.add_argument("case", nargs="?"); p.add_argument("--port", type=int, default=18686)
    p.add_argument("--wait", type=int, default=120); p.add_argument("--size", default="max")
    p = sub.add_parser("eval"); p.add_argument("cmds", nargs="+"); p.add_argument("--no-solve", action="store_true")
    p = sub.add_parser("run"); p.add_argument("file"); p.add_argument("--no-solve", action="store_true")
    p = sub.add_parser("get"); p.add_argument("paths", nargs="+")
    p = sub.add_parser("case"); p.add_argument("out")
    p = sub.add_parser("recall"); p.add_argument("case")
    sub.add_parser("save")
    p = sub.add_parser("shot"); p.add_argument("out"); p.add_argument("--pfd", action="store_true"); p.add_argument("--size")
    p = sub.add_parser("popups"); p.add_argument("outdir", nargs="?")
    p = sub.add_parser("answer"); p.add_argument("text")
    p = sub.add_parser("ui"); p.add_argument("--depth", type=int, default=6); p.add_argument("--win")
    p = sub.add_parser("click"); p.add_argument("name"); p.add_argument("--nth", type=int, default=0); p.add_argument("--type")
    p = sub.add_parser("close"); p.add_argument("--force", action="store_true")
    p = sub.add_parser("build"); p.add_argument("tst"); p.add_argument("out"); p.add_argument("--port", type=int, default=18686)
    p.add_argument("--wait", type=int, default=120); p.add_argument("--size", default="max")
    p.add_argument("--shot", help="снимок PFD после построения"); p.add_argument("--no-layout", action="store_true")
    a = ap.parse_args(argv)
    globals()["cmd_" + a.cmd](a)


if __name__ == "__main__":
    main()
