#!/usr/bin/env python3
"""softplc.py — «программный ПЛК» на Python для отладки логики на модели Symmetry (через plcbridge.py).

Цикл сканирования как у ПЛК: чтение входов → программа → запись выходов (только изменившихся), период --scan.
Программа — отдельный .py с функциями init(io) и scan(io, dt); блоки в стиле МЭК 61131 — из этого модуля:
PID, TON, TOF, R_TRIG, F_TRIG, SR, RS, RAMP. Логику, отлаженную здесь, переносить в ST почти построчно.

  python softplc.py --ua opc.tcp://localhost:4840/symmetry/ --program prog.py [--tags map.csv] [--time 600]
  python softplc.py --modbus localhost:5020 --tags map.csv --program prog.py [--word-order ABCD]
  [--log plc.csv] [--scan 0.2] [--sim-time]   (--sim-time: время ПЛК = модельное, для ускоренного моста)

io["LT100.PV"] — значение тега; запись: io["LV100.CMD"] = 42 (уходит в объект только для W-тегов).
Новые ключи (io["ALM.X"] = True) — внутренние переменные программы: не передаются, но пишутся в журнал.
io.t — время ПЛК, с (от старта); io.sim_t — модельное время (если есть Sim.Time).
Карта тегов (--tags) обязательна для Modbus (адреса/типы) и желательна для OPC UA (иначе теги — все узлы
папки Symmetry, направление: запись в W-узлы).
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import os
import struct
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------- блоки МЭК 61131 (упрощённо)
class TON:
    """Задержка включения: Q = 1, если IN держится PT секунд."""
    def __init__(self, pt):
        self.pt, self.et, self.q = pt, 0.0, False

    def __call__(self, inp, dt):
        self.et = min(self.et + dt, self.pt) if inp else 0.0
        self.q = bool(inp) and self.et >= self.pt
        return self.q


class TOF:
    """Задержка выключения: Q остаётся 1 ещё PT секунд после снятия IN."""
    def __init__(self, pt):
        self.pt, self.et, self.q = pt, 0.0, False

    def __call__(self, inp, dt):
        if inp:
            self.et, self.q = 0.0, True
        else:
            self.et = min(self.et + dt, self.pt)
            self.q = self.q and self.et < self.pt
        return self.q


class R_TRIG:
    def __init__(self):
        self.m = False

    def __call__(self, clk):
        q = bool(clk) and not self.m
        self.m = bool(clk)
        return q


class F_TRIG:
    def __init__(self):
        self.m = False

    def __call__(self, clk):
        q = not clk and self.m
        self.m = bool(clk)
        return q


class SR:
    """Триггер с приоритетом установки."""
    def __init__(self):
        self.q = False

    def __call__(self, s, r):
        self.q = bool(s) or (self.q and not r)
        return self.q


class RS:
    """Триггер с приоритетом сброса."""
    def __init__(self):
        self.q = False

    def __call__(self, s, r):
        self.q = (bool(s) or self.q) and not r
        return self.q


class RAMP:
    """Ограничение скорости изменения: rate — ед./с."""
    def __init__(self, rate, y0=0.0):
        self.rate, self.y = rate, y0

    def __call__(self, x, dt):
        d = max(-self.rate * dt, min(self.rate * dt, x - self.y))
        self.y += d
        return self.y


class PID:
    """ПИД (зависимая форма, как у регулятора Symmetry): Kp — безразмерный (% выхода на % шкалы PV), Ti/Td — с.
    direct=True: выход растёт, когда PV > SP. Режимы: auto=False — ручной (out = man), безударный переход."""
    def __init__(self, kp, ti, td=0.0, pv_lo=0.0, pv_hi=100.0, out_lo=0.0, out_hi=100.0, direct=False, out0=50.0):
        self.kp, self.ti, self.td = kp, ti, td
        self.pv_lo, self.pv_hi, self.out_lo, self.out_hi = pv_lo, pv_hi, out_lo, out_hi
        self.direct, self.auto, self.man = direct, True, out0
        self.i, self.e_prev, self.out = out0, None, out0
        self._init = None

    def __call__(self, sp, pv, dt):
        span = (self.pv_hi - self.pv_lo) or 1.0
        e = (pv - sp) / span * 100.0 if self.direct else (sp - pv) / span * 100.0
        if not self.auto:
            self.out = self.i = self.man
            self.e_prev = e
            return self.out
        if self._init is not None:            # безударно: интегратор = выход − P-составляющая
            self.i, self._init = self._init - self.kp * e, None
        d = 0.0
        if self.td and self.e_prev is not None and dt > 0:
            d = self.kp * self.td * (e - self.e_prev) / dt
        if self.ti > 0:
            self.i += self.kp * e * dt / self.ti
            self.i = max(self.out_lo, min(self.out_hi, self.i))      # anti-windup
        out = self.kp * e + self.i + d
        self.out = max(self.out_lo, min(self.out_hi, out))
        self.e_prev = e
        return self.out

    def bumpless(self, out):
        """Безударный пуск/переход в Auto: первый расчёт даст ровно out (интегратор = out − Kp·e)."""
        self.i = self.out = out
        self._init = out


# ---------------------------------------------------------------- ввод/вывод
class IO(dict):
    def __init__(self):
        super().__init__()
        self.t = 0.0
        self.sim_t = None
        self.dirty = {}

    def __setitem__(self, k, v):
        if self.get(k) != v:
            self.dirty[k] = v
        super().__setitem__(k, v)


class UaIO:
    def __init__(self, url, tags):
        from asyncua.sync import Client
        self.c = Client(url, timeout=5)
        self.c.connect()
        ns = self.c.get_namespace_index("urn:symmetry:plcbridge")
        self.ns = ns
        if tags:
            names = [(t["tag"], t["dir"]) for t in tags]
        else:
            root = self.c.nodes.objects.get_child([f"{ns}:Symmetry"])
            names = []
            for n in root.get_children():
                for m in (n.get_children() or [n]):
                    bn = m.read_browse_name().Name
                    if not bn.startswith("Sim"):
                        names.append((bn, "W" if m.read_attribute(3) else "R"))   # грубо; лучше --tags
        self.names = names
        self.nodes = {n: self.c.get_node(f"ns={ns};s={n}") for n, _ in names}
        self.types = {}
        try:
            self.sim_time = self.c.get_node(f"ns={ns};s=Sim.Time")
            self.sim_time.read_value()
        except Exception:
            self.sim_time = None

    def read(self, io):
        vals = self.c.read_values([self.nodes[n] for n, _ in self.names])
        for (n, _), v in zip(self.names, vals):
            dict.__setitem__(io, n, v)
        io.sim_t = self.sim_time.read_value() if self.sim_time else None

    def write(self, io):
        from asyncua import ua
        if not io.dirty:
            return
        nodes, vals = [], []
        for k, v in io.dirty.items():
            if k not in self.nodes:          # внутренняя переменная программы (как M-память ПЛК): только журнал
                continue
            vt = ua.VariantType.Boolean if isinstance(v, bool) else \
                ua.VariantType.Int32 if isinstance(v, int) else ua.VariantType.Double
            nodes.append(self.nodes[k]); vals.append(ua.Variant(v, vt))
        self.c.write_values(nodes, vals)
        io.dirty.clear()

    def close(self):
        self.c.disconnect()


class MbIO:
    def __init__(self, hostport, tags, order):
        from pymodbus.client import ModbusTcpClient
        host, port = (hostport.split(":") + ["502"])[:2]
        self.c = ModbusTcpClient(host, port=int(port))
        if not self.c.connect():
            raise SystemExit(f"нет связи с {hostport}")
        self.tags = [t for t in tags if t.get("mb", "").strip() != ""]
        self.order = order
        self.lo = min(int(t["mb"]) for t in self.tags)
        self.hi = max(int(t["mb"]) + (2 if t["type"] == "float" else 1) for t in self.tags)

    def _dec(self, t, r):
        if t["type"] == "float":
            hi, lo = (r[1], r[0]) if self.order == "CDAB" else (r[0], r[1])
            return struct.unpack(">f", struct.pack(">HH", hi, lo))[0]
        if t["type"] == "int":
            return r[0] - 0x10000 if r[0] >= 0x8000 else r[0]
        return bool(r[0])

    def _enc(self, t, v):
        if t["type"] == "float":
            hi, lo = struct.unpack(">HH", struct.pack(">f", float(v)))
            return [lo, hi] if self.order == "CDAB" else [hi, lo]
        if t["type"] == "int":
            return [int(v) & 0xFFFF]
        return [1 if v else 0]

    def read(self, io):
        regs = []
        a = self.lo
        while a < self.hi:                       # не более 120 регистров за запрос
            n = min(120, self.hi - a)
            r = self.c.read_holding_registers(a, count=n)
            if r.isError():
                raise IOError(r)
            regs += r.registers
            a += n
        for t in self.tags:
            k = int(t["mb"]) - self.lo
            dict.__setitem__(io, t["tag"], self._dec(t, regs[k:k + 2]))

    def write(self, io):
        by = {t["tag"]: t for t in self.tags}
        for k, v in io.dirty.items():
            t = by.get(k)
            if t is None or t["dir"] != "W":  # внутренняя переменная программы / вход — не пишем
                continue
            self.c.write_registers(int(t["mb"]), self._enc(t, v))
        io.dirty.clear()

    def close(self):
        self.c.close()


def load_map(path):
    if not path:
        return None
    raw = open(path, encoding="utf-8-sig").read().splitlines()
    delim = ";" if raw[0].count(";") >= raw[0].count(",") else ","
    rows = []
    for r in csv.DictReader([l for l in raw if l.strip() and not l.lstrip().startswith("#")], delimiter=delim):
        r = {(k or "").strip().lower(): (v or "").strip() for k, v in r.items()}
        if r.get("tag"):
            r["dir"] = (r.get("dir") or "R").upper()[:1]
            r["type"] = (r.get("type") or "float").lower()
            rows.append(r)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ua")
    ap.add_argument("--modbus")
    ap.add_argument("--tags")
    ap.add_argument("--word-order", default="ABCD", choices=["ABCD", "CDAB"])
    ap.add_argument("--program", required=True)
    ap.add_argument("--scan", type=float, default=0.2, help="период сканирования, с")
    ap.add_argument("--time", type=float, default=0, help="остановиться через N с")
    ap.add_argument("--log")
    ap.add_argument("--print-every", type=float, default=5)
    ap.add_argument("--sim-time", action="store_true",
                    help="dt таймеров/ПИД = приращение модельного времени Sim.Time (мост с --speed > 1)")
    a = ap.parse_args()
    tags = load_map(a.tags)
    if a.modbus and not tags:
        raise SystemExit("для Modbus нужна --tags")
    dev = UaIO(a.ua, tags) if a.ua else MbIO(a.modbus, tags, a.word_order)
    spec = importlib.util.spec_from_file_location("plcprog", a.program)
    prog = importlib.util.module_from_spec(spec)
    sys.modules["plcprog"] = prog
    spec.loader.exec_module(prog)
    io = IO()
    dev.read(io)
    if hasattr(prog, "init"):
        prog.init(io)
    dev.write(io)
    logw = None
    cols = list(io.keys())
    if a.log:
        lf = open(a.log, "w", encoding="utf-8-sig", newline="")
        logw = csv.writer(lf, delimiter=";")
        logw.writerow(["t, s", "sim_t, s"] + cols)
    t0 = time.perf_counter()
    last_print = -1e9
    last_sim = None
    try:
        while True:
            w0 = time.perf_counter()
            try:
                dev.read(io)
            except Exception as ex:
                print(f"!! нет связи с объектом ({type(ex).__name__}: {ex}) — стоп", flush=True)
                break
            io.t = w0 - t0
            dt = a.scan
            if a.sim_time and io.sim_t is not None:
                dt = max(0.0, io.sim_t - last_sim) if last_sim is not None else 0.0
                last_sim = io.sim_t
            prog.scan(io, dt)
            try:
                dev.write(io)
            except Exception as ex:
                print(f"!! запись не прошла ({type(ex).__name__}: {ex}) — стоп", flush=True)
                break
            if logw:
                logw.writerow([f"{io.t:.2f}", "" if io.sim_t is None else f"{io.sim_t:.2f}"] +
                              [int(io[c]) if isinstance(io.get(c), bool) else io.get(c) for c in cols])
            if io.t - last_print >= a.print_every:
                last_print = io.t
                show = getattr(prog, "SHOW", cols[:6])
                print(f"t={io.t:7.1f}  sim={io.sim_t if io.sim_t is None else round(io.sim_t, 1)}  " +
                      "  ".join(f"{k}={io.get(k):.4g}" if isinstance(io.get(k), float) else f"{k}={io.get(k)}"
                                for k in show), flush=True)
            if a.time and io.t >= a.time:
                break
            time.sleep(max(0.0, a.scan - (time.perf_counter() - w0)))
    except KeyboardInterrupt:
        pass
    finally:
        if logw:
            lf.close()
        try:
            dev.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
