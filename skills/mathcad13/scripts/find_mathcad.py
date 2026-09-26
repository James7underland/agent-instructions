"""Найти установленный Mathcad 13 и инструменты скилла на этом компьютере. Печатает JSON.

Запускать в начале каждой задачи: пути у разных разработчиков разные, ничего не зашито.

    python find_mathcad.py            # JSON: ok, dir, exe, version, source, com, skill_dir, tools, others, hint
    python find_mathcad.py --dir      # только папка установки (для подстановки в команды)

Порядок поиска (первый найденный mathcad.exe побеждает):
  1. переменная окружения MATHCAD13_DIR (ручное указание, если Mathcad стоит в нестандартном месте);
  2. COM-сервер Mathcad.Application -> CLSID -> LocalServer32 (именно его запускает mc.ps1);
  3. реестр HKLM\\SOFTWARE\\(WOW6432Node\\)Mathsoft\\Mathcad 13;
  4. записи установщика (Uninstall) с DisplayName «Mathcad 13»;
  5. стандартные папки Program Files (x86) / Program Files.
Другие версии (Mathcad 14/15, Prime) попадают в "others": скилл с ними не работает.
"""
import ctypes
import json
import os
import re
import sys

try:
    import winreg
except ImportError:  # не Windows
    winreg = None

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
ENV = "MATHCAD13_DIR"


def reg_value(root, path, name="", view=0):
    try:
        with winreg.OpenKey(root, path, 0, winreg.KEY_READ | view) as k:
            return winreg.QueryValueEx(k, name)[0]
    except OSError:
        return None


def reg_subkeys(root, path, view=0):
    try:
        with winreg.OpenKey(root, path, 0, winreg.KEY_READ | view) as k:
            i = 0
            while True:
                try:
                    yield winreg.EnumKey(k, i)
                except OSError:
                    return
                i += 1
    except OSError:
        return


def exe_from_command(cmd):
    """'"C:\\...\\mathcad.exe" /automation' -> путь к exe."""
    if not cmd:
        return None
    m = re.match(r'\s*"([^"]+)"', cmd) or re.match(r"\s*(.+?\.exe)", cmd, re.I)  # без кавычек, с пробелами
    return os.path.expandvars(m.group(1)) if m else None


def file_version(path):
    try:
        ver = ctypes.windll.version
        size = ver.GetFileVersionInfoSizeW(path, None)
        if not size:
            return None
        buf = ctypes.create_string_buffer(size)
        ver.GetFileVersionInfoW(path, 0, size, buf)
        p, n = ctypes.c_void_p(), ctypes.c_uint()
        ver.VerQueryValueW(buf, "\\", ctypes.byref(p), ctypes.byref(n))
        ffi = ctypes.cast(p, ctypes.POINTER(ctypes.c_uint32 * 4)).contents
        ms, ls = ffi[2], ffi[3]
        return "%d.%d.%d.%d" % (ms >> 16, ms & 0xFFFF, ls >> 16, ls & 0xFFFF)
    except Exception:
        return None


def candidates():
    """(источник, папка или exe) по порядку приоритета."""
    if os.environ.get(ENV):
        yield "env " + ENV, os.environ[ENV]
    if winreg is None:
        return
    hkcr, hklm = winreg.HKEY_CLASSES_ROOT, winreg.HKEY_LOCAL_MACHINE
    views = (winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY)
    for progid in ("Mathcad.Application", "Mathcad.Application.1"):
        clsid = reg_value(hkcr, progid + r"\CLSID")
        if clsid:
            for key in (r"WOW6432Node\CLSID", "CLSID"):  # сервер 32-битный: сначала его ветка
                srv = reg_value(hkcr, r"%s\%s\LocalServer32" % (key, clsid))
                if srv:
                    yield "COM " + progid, exe_from_command(srv)
                    break
    for view in views:
        for sub in ("Mathcad 13", r"Mathcad 13\Settings"):
            for name in ("InstallDir", "InstallPath", "Path", ""):
                v = reg_value(hklm, r"SOFTWARE\Mathsoft\%s" % sub, name, view)
                if isinstance(v, str) and v:
                    yield r"HKLM\SOFTWARE\Mathsoft\%s" % sub, v
    for _, loc in uninstall_entries(r"^Mathcad 13\b"):
        yield "Uninstall", loc
    for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"),
                 r"C:\Program Files (x86)", r"C:\Program Files"):
        if base:
            yield "default folder", os.path.join(base, "Mathsoft", "Mathcad 13")


def uninstall_entries(pattern):
    if winreg is None:
        return
    root = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    for view in (winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY):
        for sub in reg_subkeys(winreg.HKEY_LOCAL_MACHINE, root, view):
            name = reg_value(winreg.HKEY_LOCAL_MACHINE, root + "\\" + sub, "DisplayName", view)
            if isinstance(name, str) and re.search(pattern, name, re.I):
                loc = reg_value(winreg.HKEY_LOCAL_MACHINE, root + "\\" + sub, "InstallLocation", view) or ""
                yield name, loc


def as_exe(p):
    if not p:
        return None
    p = p.strip().strip('"')
    exe = p if p.lower().endswith(".exe") else os.path.join(p, "mathcad.exe")
    return os.path.normpath(exe) if os.path.isfile(exe) else None


def find():
    res = {"ok": False, "dir": None, "exe": None, "version": None, "source": None,
           "com": {"registered": False, "server": None}, "skill_dir": SKILL_DIR,
           "tools": {n: os.path.join(HERE, n) for n in ("mc.ps1", "xmcd.py", "report.py", "mcsheet.py", "mcplot.py")},
           "others": [], "tried": []}
    done = set()
    for src, path in candidates():
        if (src, path) in done:
            continue
        done.add((src, path))
        exe = as_exe(path)
        res["tried"].append({"source": src, "path": path, "found": bool(exe)})
        if src.startswith("COM") and path:
            res["com"] = {"registered": True, "server": path}
        if exe and not res["exe"]:
            res.update(exe=exe, dir=os.path.dirname(exe), source=src, version=file_version(exe))
    seen = set()
    for name, loc in uninstall_entries(r"mathcad"):
        if not re.match(r"^Mathcad 13\b", name, re.I) and name not in seen:
            seen.add(name)
            res["others"].append({"name": name, "path": loc})
    if res["exe"]:
        ok_ver = (res["version"] or "13").startswith("13")
        res["ok"] = ok_ver and res["com"]["registered"]
        if not ok_ver:
            res["hint"] = "Найден mathcad.exe версии %s, а скилл рассчитан на Mathcad 13." % res["version"]
        elif not res["com"]["registered"]:
            res["hint"] = ("mathcad.exe найден, но COM Mathcad.Application не зарегистрирован: mc.ps1 работать не "
                           "будет. Запустить от администратора: \"%s\" /regserver" % res["exe"])
    else:
        res["hint"] = ("Mathcad 13 не найден. Если он установлен в нестандартную папку, задать переменную "
                       "окружения %s=<папка с mathcad.exe>. Без Mathcad доступно только чтение/генерация .xmcd "
                       "(xmcd.py read/build), без пересчёта." % ENV)
    return res


def main():
    r = find()
    if "--dir" in sys.argv[1:]:
        print(r["dir"] or "")
        sys.exit(0 if r["dir"] else 1)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(r, ensure_ascii=False, indent=1))
    sys.exit(0 if r["ok"] else 1)


if __name__ == "__main__":
    main()
