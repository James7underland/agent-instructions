#!/usr/bin/env python3
"""check.py — проверка решения кейса Symmetry: балансы массы и энергии по каждому аппарату и по схеме, статусы.

  python check.py CASE.vsym [--tol 1e-4] [--json]
Для каждого аппарата корневой схемы: Σ G вход − Σ G выход (кг/ч) и Σ (H·F + Q) вход − выход (кВт) по портам
(значения портов берутся у движка после пересчёта). Реакторы: массовый баланс обязан сходиться, энергетический —
в Symmetry тоже (энтальпии с теплотами образования), но проверяйте по смыслу. Выводит несошедшиеся/нерешённые объекты.
Код выхода 0 — всё в допуске, 2 — есть нарушения.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sym  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("case"); ap.add_argument("--tol", type=float, default=5e-4); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    import vsym
    meta = vsym.load_meta(a.case)
    eng = sym.Engine(echo=lambda *x: None)
    sym.open_case(eng, a.case)
    eng.eval("units SI"); eng.msgs.clear()

    def val(p, u):
        try:
            return eng.value(p, u)[0]
        except Exception:
            return None

    res, bad = [], 0
    bnd_in = bnd_out = 0.0
    for u in meta["root"].get("unitOps", []):
        tp, path = u.get("tp", ""), u.get("p")
        status = u.get("os", "")
        if tp == "Stream.Stream_Material":
            ins = [p for p in u.get("matPortsIn") or [] if p.get("conn")]
            outs = [p for p in u.get("matPortsOut") or [] if p.get("conn")]
            g = val(f"{path}.Out.MassFlow", "kg/h") or 0.0
            if not ins:
                bnd_in += g
            if not outs:
                bnd_out += g
            if status and "Solved" not in status and not ("Converged" in status and "Not" not in status):
                res.append({"obj": path, "status": status}); bad += 1
            continue
        if tp.startswith("Stream."):
            continue
        gin = gout = ein = eout = 0.0
        miss = []
        for key, sign in (("matPortsIn", 1), ("matPortsOut", -1)):
            for p in u.get(key) or []:
                g = val(p["p"] + ".MassFlow", "kg/h")
                e = val(p["p"] + ".Energy", "kW")
                if g is None:
                    miss.append(p["p"]); continue
                if sign > 0:
                    gin += g; ein += e or 0.0
                else:
                    gout += g; eout += e or 0.0
        # энергопорты: подключённые — из metadata (направление известно), остальные — из вывода движка "/X"
        ene = {}
        for key, sign in (("enePortsIn", 1), ("enePortsOut", -1)):
            for p in u.get(key) or []:
                ene[p["p"].rsplit(".", 1)[1]] = sign
        txt = eng.eval(path) or ""
        eng.msgs.clear()
        live = [l.split(":", 1)[1].strip() for l in str(txt).splitlines() if l.startswith("Status:")]
        if live:
            status = " / ".join(live)
        for line in str(txt).splitlines():
            if line.startswith("Port:") and "= EnePort" in line:
                nm = line.split(":", 1)[1].split("=")[0].strip()
                if nm not in ene:
                    ene[nm] = -1 if ("Out" in nm or "condenser" in nm.lower() or "cooler" in nm.lower()) else 1
        for nm, sign in ene.items():
            q = val(f"{path}.{nm}.Energy", "kW")
            if q is None:
                continue
            if sign > 0:
                ein += q
            else:
                eout += q
        dg = gin - gout
        de = ein - eout
        rg = abs(dg) / max(gin, 1e-9)
        re_ = abs(de) / max(abs(ein), abs(eout), 1e-9)
        reactor = any(k in tp for k in ("Rxn", "Reactor", "CSTR", "PFR", "Claus", "Cracker", "Gasification", "FCC", "CCR"))
        solved = (("Solved" in status and "Not Solved" not in status)
                  or ("Converged" in status and "Not Converged" not in status))
        e_ok = reactor or re_ < max(a.tol, 1e-3)
        ok = solved and rg < a.tol and e_ok and not miss
        item = {"reactor": reactor, "obj": path, "type": tp, "status": status, "G_in": gin, "G_out": gout, "dG_rel": rg,
                "E_in_kW": ein, "E_out_kW": eout, "dE_rel": re_, "missing": miss, "ok": bool(ok)}
        if not ok:
            bad += 1
        res.append(item)
    overall = {"feed_kg_h": bnd_in, "products_kg_h": bnd_out, "rel": abs(bnd_in - bnd_out) / max(bnd_in, 1e-9)}
    if overall["rel"] > a.tol:
        bad += 1
    if a.json:
        print(json.dumps({"units": res, "overall": overall, "bad": bad}, ensure_ascii=False, indent=1))
    else:
        for r in res:
            if "G_in" in r:
                print(f"{'OK ' if r['ok'] else '!! '}{r['obj']:14s} {r['type']:34s} [{r['status']}] "
                      f"G {r['G_in']:.6g}→{r['G_out']:.6g} кг/ч (отн. {r['dG_rel']:.1e}); "
                      f"E {r['E_in_kW']:.6g}→{r['E_out_kW']:.6g} кВт (отн. {r['dE_rel']:.1e})"
                      + (" [реактор: энергобаланс по потокам не проверяется]" if r["reactor"] else "")
                      + (f" нет значений: {r['missing']}" if r['missing'] else ""))
            else:
                print(f"!! {r['obj']} статус {r['status']}")
        print(f"Схема: питание {bnd_in:.6g} кг/ч, продукты {bnd_out:.6g} кг/ч, отн. {overall['rel']:.1e}")
        print("ИТОГ:", "всё в допуске" if bad == 0 else f"нарушений {bad}")
    sym.hard_exit(0 if bad == 0 else 2)


if __name__ == "__main__":
    main()
