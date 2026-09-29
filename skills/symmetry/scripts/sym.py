#!/usr/bin/env python3
"""sym.py — драйвер расчётного движка Symmetry 2023.2 (SLB/VMG) через COM без GUI.

Движок: COM-класс VMGMasterInterfaceNet.VMGMainEngine (in-process .NET, только 64-бит Python + pywin32).
Лицензия: SLBSLS_LICENSE_FILE=27000@localhost (локальный Schlumberger Flexnet Server) — ставится автоматически.

Команды (из Bash: PYTHONIOENCODING=utf-8 python sym.py ...):
  run  [a.tst ...] [-e CMD]... [--recall CASE] [--save OUT.vsym] [--units SI] [--batch] [-v]
       [--streams [FILE|-]] [--get PATH[@unit]]... [--json]
       Выполнить команды языка Symmetry (.tst построчно, затем -e по порядку). После каждой команды — Solve()
       (как GUI с включённым решателем), если нет hold. --batch: решать только на go/solve, перед запросами и в конце.
       Строки-запросы (напр. "/S1.Out", "dir /V1") печатают ответ движка. Ошибки/предупреждения печатаются всегда.
       Псевдокоманды sym.py: solve (принудительный пересчёт), echo ТЕКСТ, save FILE.vsym.
  streams CASE [--units SI] [--props T,P,...] [--comp mole|mass|none] [--out FILE.csv|.xlsx|.json] [--all]
       Таблица материальных потоков (включая подсхемы). По умолчанию только объекты Stream_Material.
  get  CASE PATH[@unit] ...     Числа из кейса (JSON): скаляры и векторы, в единицах активного набора или @unit.
  tree CASE [--path /] [--depth 3]   Дерево объектов с типами.
  info CASE PATH                Текстовый вид объекта (как в консоли) + "dir PATH".
  new  --out OUT.vsym a.tst ... То же, что run ... --save (удобный синоним).
CASE = путь к .vsym/.vmp или "-" (пустой кейс).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

for _s in (sys.stdout, sys.stderr):      # вывод в конвейер (cp1251) не падает на →, °, ₂
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

os.environ.setdefault("SLBSLS_LICENSE_FILE", "27000@localhost")

NOISE = re.compile(r"(Forget|Forgot|Forgetting|UpdateUndoRedo|Solving operation|Before Main Solve|After Main Solve|"
                   r"Solved Partially|Solved simulation|Flowsheet / solved|DoneSolving|CMDBeforeCleanUp|Extracting file|"
                   r"Finished recalling)")
PSEUDO = {"solve", "echo", "save"}
MUTATING_KW = {"units", "hold", "go", "delete", "cd", "copy", "paste", "cut", "undo", "redo", "import", "init",
               "optimizecode", "maxversions", "displayproperties", "commonproperties", "_call", "clear", "read",
               "recall", "store", "language", "profiler", "dstoresnpsht", "dloadsnpsht"}
DEFAULT_PROPS = ["VapFrac", "T", "P", "MoleFlow", "MassFlow", "StdLiqVolumeFlow", "StdGasVolumeFlow", "MolecularWeight",
                 "MassDensity", "H", "Energy"]


def _first(x):
    return x[0] if isinstance(x, tuple) else x


# короткие имена единиц → имена движка (все допустимые: GetVMGVariable(p)[0].GetValidUnitNames())
UNIT_ALIASES = {"t/h": "ton(metric)/h", "т/ч": "ton(metric)/h", "t/d": "ton(metric)/d", "°C": "C", "degC": "C",
                "м3/ч": "m3/h", "кг/ч": "kg/h", "кПа": "kPa", "МПа": "MPa"}

UNKNOWN = -12321.0  # так движок отдаёт «нет значения» (None) через COM


def _none(x):
    return None if isinstance(x, (int, float)) and abs(x - UNKNOWN) < 1e-6 else x


class Engine:
    def __init__(self, verbose: bool = False, echo=print):
        import win32com.client
        import win32com.server.util
        self.verbose = verbose
        self.echo = echo
        self.e = win32com.client.Dispatch("VMGMasterInterfaceNet.VMGMainEngine")
        self.msgs: list[tuple[str, str]] = []
        eng = self

        class CB:
            _public_methods_ = ["PyInfoMessage"]

            def PyInfoMessage(self, msg, args, mtype):
                try:
                    txt = _first(eng.e.RenderMessage(msg, args))
                except Exception:
                    txt = f"{msg} {args}"
                eng.msgs.append((str(mtype), str(txt)))
                return None

        self.e.SetCallBackCOMObject(win32com.server.util.wrap(CB()), "CB")

    # --- сообщения ---
    def flush(self, show_info: bool | None = None) -> list[tuple[str, str]]:
        show_info = self.verbose if show_info is None else show_info
        out = self.msgs[:]
        self.msgs.clear()
        for t, s in out:
            if t == "Info":
                if show_info and not NOISE.search(s):
                    self.echo(f"   [i] {s}")
            else:
                self.echo(f"   !! [{t}] {s}")
        return out

    # --- основные операции ---
    def eval(self, cmd: str):
        return _first(self.e.Eval(cmd))

    def solve(self):
        self.e.Solve()

    @property
    def on_hold(self) -> bool:
        return bool(self.e.IsOnHold)

    def recall(self, path: str):
        r = self.e.RecallFile(os.path.abspath(path))
        return _first(r)

    def save(self, path: str):
        path = os.path.abspath(path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return _first(self.e.SaveFile(path))

    def var(self, path: str):
        return _first(self.e.GetVMGVariable(path))

    def value(self, path: str, unit: str | None = None):
        """Число/вектор. Без unit — в активном наборе единиц. Возвращает (value, unit)."""
        unit = UNIT_ALIASES.get(unit, unit) if unit else unit
        v = self.var(path)
        if v is None:
            raise KeyError(path)
        size = v.Size
        is_vec = bool(v.DataType & 16) if v.DataType is not None else size > 1
        if is_vec:
            if unit:
                vals = _first(v.GetValuesAtUnits(unit))
            else:
                vals = v.GetValues()
            vals = [_none(x) for x in vals] if vals is not None else None
            return vals, (unit or v.GetUnitName() or "")
        if unit:
            r = v.GetValueAtUnits(unit, 0)
            return _none(r[0] if isinstance(r, tuple) else r), unit
        return _none(v.GetValue(0)), (v.GetUnitName() or "")

    def compounds(self) -> list[str]:
        try:
            names = self.e.RootFlowsheet.GetCompoundNames()
            return list(names) if names else []
        except Exception:
            return []

    def children(self, path: str = "/") -> list[tuple[str, str]]:
        """(имя, тип) дочерних объектов по выводу 'dir PATH'."""
        txt = self.eval(f"dir {path}") or ""
        self.msgs.clear()
        res = []
        for line in str(txt).splitlines():
            m = re.match(r"^\s*([^:\s]+):\s*(.*)$", line)
            if not m:
                continue
            name, rest = m.group(1), m.group(2)
            m2 = re.search(r"=\s*([A-Za-z_][\w.]*)\s*(;|$)", rest)
            tp = m2.group(1) if m2 else rest.strip()
            res.append((name, tp))
        return res


def hard_exit(code: int = 0):
    """Выход без разрушения COM-объектов: после динамики движок падает (segfault 139) при штатной выгрузке."""
    sys.stdout.flush(); sys.stderr.flush()
    os._exit(code)


def is_query(cmd: str) -> bool:
    c = cmd.strip()
    if not c:
        return False
    first = c.split()[0].lower()
    if first in ("dir", "tree", "about", "help", "unitsets") or (first == "units" and len(c.split()) == 1):
        return True
    if first in MUTATING_KW or first in PSEUDO:
        return False
    if re.search(r"(~?=|->|\s\+\s|\s-\s|\s\+$|\s-$)", c):
        return False
    return True


def iter_script_lines(files: list[str], exprs: list[str]):
    for f in files:
        with open(f, encoding="utf-8-sig", errors="replace") as fh:
            for line in fh:
                yield line.rstrip("\r\n")
    for e in exprs:
        yield e


def run_commands(eng: Engine, lines, batch: bool = False, quiet: bool = False):
    dirty = False
    errors = 0
    dyn = False          # после "/ActiveEngine = 2" Solve() не вызываем (стационарный решатель сбивает динамику)
    for raw in lines:
        cmd = raw.strip()
        if not cmd or cmd.startswith("#"):
            continue
        low = cmd.split()[0].lower()
        if re.match(r"^/?ActiveEngine\s*=\s*2", cmd):
            dyn = True
            try:                                  # без поддержки динамики "/ActiveEngine = 2" молча не работает
                if not getattr(eng, "_dyn_support", False):
                    eng.e.AddDynamicsSupport2()
                    eng._dyn_support = True
            except Exception as ex:
                eng.echo(f"   !! AddDynamicsSupport2: {ex}")
        if low == "solve":
            eng.solve(); dirty = False
            errors += sum(1 for t, _ in eng.flush() if t != "Info")
            continue
        if low == "echo":
            eng.echo(cmd[5:]); continue
        if low == "save":
            fn = cmd[5:].strip().strip('"')
            eng.echo(f"# save {fn} -> {eng.save(fn)}"); eng.flush(); continue
        query = is_query(cmd)
        if query and dirty and not eng.on_hold and not dyn:
            eng.solve(); dirty = False
            eng.flush()
        if not quiet:
            eng.echo(f"> {cmd}")
        try:
            out = eng.eval(cmd)
        except Exception as ex:  # COM-исключение
            out = None
            eng.echo(f"   !! [COM] {ex}")
            errors += 1
        if not query:
            dirty = True
            if (not batch or low == "go") and not eng.on_hold and not dyn:
                eng.solve(); dirty = False
        if out not in (None, ""):
            eng.echo(str(out).rstrip())
        errors += sum(1 for t, _ in eng.flush() if t != "Info")
    if dirty and not eng.on_hold and not dyn:
        eng.solve()
        errors += sum(1 for t, _ in eng.flush() if t != "Info")
    return errors


# ---------- таблица потоков ----------
def find_streams(eng: Engine, path: str = "/", include_all: bool = False, depth: int = 0) -> list[str]:
    res = []
    for name, tp in eng.children(path):
        full = "/" + name if path == "/" else f"{path}.{name}"
        if tp.endswith("Stream_Material"):
            res.append(full)
        elif "Flowsheet" in tp and depth < 6:
            res.extend(find_streams(eng, full, include_all, depth + 1))
    return res


def stream_table(eng: Engine, props: list[str], comp: str = "mole"):
    streams = find_streams(eng)
    cmps = eng.compounds()
    rows, units = [], {}
    for s in streams:
        row = {"Stream": s}
        for p in props:
            try:
                val, u = eng.value(f"{s}.Out.{p}")
            except Exception:
                val, u = None, ""
            row[p] = val
            if u and p not in units:
                units[p] = u
        if comp != "none" and cmps:
            vec = "Fraction" if comp == "mole" else "MassFraction"
            try:
                vals, _ = eng.value(f"{s}.Out.{vec}")
            except Exception:
                vals = None
            for i, c in enumerate(cmps):
                row[f"x_{c}" if comp == "mole" else f"w_{c}"] = (vals[i] if vals and i < len(vals) else None)
        rows.append(row)
    eng.msgs.clear()
    return rows, units, cmps


def write_table(rows, units, out: str | None):
    if not rows:
        print("(нет потоков)")
        return
    cols = list(rows[0].keys())
    heads = [f"{c}, {units[c]}" if c in units and units[c] else c for c in cols]
    if out and out.lower().endswith(".json"):
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"units": units, "rows": rows}, f, ensure_ascii=False, indent=1)
    elif out and out.lower().endswith(".xlsx"):
        from openpyxl import Workbook
        wb = Workbook(); ws = wb.active; ws.title = "Потоки"
        ws.append(heads)
        for r in rows:
            ws.append([r[c] for c in cols])
        wb.save(out)
    elif out and out != "-":
        import csv
        with open(out, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(heads)
            for r in rows:
                w.writerow([("" if r[c] is None else (f"{r[c]:.6g}".replace(".", ",") if isinstance(r[c], float) else r[c]))
                            for c in cols])
    else:
        def fmt(v):
            return "-" if v is None else (f"{v:.5g}" if isinstance(v, float) else str(v))
        width = [max(len(h), *(len(fmt(r[c])) for r in rows)) for h, c in zip(heads, cols)]
        print("  ".join(h.ljust(w) for h, w in zip(heads, width)))
        for r in rows:
            print("  ".join(fmt(r[c]).ljust(w) for c, w in zip(cols, width)))
    if out and out != "-":
        print(f"# таблица -> {out}")


def parse_path_unit(s: str):
    if "@" in s:
        p, u = s.rsplit("@", 1)
        return p, u
    return s, None


def cmd_get(eng: Engine, items: list[str]):
    res = {}
    for it in items:
        p, u = parse_path_unit(it)
        try:
            val, unit = eng.value(p, u)
            res[p] = {"value": val, "unit": unit}
        except Exception as ex:
            res[p] = {"error": str(ex)}
    eng.msgs.clear()
    return res


def print_tree(eng: Engine, path: str, depth: int, indent: int = 0):
    for name, tp in eng.children(path):
        full = "/" + name if path == "/" else f"{path}.{name}"
        if tp.startswith("sim.solver.Ports") or re.fullmatch(r"[\w\s.+-]*", tp) is None:
            pass
        print("  " * indent + f"{name}: {tp}")
        if depth > 1 and (".unitop." in tp or "Flowsheet" in tp or "Stream" in tp):
            print_tree(eng, full, depth - 1, indent + 1)


def open_case(eng: Engine, case: str | None):
    if case and case != "-":
        if not os.path.exists(case):
            sys.exit(f"нет файла {case}")
        t = time.time()
        r = eng.recall(case)
        eng.flush()
        print(f"# recall {case} -> {r} ({time.time() - t:.1f} c)")


_MSYS = re.compile(r"^[A-Za-z]:[/\\]Program Files[/\\]Git(?=[/\\])")


def unmangle(arg: str) -> str:
    """Git Bash превращает '/S1.Out.T' в 'C:/Program Files/Git/S1.Out.T' — возвращаем как было."""
    if re.fullmatch(r"[A-Za-z]:/", arg):          # "/G" → "G:/" (однобуквенное имя MSYS считает диском)
        return "/" + arg[0].upper()
    return _MSYS.sub("", arg).replace("\\", "/") if _MSYS.match(arg) else arg


def main(argv=None):
    argv = [unmangle(x) for x in (sys.argv[1:] if argv is None else argv)]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run"); n = sub.add_parser("new")
    for p in (r, n):
        p.add_argument("files", nargs="*")
        p.add_argument("-e", dest="exprs", action="append", default=[])
        p.add_argument("--recall")
        p.add_argument("--units")
        p.add_argument("--batch", action="store_true")
        p.add_argument("-v", "--verbose", action="store_true")
        p.add_argument("-q", "--quiet", action="store_true", help="не печатать сами команды")
        p.add_argument("--streams", nargs="?", const="-")
        p.add_argument("--get", action="append", default=[])
    r.add_argument("--save")
    n.add_argument("--out", required=True)

    s = sub.add_parser("streams"); s.add_argument("case"); s.add_argument("--units"); s.add_argument("--props")
    s.add_argument("--comp", default="mole", choices=["mole", "mass", "none"]); s.add_argument("--out")
    g = sub.add_parser("get"); g.add_argument("case"); g.add_argument("paths", nargs="+"); g.add_argument("--units")
    t = sub.add_parser("tree"); t.add_argument("case"); t.add_argument("--path", default="/"); t.add_argument("--depth", type=int, default=2)
    i = sub.add_parser("info"); i.add_argument("case"); i.add_argument("path")
    a = ap.parse_args(argv)

    eng = Engine(verbose=getattr(a, "verbose", False))
    if a.cmd in ("run", "new"):
        open_case(eng, a.recall)
        pre = [f"units {a.units}"] if a.units else []
        errs = run_commands(eng, list(pre) + list(iter_script_lines(a.files, a.exprs)), batch=a.batch, quiet=a.quiet)
        if a.get:
            print(json.dumps(cmd_get(eng, a.get), ensure_ascii=False, indent=1))
        if a.streams:
            rows, units, _ = stream_table(eng, DEFAULT_PROPS)
            write_table(rows, units, a.streams)
        out = a.save if a.cmd == "run" else a.out
        if out:
            print(f"# save -> {eng.save(out)}")
            eng.flush()
        print(f"# ошибок/предупреждений: {errs}")
        return 0 if errs == 0 else 2
    open_case(eng, a.case)
    if getattr(a, "units", None):
        eng.eval(f"units {a.units}"); eng.msgs.clear()
    if a.cmd == "streams":
        props = a.props.split(",") if a.props else DEFAULT_PROPS
        rows, units, _ = stream_table(eng, props, a.comp)
        write_table(rows, units, a.out)
    elif a.cmd == "get":
        print(json.dumps(cmd_get(eng, a.paths), ensure_ascii=False, indent=1))
    elif a.cmd == "tree":
        print_tree(eng, a.path, a.depth)
    elif a.cmd == "info":
        print(eng.eval(a.path)); print(eng.eval(f"dir {a.path}")); eng.flush()
    return 0


if __name__ == "__main__":
    hard_exit(main() or 0)
