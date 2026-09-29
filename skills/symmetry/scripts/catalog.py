#!/usr/bin/env python3
"""catalog.py — каталог unit operations Symmetry: создаёт каждую операцию из UI64\\Symmetry.ini [UnitOperation]
в пустом кейсе (Advanced Peng-Robinson, C1–nC5 + вода) и сохраняет ответы движка "/X" и "dir /X".

  python catalog.py OUT_DIR [--only Heater,Valve] [--timeout 90]
  python catalog.py OUT_DIR --md CATALOG.md      # сводная таблица по готовому OUT_DIR/index.json
Результат: OUT_DIR/<Имя>.txt (сырой вывод) + OUT_DIR/index.json (имя, конструктор, группа, порты, параметры, ошибки).
Каждая операция — отдельный процесс (падение движка не валит обход).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

INI = r"C:\Program Files\VMG\Symmetry\UI64\Symmetry.ini"
HERE = os.path.dirname(os.path.abspath(__file__))
SETUP = ["units SI", "$RootThermo = VirtualMaterials.Advanced_Peng-Robinson", "/ -> $RootThermo",
         "$RootThermo + METHANE ETHANE PROPANE n-BUTANE n-PENTANE WATER"]


def read_ops():
    ops, group, on = [], "", False
    for raw in open(INI, encoding="utf-8", errors="replace"):
        line = raw.strip()
        if line.startswith("["):
            on = line.lower() == "[unitoperation]"
            continue
        if not on or not line or line.startswith("'"):
            continue
        m = re.match(r"^<\s*/", line)
        if m:
            group = ""; continue
        m = re.match(r"^<([^/>][^>]*)>", line)
        if m:
            group = m.group(1); continue
        if line.startswith("'") or "=" not in line:
            continue
        name, ctor = [x.strip() for x in line.split("=", 1)]
        ctor = ctor.split(" '")[0].strip()
        ops.append({"name": name, "ctor": ctor, "group": group})
    return ops


def child(name, ctor, out_dir):
    sys.path.insert(0, HERE)
    import sym
    lines = []
    eng = sym.Engine(echo=lines.append)
    for c in SETUP:
        eng.eval(c)
    eng.msgs.clear()
    eng.eval(f"/X = {ctor}")
    errs = [s for t, s in eng.msgs if t != "Info"]
    eng.msgs.clear()
    view = eng.eval("/X") or ""
    d = eng.eval("dir /X") or ""
    eng.msgs.clear()
    with open(os.path.join(out_dir, f"{name}.txt"), "w", encoding="utf-8") as f:
        f.write(f"# {name} = {ctor}\n")
        if errs:
            f.write("# ERRORS: " + " | ".join(errs) + "\n")
        f.write("\n## /X\n" + str(view) + "\n\n## dir /X\n" + str(d) + "\n")
    ports = {"mat": [], "ene": [], "sig": []}
    params = {}
    for line in str(d).splitlines():
        m = re.match(r"^\s*([^:]+):\s*(.*)$", line)
        if not m:
            continue
        k, v = m.group(1).strip(), m.group(2).strip()
        if "Port_Material" in v:
            ports["mat"].append(k)
        elif "Port_Energy" in v:
            ports["ene"].append(k)
        elif "Port_Signal" in v:
            ports["sig"].append(k)
        elif v.startswith(k + " ="):
            params[k] = v.split("=", 1)[1].strip()
        else:
            params[k] = v
    print(json.dumps({"ports": ports, "params": params, "errors": errs}, ensure_ascii=False))


def write_md(out_dir, md):
    idx = json.load(open(os.path.join(out_dir, "index.json"), encoding="utf-8"))
    groups = {}
    for o in idx:
        groups.setdefault(o.get("group") or "Основные", []).append(o)
    L = ["# Каталог unit operations Symmetry 2023.2 (снят движком)", "",
         "Источник: `UI64\\Symmetry.ini [UnitOperation]` (конструкторы с настройками GUI по умолчанию). Для каждой операции"
         " создан объект `/X = <конструктор>` и сняты `/X` и `dir /X` — полный вывод: `unitops/<Имя>.txt`.",
         "M — материальные порты, E — энергетические, S — число сигнальных портов (задаваемые/расчётные величины,"
         " напр. DeltaP, OutT), P — число параметров (Param). Имена портов используются в командах `/X.In -> /S1.Out`.", ""]
    for g, ops in groups.items():
        L += [f"## {g}", "", "| Имя | Конструктор | M | E | S | P |", "|---|---|---|---|---|---|"]
        for o in ops:
            pr = o.get("ports", {})
            err = "; ".join(o.get("errors", []))
            ctor = o["ctor"].replace("|", "\\|")
            if len(ctor) > 90:
                ctor = ctor[:87] + "..."
            L.append(f"| {o['name']} | `{ctor}` | {' '.join(pr.get('mat', []))} | {' '.join(pr.get('ene', []))} | "
                     f"{len(pr.get('sig', []))} | {len(o.get('params', {}))}{' ⚠ ' + err if err else ''} |")
        L.append("")
    open(md, "w", encoding="utf-8").write("\n".join(L))
    print("md ->", md)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--only")
    ap.add_argument("--timeout", type=int, default=90)
    ap.add_argument("--child", nargs=2)
    ap.add_argument("--md")
    a = ap.parse_args()
    if a.md:
        write_md(a.out, a.md)
        return
    os.makedirs(a.out, exist_ok=True)
    if a.child:
        child(a.child[0], a.child[1], a.out)
        return
    ops = read_ops()
    if a.only:
        want = set(a.only.split(","))
        ops = [o for o in ops if o["name"] in want]
    seen, index = set(), []
    for o in ops:
        if o["name"] in seen:
            continue
        seen.add(o["name"])
        try:
            r = subprocess.run([sys.executable, __file__, a.out, "--child", o["name"], o["ctor"]],
                               capture_output=True, text=True, encoding="utf-8", timeout=a.timeout,
                               env=dict(os.environ, PYTHONIOENCODING="utf-8"))
            last = [l for l in r.stdout.splitlines() if l.startswith("{")]
            info = json.loads(last[-1]) if last else {"errors": ["no output: " + r.stderr[-400:]]}
        except subprocess.TimeoutExpired:
            info = {"errors": ["timeout"]}
        o.update(info)
        index.append(o)
        print(f"{o['name']:28s} ports={sum(len(v) for v in info.get('ports', {}).values()):3d} "
              f"params={len(info.get('params', {})):3d} err={'; '.join(info.get('errors', []))[:80]}", flush=True)
    with open(os.path.join(a.out, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
