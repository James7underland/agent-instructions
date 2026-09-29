#!/usr/bin/env python3
"""vsym.py — разбор кейсов Symmetry (.vsym/.vmp = ZIP) без запуска движка.

  python vsym.py list CASE                  # состав архива
  python vsym.py tst CASE [--clean]         # текст кейса (команды .tst); --clean: без displayproperties/Historian/комментариев
  python vsym.py meta CASE                  # сводка _metadata.json: набор единиц, пакет свойств, компоненты, дерево unit ops
  python vsym.py specs CASE                 # заданные в .tst значения (строки "путь = значение [ед.]", последнее присваивание)
  python vsym.py extract CASE OUTDIR        # распаковать (например, взять .vsd с PFD для Visio)
  python vsym.py visio CASE OUT.png [--parts N]  # PFD из GUI (.vsd) целиком в PNG через Visio (невидимо);
                                            # --parts N — дополнительно порезать широкую схему на N кусков
Архив: __s42z__.s42 (двоичное состояние решателя), <имя>.tst (журнал команд = воспроизводимый текст кейса),
<имя>.GUI (настройки интерфейса, ini), <имя>.vsd (PFD, Visio; только если сохранял GUI), _metadata.json,
DynamicsCase.s2m (если была динамика). Кейс, сохранённый движком (sym.py --save), не содержит .vsd/.GUI —
GUI при открытии сам расставит значки (без соединительных линий).
"""
from __future__ import annotations

import json
import re
import sys
import zipfile

NOISE = re.compile(r"^\s*(displayproperties|commonproperties|optimizecode|maxversions|#|/\.\.Historian|"
                   r"delete /Info|\s*/Info\.|/\S+\.Info\.)")


def z(case):
    return zipfile.ZipFile(case)


def _old_ops(uo, parent="/"):
    """Старый формат (Symmetry ≤2020): UnitOperations{тип:{имя:{MatPortsIn:{порт:{conn}}...}}} → новый список."""
    res = []
    for tp, objs in (uo or {}).items():
        for name, o in (objs or {}).items():
            path = ("/" if parent == "/" else parent + ".") + name
            u = {"tp": tp, "n": name, "p": path, "os": str(o.get("os", "")).replace("G?", "")}
            for old, new in (("MatPortsIn", "matPortsIn"), ("MatPortsOut", "matPortsOut"),
                             ("EnePortsIn", "enePortsIn"), ("EnePortsOut", "enePortsOut")):
                ports = o.get(old) or o.get(new) or {}
                if isinstance(ports, list):  # уже новый вид
                    u[new] = ports
                    continue
                u[new] = [{"n": pn, "p": f"{path}.{pn}", "conn": (pv or {}).get("conn")} for pn, pv in ports.items()]
            sub = o.get("UnitOperations") or o.get("unitOps")
            if isinstance(sub, dict) and sub:
                u["unitOps"] = _old_ops(sub, path)
            res.append(u)
    return res


def load_meta(case):
    """_metadata.json в новом формате: {"root": {"unitOps": [...]}, "thermo": [...], "unitSet": ...}."""
    zf = z(case)
    n = member(zf, "_metadata.json")
    if not n:
        raise SystemExit("нет _metadata.json в кейсе")
    m = json.loads(zf.read(n).decode("utf-8", "replace"))
    if "root" not in m and "RootFlowsheet" in m:
        rf = m["RootFlowsheet"]
        th = [{"n": k, "thermoModel": v.get("PropertyPackage"), "cmps": v.get("Compounds"), "attachedTo": v.get("AttachedTo")}
              for k, v in ((m.get("Thermodynamics") or {}).get("ThermoCases") or {}).items()]
        # 2018–2020: RootFlowsheet.UnitOperations{тип:{имя:{MatPortsIn:{…}}}};
        # 2023 из старых версий (MetaVersion 2): RootFlowsheet.unitOps{тип:{имя:{matPortsIn:{…}}}}
        uo = rf.get("UnitOperations") or rf.get("unitOps")
        m = {"root": {"tp": rf.get("tp"), "p": "/", "unitOps": _old_ops(uo if isinstance(uo, dict) else {})},
             "thermo": th, "savedOnUTC": m.get("SavedOn_GMT"), "engines": m.get("Engines"), "format": "old"}
    return m


def member(zf, ext):
    for n in zf.namelist():
        if n.lower().endswith(ext):
            return n
    return None


def cmd_tst(case, clean=False):
    zf = z(case)
    n = member(zf, ".tst")
    if not n:
        sys.exit("нет .tst в архиве")
    txt = zf.read(n).decode("utf-8", "replace")
    for line in txt.splitlines():
        if not line.strip():
            continue
        if clean and NOISE.search(line):
            continue
        print(line)


