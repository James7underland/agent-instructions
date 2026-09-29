#!/usr/bin/env python3
"""dyn.py — динамический расчёт Symmetry через COM: прогон интегратора по сетке времени, события, тренды, график.

  python dyn.py [--recall CASE.vsym] [--script build.tst ...] [--to-dynamics]
                --tend 600 --dt 1 --rec /CN1.In@m3/h --rec /CN1.OP --rec /CN1.Target@m3/h
                [--event "60:/CN1.Target = 3 m3/hr"]... [--pre CMD]... [--csv OUT.csv] [--png OUT.png]
                [--title "..."] [--save OUT.vsym] [--reset-time]

  --script        команды (.tst) выполнить после recall (стационар; можно построить схему с нуля)
  --to-dynamics   перевести кейс в динамику: "/ActiveEngine = 2" + "init / / SteadyState" (инициализация из стационара)
  --reinit        уже динамический кейс: переинициализировать из стационара (если сохранённое состояние «разваливается»)
                  Для длинных труб/жёстких моделей: --pre "/Integrator.IntegMeth = BDF2" (неявный метод)
  --pre CMD       команды перед стартом (напр. "/Integrator.StepSize = 0.1 s")
  --event T:CMD   в момент T (с) выполнить команду (скачок задания, смена Cv, режима регулятора...)
  --rec PATH[@unit][=Метка]   что записывать (сигнал, переменная порта); @unit — единицы, =Метка — подпись на графике
  --png           график: все --rec по группам единиц (одна ось на единицу), время в секундах (или --tmin для минут)
Интегратор: RealTime=0 → "IntegRun = 1" блокирует до StopTime (абсолютное время). Шаг интегрирования — StepSize.
"""
from __future__ import annotations

import argparse
import csv
import time
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sym  # noqa: E402


def parse_rec(s: str):
    label = None
    if "=" in s:
        s, label = s.split("=", 1)
    s = sym.unmangle(s)
    p, u = sym.parse_path_unit(s)
    return p, u, (label or (p + (f" [{u}]" if u else "")))


def dyn_cmds(eng, cmds):
    """Команды в динамике — без Solve() (стационарный решатель в динамическом кейсе сбивает интегратор)."""
    for c in cmds:
        eng.eval(c)
        for t, m in eng.msgs:
            if t != "Info":
                print(f"   !! [{t}] {m}")
        eng.msgs.clear()


