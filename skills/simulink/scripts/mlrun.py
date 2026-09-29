# -*- coding: utf-8 -*-
"""Запуск MATLAB/Simulink в пакетном режиме (matlab -batch) из любой оболочки.

    python mlrun.py --info
        JSON: папка MATLAB, версия, есть ли Simulink / Control / Signal / DSP.
    python mlrun.py [--cd DIR] [--path DIR ...] [--timeout СЕК] [--log ФАЙЛ] "команды MATLAB"
        cd в DIR, addpath для DIR из --path и папки scripts/matlab скилла, затем команды.
        Вывод MATLAB (консоль Windows отдаёт его в cp866) перекодируется в UTF-8.
        Код выхода = код выхода MATLAB (1 при ошибке в скрипте).

Зачем: в -batch MATLAB понимает только пути Windows (C:\\...), а Git Bash
подставляет /c/...; вывод с кириллицей приходит в cp866; экранирование
кавычек и обратных слешей в bash-строке легко испортить.
Папку MATLAB можно задать переменной MATLAB_ROOT.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def win(p):
    """/c/Users/... (Git Bash) -> C:\\Users\\..., относительный -> абсолютный."""
    m = re.match(r"^/([a-zA-Z])/(.*)$", p)
    if m:
        p = m.group(1).upper() + ":\\" + m.group(2).replace("/", "\\")
    return os.path.abspath(p)


def find_root():
    env = os.environ.get("MATLAB_ROOT")
    if env and os.path.exists(os.path.join(env, "bin", "matlab.exe")):
        return env
    cands = sorted(glob.glob(r"C:\Program Files\MATLAB\R20*"), reverse=True)
    for c in cands:
        if os.path.exists(os.path.join(c, "bin", "matlab.exe")):
            return c
    try:
        out = subprocess.run(["where", "matlab"], capture_output=True, text=True).stdout
        for line in out.splitlines():
            if line.lower().endswith("matlab.exe"):
                return os.path.dirname(os.path.dirname(line.strip()))
    except OSError:
        pass
    return None


def q(s):
    """Строка MATLAB в одинарных кавычках."""
    return "'" + s.replace("'", "''") + "'"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("code", nargs="?", default="")
    ap.add_argument("--info", action="store_true")
    ap.add_argument("--cd")
    ap.add_argument("--path", action="append", default=[])
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--log")
    a = ap.parse_args()

    root = find_root()
    if a.info:
        tb = os.path.join(root, "toolbox") if root else ""
        info = dict(ok=bool(root), root=root,
                    version=os.path.basename(root) if root else None,
                    simulink=bool(root) and os.path.isdir(os.path.join(tb, "simulink")),
                    control=bool(root) and os.path.isdir(os.path.join(tb, "control")),
                    signal=bool(root) and os.path.isdir(os.path.join(tb, "signal")),
                    dsp=bool(root) and os.path.isdir(os.path.join(tb, "dsp")),
                    helpers=os.path.join(HERE, "matlab"),
                    hint=None if root else "MATLAB не найден: задай MATLAB_ROOT")
        print(json.dumps(info, ensure_ascii=False, indent=1))
        return 0
    if not root:
        print("MATLAB не найден: задай MATLAB_ROOT", file=sys.stderr)
        return 2

    pre = []
    if a.cd:
        pre.append("cd(%s);" % q(win(a.cd)))
    for p in [os.path.join(HERE, "matlab")] + a.path:
        pre.append("addpath(%s);" % q(win(p)))
    code = " ".join(pre) + " " + a.code
    exe = os.path.join(root, "bin", "matlab.exe")
    try:
        r = subprocess.run([exe, "-batch", code], capture_output=True, timeout=a.timeout)
    except subprocess.TimeoutExpired:
        print("MATLAB не уложился в %d с" % a.timeout, file=sys.stderr)
        return 3
    raw = r.stdout + r.stderr
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("cp866", errors="replace")
    if a.log:
        with open(a.log, "w", encoding="utf-8") as fh:
            fh.write(text)
    sys.stdout.reconfigure(encoding="utf-8")
    print(text)
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