def walk_ops(node, depth=0, out=None):
    out = out if out is not None else []
    for u in node.get("unitOps", []) or []:
        conns = []
        for key in ("matPortsIn", "matPortsOut"):
            for p in u.get(key, []) or []:
                if p.get("conn"):
                    conns.append(f"{p.get('n')}->{p['conn']}")
        out.append(("  " * depth) + f"{u.get('n')}: {u.get('tp')} [{u.get('os', '')}] " + (" ".join(conns)))
        if u.get("unitOps"):
            walk_ops(u, depth + 1, out)
    return out


def cmd_meta(case):
    m = load_meta(case)
    print("saved:", m.get("savedOnUTC"), "| unitSet:", m.get("unitSet"), "| engines:", m.get("engines"))
    th = m.get("thermo") or m.get("propPkgs") or {}
    if th:
        print("thermo:", json.dumps(th, ensure_ascii=False)[:1500])
    root = m.get("root") or {}
    for line in walk_ops(root):
        print(line)
    other = {k: v for k, v in m.items() if k not in ("root", "thermo", "propPkgs")}
    if m.get("format") == "old":
        print("(старый формат metadata — сведения неполные; актуальный: пересохранить sym.py run --recall X --save Y)")
    print("keys:", list(other.keys()))


def cmd_specs(case):
    zf = z(case)
    txt = zf.read(member(zf, ".tst")).decode("utf-8", "replace")
    last = {}
    units = "?"
    for line in txt.splitlines():
        s = line.strip()
        if s.startswith("units "):
            units = s.split()[1]
        m = re.match(r"""^['"]?(/[^'"=~]+?)['"]?\s*(~?=)\s*(.*?)\s*(#.*)?$""", s)
        if m and not re.search(r"\w+\.\w+\(", m.group(3) or ""):
            path, op, val = m.group(1).strip(), m.group(2), m.group(3)
            if path.startswith("/..") or ".Info." in path:
                continue
            last[path] = (op, val, units)
    for p, (op, v, u) in last.items():
        if v == "":
            continue
        print(f"{p} {op} {v}" + ("" if re.search(r"[A-Za-z%]", v) else f"   [units {u}]"))


def cmd_visio(case, out, parts=0):
    """Экспорт страниц PFD (.vsd внутри .vsym) через Visio.InvisibleApp → PNG. Нужен установленный Visio."""
    import os
    import tempfile
    import win32com.client
    zf = z(case)
    n = member(zf, ".vsd")
    if not n:
        sys.exit("в кейсе нет .vsd (кейс сохранён движком, а не GUI) — используйте pfd.py")
    tmp = os.path.join(tempfile.mkdtemp(prefix="symvsd_"), "pfd.vsd")
    open(tmp, "wb").write(zf.read(n))
    v = win32com.client.DispatchEx("Visio.InvisibleApp")
    outs = []
    try:
        d = v.Documents.OpenEx(tmp, 0x2 | 0x80)
        base, ext = os.path.splitext(os.path.abspath(out))
        k = 0
        for p in d.Pages:
            if p.Background:          # фон «VMGBackground» (логотип) пропускаем
                continue
            fn = base + ("" if k == 0 else f"_{k}") + (ext or ".png")
            p.Export(fn); outs.append((p.Name, fn)); k += 1
        d.Close()
    finally:
        v.Quit()
    for name, fn in outs:
        print(f"{name} -> {fn}")
        if parts and parts > 1:
            from PIL import Image
            im = Image.open(fn).convert("RGB")
            W, H = im.size
            w = W // parts
            for i in range(parts):
                pf = fn.replace(".png", f"_part{i + 1}.png")
                im.crop((max(0, i * w - 80), 0, min(W, (i + 1) * w + 80), H)).save(pf)
                print("   ", pf)


def main():
    if len(sys.argv) < 3:
        print(__doc__); return
    c, case = sys.argv[1], sys.argv[2]
    if c == "list":
        for i in z(case).infolist():
            print(f"{i.file_size:10d}  {i.filename}")
    elif c == "tst":
        cmd_tst(case, "--clean" in sys.argv)
    elif c == "meta":
        cmd_meta(case)
    elif c == "specs":
        cmd_specs(case)
    elif c == "visio":
        parts = int(sys.argv[sys.argv.index("--parts") + 1]) if "--parts" in sys.argv else 0
        cmd_visio(case, sys.argv[3], parts)
    elif c == "extract":
        z(case).extractall(sys.argv[3])
        print("->", sys.argv[3])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