def main():
    argv = [sym.unmangle(x) for x in sys.argv[1:]]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--recall")
    ap.add_argument("--script", action="append", default=[])
    ap.add_argument("--to-dynamics", action="store_true")
    ap.add_argument("--reinit", action="store_true",
                    help="динамический кейс: заново инициализировать из стационара (init / / SteadyState)")
    ap.add_argument("--pre", action="append", default=[])
    ap.add_argument("--event", action="append", default=[])
    ap.add_argument("--rec", action="append", default=[])
    ap.add_argument("--tend", type=float, required=True)
    ap.add_argument("--dt", type=float, default=1.0)
    ap.add_argument("--reset-time", action="store_true", help="IntegratorTime = 0 перед стартом")
    ap.add_argument("--settle", type=float, default=0.0,
                    help="сначала прогнать S секунд без записи (успокоить регуляторы), время отсчитывать от конца")
    ap.add_argument("--csv")
    ap.add_argument("--png")
    ap.add_argument("--title", default="")
    ap.add_argument("--tmin", action="store_true", help="ось времени в минутах")
    ap.add_argument("--save")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)

    eng = sym.Engine(verbose=a.verbose)
    if not eng.e.HasDynamicsSupport:
        eng.e.AddDynamicsSupport2()
    eng.flush()
    if a.recall:
        sym.open_case(eng, a.recall)
    if a.script:
        sym.run_commands(eng, list(sym.iter_script_lines(a.script, [])), quiet=not a.verbose)
    if a.to_dynamics:
        dyn_cmds(eng, ["/ActiveEngine = 2", "init / / SteadyState"])
    elif a.reinit:
        dyn_cmds(eng, ["init / / SteadyState"])
    base = ["/Integrator.RealTime = 0"] + (["/Integrator.IntegratorTime = 0 s"] if a.reset_time else [])
    dyn_cmds(eng, base + a.pre)

    recs = [parse_rec(r) for r in a.rec]
    events = []
    for ev in a.event:
        t, cmd = ev.split(":", 1)
        events.append((float(t), sym.unmangle(cmd.strip())))
    events.sort()

    def t_now():
        v, _ = eng.value("/Integrator.IntegratorTime", "s")
        return float(v or 0.0)

    def run_to(target):
        """Интегрировать до абсолютного времени target. IntegRun=1 обычно блокирует до StopTime, но может вернуться
        раньше — тогда повторяем. Если время не сдвинулось — интегратор встал (сбой расчёта): печатаем причину."""
        for _ in range(4):
            before = t_now()
            eng.msgs.clear()
            eng.eval(f"/Integrator.StopTime = {target} s")
            eng.eval("/Integrator.IntegRun = 1")
            t1 = time.time()
            while eng.e.IsIntegratorRunning and time.time() - t1 < 3600:
                time.sleep(0.5)
            now = t_now()
            if now >= target - 1e-6:
                return True
            if now <= before + 1e-9:
                why = sorted({m for t, m in eng.msgs if "DYNMsg" in m and "ntegrator" not in m} |
                             {m for t, m in eng.msgs if t != "Info"})
                print(f"   !! интегратор остановился на {now:g} с (цель {target:g} с). Сообщения: {why[:5]}")
                return None
        print(f"   !! интегратор не дошёл до {target:g} с (сейчас {t_now():g} с)")
        return False

    def sample():
        row = [t_now()]
        for p, u, _ in recs:
            try:
                row.append(eng.value(p, u)[0])
            except Exception:
                row.append(None)
        return row

    if a.settle > 0:
        run_to(t_now() + a.settle)
        eng.msgs.clear()
        print(f"# успокоение {a.settle:g} с")
    t0 = t_now()
    rows = [sample()]
    rows[0][0] = 0.0
    n = max(1, int(round(a.tend / a.dt)))
    ei = 0
    for k in range(1, n + 1):
        target = t0 + k * a.dt
        # события заданы относительно старта прогона: применяем перед шагом, начинающимся в момент >= T
        while ei < len(events) and events[ei][0] <= (k - 1) * a.dt + 1e-9:
            print(f"# t={events[ei][0]:g} s: {events[ei][1]}")
            dyn_cmds(eng, [events[ei][1]])
            ei += 1
        ok = run_to(target)
        errs = [s for t, s in eng.msgs if t not in ("Info",)]
        eng.msgs.clear()
        for s in errs:
            print("   !!", s)
        r = sample(); r[0] -= t0
        rows.append(r)
        if ok is None:
            print("# прогон прерван: модель не считается дальше (см. сообщения выше; попробуйте --pre "
                  "\"/Integrator.StepSize = 0.25 s\" или устраните причину в модели)")
            break
    print(f"# прогон {t0:.1f} → {t_now():.1f} с, точек {len(rows)}")

    heads = ["t, s"] + [lab for _, _, lab in recs]
    if a.csv:
        with open(a.csv, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(heads)
            for r in rows:
                w.writerow([("" if x is None else f"{x:.6g}".replace(".", ",")) for x in r])
        print(f"# csv -> {a.csv}")
    else:
        step = max(1, len(rows) // 20)
        print("  ".join(heads))
        for r in rows[::step]:
            print("  ".join("-" if x is None else f"{x:.5g}" for x in r))
    if a.png:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        groups = {}
        for i, (p, u, lab) in enumerate(recs):
            groups.setdefault(u or eng.value(p)[1] or "", []).append((i + 1, lab))
        fig, axes = plt.subplots(len(groups), 1, figsize=(9, 2.8 * len(groups) + 0.6), sharex=True, squeeze=False)
        tt = [r[0] / (60 if a.tmin else 1) for r in rows]
        for ax, (u, items) in zip(axes[:, 0], groups.items()):
            for i, lab in items:
                ax.plot(tt, [r[i] for r in rows], label=lab, lw=1.6)
            ax.set_ylabel(u)
            ax.grid(True, alpha=0.35)
            ax.legend(loc="best", fontsize=8)
        axes[-1, 0].set_xlabel("t, мин" if a.tmin else "t, с")
        if a.title:
            fig.suptitle(a.title)
        fig.tight_layout()
        fig.savefig(a.png, dpi=150)
        print(f"# png -> {a.png}")
    if a.save:
        print(f"# save -> {eng.save(a.save)}")
    sym.hard_exit(0)


if __name__ == "__main__":
    main()
