#!/usr/bin/env python3
"""plcbridge.py — динамическая модель Symmetry как «объект» для ПЛК: OPC UA сервер / OPC UA клиент / Modbus TCP.

Движок Symmetry (COM, динамика) крутится шагами dt в своём потоке, темп — реальное время × --speed.
Каждый шаг: команды ПЛК (теги W) → модель → интегратор +dt → показания (теги R) → ПЛК.

  python plcbridge.py --recall CASE.vsym --tags tags.csv [--ua 4841] [--modbus 5020]
                      [--ua-client opc.tcp://plc:4840] [--dt 0.5] [--speed 1] [--duration 600]
                      [--to-dynamics | --reinit] [--script extra.tst] [--pre CMD]... [--log trend.csv]
                      [--word-order ABCD|CDAB] [--host 0.0.0.0] [--dry]
  python plcbridge.py --gui 18686 --tags tags.csv --ua 4841     # модель в открытом GUI (видно PFD), dt ≥ 0.5 с

Карта тегов (CSV, разделитель ';' или ',', UTF-8; или OPC XML Symmetry — OPCTag/SimPath/CanWrite/UnitName):
  tag;path;unit;dir;type;mb;expr;desc
  LT100.PV;/LT100.In;%;R;float;0;;Уровень в С-1
  LV100.CMD;/ZVL.OPTarget;%;W;float;100;;Задание клапану
  XV100.OPEN;/ZVIN.OPTarget;%;W;bool;110;100*x;Открыть отсекатель (1 → 100 %)
  XV100.ZSO;/VIN.%Opening;%;R;bool;12;x>98;Концевик «открыт»
  dir  R — модель → ПЛК, W — ПЛК → модель (начальное значение берётся из модели)
  type float (Double; Modbus float32 = 2 регистра) | int (Int32; Modbus int16) | bool (Boolean; Modbus 0/1)
  mb   адрес holding-регистра (с 0); тот же адрес читается функцией 4 (input registers)
  expr пересчёт на Python от x: R — из значения модели в значение ПЛК (шкала 4–20 мА: (x-0)/100*27648,
       дискрет: x>98); W — из значения ПЛК в значение модели (100*x; 'On' if x else 'Off')
  unit единицы модели (как в командах Symmetry: kPa, C, m3/h, %, kmol/h); пусто — единицы по умолчанию (SI)

OPC UA: endpoint opc.tcp://<host>:<port>/symmetry/, без шифрования, анонимно; узлы ns=2;s=<tag>
(папки по префиксу до первой точки), служебные узлы Sim.Time, Sim.Run (пауза/пуск), Sim.Speed, Sim.Status,
Sim.Step, Sim.Healthy. --ua-client: мост сам подключается к OPC UA серверу ПЛК: колонка ua — NodeId в ПЛК
(напр. ns=4;s=|var|PLC.Application.GVL.LT100_PV); R-теги пишутся в ПЛК, W-теги читаются из ПЛК.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import math
import os
import re
import struct
import sys
import threading
import time
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sym  # noqa: E402


# ---------------------------------------------------------------- теги
class Tag:
    def __init__(self, name, path, unit="", dir="R", type="float", mb=None, expr="", desc="", ua=""):
        self.name, self.path, self.unit = name.strip(), sym.unmangle(path.strip()), (unit or "").strip()
        if self.unit.lower() in ("active set", "default", "-"):
            self.unit = ""
        self.dir = (dir or "R").strip().upper()[:1]
        self.type = (type or "float").strip().lower()
        self.mb = int(mb) if str(mb or "").strip() not in ("", "None") else None
        self.expr = (expr or "").strip()
        self.desc, self.ua = desc or "", (ua or "").strip()
        self._code = compile(self.expr, f"<{self.name}>", "eval") if self.expr else None
        self.plc = None        # значение на стороне ПЛК
        self.model = None      # значение модели (в единицах unit)

    def f(self, x):
        """R: модель → ПЛК; W: ПЛК → модель."""
        v = eval(self._code, {"math": math, "min": min, "max": max, "abs": abs, "round": round}, {"x": x}) \
            if self._code else x
        return self.cast(v) if self.dir == "R" else v

    def cast(self, v):
        if v is None:
            return None
        if isinstance(v, str):
            v = 1 if v.strip().lower() in ("on", "yes", "true", "1", "open", "running") else 0
        if self.type == "bool":
            return bool(v)
        if self.type == "int":
            return int(round(float(v)))
        return float(v)

    def inverse(self, model_value):
        """Начальное значение W-тега по значению модели: линейное обращение expr (a*x+b)."""
        if model_value is None or isinstance(model_value, str):
            return self.cast(0)
        if not self._code:
            return self.cast(model_value)
        try:
            b = float(self.f(0)); a = float(self.f(1)) - b
            return self.cast((model_value - b) / a) if a else self.cast(0)
        except Exception:
            return self.cast(0)


def load_tags(path):
    tags = []
    if path.lower().endswith(".xml"):
        for v in ET.parse(path).iter("Variable"):
            tags.append(Tag(v.findtext("OPCTag"), v.findtext("SimPath"), v.findtext("UnitName") or "",
                            "W" if (v.findtext("CanWrite") or "").lower() == "true" else "R",
                            "float" if (v.findtext("VarType") or "Float").lower() in ("float", "double") else "int"))
        return tags
    raw = open(path, encoding="utf-8-sig").read()
    delim = ";" if raw.splitlines()[0].count(";") >= raw.splitlines()[0].count(",") else ","
    for row in csv.DictReader([l for l in raw.splitlines() if l.strip() and not l.lstrip().startswith("#")],
                              delimiter=delim):
        row = {(k or "").strip().lower(): (v or "") for k, v in row.items()}
        if not row.get("tag") or not row.get("path"):
            continue
        tags.append(Tag(row["tag"], row["path"], row.get("unit", ""), row.get("dir", "R"), row.get("type", "float"),
                        row.get("mb"), row.get("expr", ""), row.get("desc", ""), row.get("ua", "")))
    names = [t.name for t in tags]
    dup = {n for n in names if names.count(n) > 1}
    if dup:
        raise SystemExit(f"повторяющиеся теги: {sorted(dup)}")
    return tags


# ---------------------------------------------------------------- общее состояние
class Shared:
    def __init__(self, speed):
        self.lock = threading.Lock()
        self.writes = {}           # tag -> значение ПЛК (последнее)
        self.running = True
        self.speed = speed
        self.time = 0.0
        self.step = 0
        self.status = "starting"
        self.healthy = False
        self.ready = threading.Event()
        self.stop = threading.Event()
        self.wall_ms = 0.0

    def put_write(self, tag, val):
        with self.lock:
            self.writes[tag] = val

    def take_writes(self):
        with self.lock:
            w, self.writes = self.writes, {}
        return w


# ---------------------------------------------------------------- модель
class Sim(threading.Thread):
    def __init__(self, a, tags, sh):
        super().__init__(daemon=True)
        self.a, self.tags, self.sh = a, tags, sh
        self.by_name = {t.name: t for t in tags}
        self.log = None

    def cmd(self, c):
        self.eng.eval(c)
        bad = [m for t, m in self.eng.msgs if t != "Info"]
        self.eng.msgs.clear()
        for m in bad:
            print(f"   !! {c}: {m}", flush=True)
        return not bad

    def read(self, t):
        try:
            v, _ = self.eng.value(t.path, t.unit or None)
        except Exception:
            v = None
        if isinstance(v, (list, tuple)):
            v = v[0] if v else None
        if isinstance(v, float) and abs(v - sym.UNKNOWN) < 1e-6:
            v = None
        return v

    def apply(self, t, x):
        t.plc = x
        v = t.f(x)
        if isinstance(v, bool):
            v = int(v)
        if isinstance(v, str):
            ok = self.cmd(f"{t.path} = {v}")
        else:
            ok = self.cmd(f"{t.path} = {float(v)!r} {t.unit}".rstrip())
        print(f"   {self.sh.time:8.1f} s  {t.name} = {x}  →  {t.path} = {v} {t.unit}{'' if ok else '  (ошибка)'}",
              flush=True)

    def t_now(self):
        v, _ = self.eng.value("/Integrator.IntegratorTime", "s")
        return float(v or 0.0)

    def advance(self, dt):
        target = self.t_now() + dt
        for _ in range(3):
            before = self.t_now()
            self.eng.msgs.clear()
            self.eng.eval(f"/Integrator.StopTime = {target!r} s")
            self.eng.eval("/Integrator.IntegRun = 1")
            while self.eng.e.IsIntegratorRunning:
                time.sleep(0.01)
            now = self.t_now()
            if now >= target - 1e-6:
                return True
            if now <= before + 1e-9:
                why = sorted({m for t, m in self.eng.msgs if t != "Info" or "DYNMsg" in m})[:3]
                self.sh.status = f"интегратор встал на {now:g} с: {why}"
                return False
        return False

    def run(self):
        import pythoncom
        pythoncom.CoInitialize()
        a, sh = self.a, self.sh
        self.eng = eng = sym.Engine()
        eng.e.AddDynamicsSupport2()          # всегда (проверка HasDynamicsSupport в потоке врёт)
        eng.flush()
        if a.recall:
            sym.open_case(eng, a.recall)
        if a.script:
            sym.run_commands(eng, list(sym.iter_script_lines(a.script, [])), quiet=True)
        if a.to_dynamics:
            for c in ("/ActiveEngine = 2", "init / / SteadyState"):
                self.cmd(c)
        elif a.reinit:
            self.cmd("init / / SteadyState")
        for c in ["/Integrator.RealTime = 0"] + a.pre:
            self.cmd(sym.unmangle(c))
        step, _ = eng.value("/Integrator.StepSize", "s")
        if step and a.dt < step - 1e-9:     # иначе интегратор всё равно шагнёт на StepSize (1 с по умолчанию)
            self.cmd(f"/Integrator.StepSize = {a.dt!r} s")
            print(f"# StepSize {step:g} → {a.dt:g} с (шаг обмена меньше шага интегратора)", flush=True)
        elif step and abs(a.dt / step - round(a.dt / step)) > 1e-6:
            print(f"   !! dt = {a.dt:g} с не кратен StepSize = {step:g} с — время будет идти ступенями StepSize", flush=True)
        eng.msgs.clear()
        for t in self.tags:
            t.model = self.read(t)
            if t.dir == "W":
                t.plc = t.inverse(t.model)
            else:
                t.plc = t.f(t.model) if t.model is not None else None
            if t.model is None:
                print(f"   ?? {t.name}: {t.path} не читается (путь/единицы?)", flush=True)
        sh.time = self.t_now()
        sh.status, sh.healthy = "running", True
        if a.log:
            self.log = open(a.log, "w", encoding="utf-8-sig", newline="")
            self.logw = csv.writer(self.log, delimiter=";")
            self.logw.writerow(["t, s"] + [t.name for t in self.tags])
        sh.ready.set()
        t_end = sh.time + a.duration if a.duration else None
        while not sh.stop.is_set():
            if not sh.running:
                time.sleep(0.05)
                for n, x in sh.take_writes().items():        # команды применяем и на паузе
                    self.apply(self.by_name[n], x)
                continue
            w0 = time.perf_counter()
            for n, x in sh.take_writes().items():
                self.apply(self.by_name[n], x)
            t_before = sh.time
            ok = self.advance(a.dt)
            sh.time = self.t_now()
            adv = max(sh.time - t_before, 0.0)
            sh.step += 1
            for t in self.tags:
                t.model = self.read(t)
                if t.dir == "R":
                    try:
                        t.plc = t.f(t.model) if t.model is not None else None
                    except Exception as ex:
                        t.plc = None
                        print(f"   !! expr {t.name}: {ex}", flush=True)
            if self.log:
                self.logw.writerow([f"{sh.time:.3f}"] + [("" if t.plc is None else
                                                          (int(t.plc) if isinstance(t.plc, bool) else t.plc))
                                                         for t in self.tags])
                if sh.step % 20 == 0:
                    self.log.flush()
            sh.healthy = ok
            if not ok:
                print("   !! " + sh.status, flush=True)
                sh.running = False
            el = time.perf_counter() - w0
            sh.wall_ms = el * 1000
            if sh.speed and sh.speed > 0:
                wait = adv / sh.speed - el
                if wait > 0:
                    time.sleep(wait)
            if t_end is not None and sh.time >= t_end - 1e-9:
                sh.status = "done"
                sh.stop.set()
        if self.log:
            self.log.close()
        if a.save:
            print("# save ->", eng.save(os.path.abspath(a.save)), flush=True)


# ---------------------------------------------------------------- модель в живом GUI (REST)
class GuiSim(threading.Thread):
    """Интегратор крутится в самом GUI (RealTime = 1, темп RtScale), мост раз в dt читает/пишет через REST.
    GUI должен быть уже открыт с динамическим кейсом (gui.py launch CASE) и запущен с --HTTPServer."""

    def __init__(self, a, tags, sh):
        super().__init__(daemon=True)
        self.a, self.tags, self.sh = a, tags, sh
        self.by_name = {t.name: t for t in tags}
        self.url = f"http://localhost:{a.gui}/api/actions/json"
        self.log = None
        self.runner = None

    def call(self, name, args, timeout=15):
        import json
        import urllib.request
        req = urllib.request.Request(self.url, data=json.dumps({"call": name, "args": args}).encode(),
                                     headers={"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=timeout).read())

    def cmd(self, c):
        try:
            r = self.call("Eval", {"cmd": c, "solve": 0})
            if r.get("status") not in (0, None):
                print(f"   !! {c}: {r}", flush=True)
            return True
        except Exception as ex:
            print(f"   !! {c}: {type(ex).__name__} — возможно, в GUI открыто модальное окно "
                  f"(gui.py popups / gui.py answer OK)", flush=True)
            return False

    def read_all(self):
        req = [{"p": t.path, "u": sym.UNIT_ALIASES.get(t.unit, t.unit)} if t.unit else t.path for t in self.tags]
        req += [{"p": "/Integrator.IntegratorTime", "u": "s"}, "/Integrator.IntegRun"]
        r = self.call("Values", {"reqVars": req})["resp"]
        for t, v in zip(self.tags, r):
            if isinstance(v, float) and abs(v - sym.UNKNOWN) < 1e-6:
                v = None
            t.model = v
        return float(r[-2] or 0.0), int(r[-1] or 0)

    def apply(self, t, x):
        t.plc = x
        v = t.f(x)
        if isinstance(v, bool):
            v = int(v)
        u = sym.UNIT_ALIASES.get(t.unit, t.unit)
        c = f"{t.path} = {v}" if isinstance(v, str) else f"{t.path} = {float(v)!r} {u}".rstrip()
        ok = self.cmd(c)
        print(f"   {self.sh.time:8.1f} s  {t.name} = {x}  →  {c}{'' if ok else '  (ошибка)'}", flush=True)

    def start_integrator(self):
        def go():
            try:                     # ответ придёт только после остановки интегратора
                self.call("Eval", {"cmd": "/Integrator.IntegRun = 1", "solve": 0}, timeout=24 * 3600)
            except Exception:
                pass
        self.runner = threading.Thread(target=go, daemon=True)
        self.runner.start()

    def run(self):
        a, sh = self.a, self.sh
        try:
            t0, running = self.read_all()
        except Exception as ex:
            sh.status = f"нет связи с GUI на порту {a.gui}: {ex}"
            print("   !! " + sh.status, flush=True)
            return
        if running:
            self.cmd("/Integrator.IntegRun = 0")
            time.sleep(0.5)
        for c in [f"/Integrator.RealTime = 1", f"/Integrator.RtScale = {sh.speed or 1}"] + a.pre:
            self.cmd(sym.unmangle(c))
        t0, _ = self.read_all()
        for t in self.tags:
            if t.dir == "W":
                t.plc = t.inverse(t.model)
            else:
                t.plc = t.f(t.model) if t.model is not None else None
            if t.model is None:
                print(f"   ?? {t.name}: {t.path} не читается (путь/единицы?)", flush=True)
        sh.time, sh.status, sh.healthy = t0, "running (GUI)", True
        if a.log:
            self.log = open(a.log, "w", encoding="utf-8-sig", newline="")
            self.logw = csv.writer(self.log, delimiter=";")
            self.logw.writerow(["t, s"] + [t.name for t in self.tags])
        sh.ready.set()
        t_end = t0 + a.duration if a.duration else None
        self.start_integrator()
        was_running, speed = True, sh.speed
        last_t, still = t0, 0.0
        while not sh.stop.is_set():
            w0 = time.perf_counter()
            if sh.running != was_running:
                if sh.running:
                    self.start_integrator()
                else:
                    self.cmd("/Integrator.IntegRun = 0")
                was_running = sh.running
            if sh.speed != speed and sh.speed:
                speed = sh.speed
                self.cmd(f"/Integrator.RtScale = {speed}")
            for n, x in sh.take_writes().items():
                self.apply(self.by_name[n], x)
            try:
                sh.time, run = self.read_all()
            except Exception as ex:
                sh.status, sh.healthy = f"REST: {type(ex).__name__}", False
                time.sleep(a.dt)
                continue
            for t in self.tags:
                if t.dir == "R":
                    try:
                        t.plc = t.f(t.model) if t.model is not None else None
                    except Exception as ex:
                        t.plc = None
            sh.step += 1
            still = still + a.dt if (sh.running and sh.time <= last_t + 1e-9) else 0.0
            last_t = sh.time
            sh.healthy = still < 5 * a.dt + 3
            sh.status = "running (GUI)" if sh.healthy else "время модели в GUI не идёт (интегратор встал?)"
            if self.log:
                self.logw.writerow([f"{sh.time:.3f}"] + [("" if t.plc is None else
                                                          (int(t.plc) if isinstance(t.plc, bool) else t.plc))
                                                         for t in self.tags])
                if sh.step % 20 == 0:
                    self.log.flush()
            sh.wall_ms = (time.perf_counter() - w0) * 1000
            if t_end is not None and sh.time >= t_end - 1e-9:
                sh.status = "done"
                sh.stop.set()
            time.sleep(max(0.0, a.dt - (time.perf_counter() - w0)))
        self.cmd("/Integrator.IntegRun = 0")
        if self.log:
            self.log.close()


# ---------------------------------------------------------------- кодирование Modbus
def enc(t, v, order):
    if t.type == "float":
        b = struct.pack(">f", float(v if v is not None else float("nan")))
        hi, lo = struct.unpack(">HH", b)
        return [lo, hi] if order == "CDAB" else [hi, lo]
    if t.type == "int":
        return [int(v or 0) & 0xFFFF]
    return [1 if v else 0]


def dec(t, regs, order):
    if t.type == "float":
        hi, lo = (regs[1], regs[0]) if order == "CDAB" else (regs[0], regs[1])
        return struct.unpack(">f", struct.pack(">HH", hi, lo))[0]
    if t.type == "int":
        r = regs[0]
        return r - 0x10000 if r >= 0x8000 else r
    return bool(regs[0])


def nregs(t):
    return 2 if t.type == "float" else 1


# ---------------------------------------------------------------- серверы / клиент
async def ua_server(a, tags, sh):
    from asyncua import Server, ua
    vt = {"float": ua.VariantType.Double, "int": ua.VariantType.Int32, "bool": ua.VariantType.Boolean}
    srv = Server()
    await srv.init()
    srv.set_endpoint(f"opc.tcp://{a.host}:{a.ua}/symmetry/")
    srv.set_server_name("Symmetry PLC bridge")
    srv.set_security_policy([ua.SecurityPolicyType.NoSecurity])
    idx = await srv.register_namespace("urn:symmetry:plcbridge")
    root = await srv.nodes.objects.add_folder(ua.NodeId("Symmetry", idx), "Symmetry")
    folders, nodes = {}, {}
    for t in tags:
        grp = t.name.split(".")[0] if "." in t.name else ""
        parent = root
        if grp:
            if grp not in folders:
                folders[grp] = await root.add_folder(ua.NodeId(f"{grp}/", idx), grp)
            parent = folders[grp]
        init = t.plc if t.plc is not None else t.cast(0)
        n = await parent.add_variable(ua.NodeId(t.name, idx), t.name, ua.Variant(init, vt[t.type]))
        if t.desc:
            await n.write_attribute(ua.AttributeIds.Description,
                                    ua.DataValue(ua.Variant(ua.LocalizedText(t.desc), ua.VariantType.LocalizedText)))
        if t.dir == "W":
            await n.set_writable()
        nodes[t.name] = (n, init)
    simf = await root.add_folder(ua.NodeId("Sim/", idx), "Sim")
    s_time = await simf.add_variable(ua.NodeId("Sim.Time", idx), "Sim.Time", 0.0)
    s_step = await simf.add_variable(ua.NodeId("Sim.Step", idx), "Sim.Step", ua.Variant(0, ua.VariantType.Int64))
    s_stat = await simf.add_variable(ua.NodeId("Sim.Status", idx), "Sim.Status", "starting")
    s_ok = await simf.add_variable(ua.NodeId("Sim.Healthy", idx), "Sim.Healthy", False)
    s_run = await simf.add_variable(ua.NodeId("Sim.Run", idx), "Sim.Run", True)
    s_spd = await simf.add_variable(ua.NodeId("Sim.Speed", idx), "Sim.Speed", float(sh.speed))
    await s_run.set_writable(); await s_spd.set_writable()
    seen = {n: v for n, (_, v) in nodes.items()}
    last_run, last_spd = True, float(sh.speed)
    print(f"# OPC UA: opc.tcp://localhost:{a.ua}/symmetry/  (ns={idx}, NodeId s=<тег>)", flush=True)
    async with srv:
        while not sh.stop.is_set():
            for t in tags:
                n, _ = nodes[t.name]
                if t.dir == "W":
                    v = await n.read_value()
                    if v != seen[t.name]:
                        seen[t.name] = v
                        sh.put_write(t.name, v)
                elif t.plc is not None and t.plc != seen[t.name]:
                    seen[t.name] = t.plc
                    await n.write_value(ua.Variant(t.cast(t.plc), vt[t.type]))
            r = bool(await s_run.read_value())
            if r != last_run:
                last_run = sh.running = r
            sp = float(await s_spd.read_value())
            if sp != last_spd:
                last_spd = sh.speed = sp
            if not sh.healthy and sh.running is False and last_run:
                await s_run.write_value(False); last_run = False
            await s_time.write_value(float(sh.time))
            await s_step.write_value(ua.Variant(sh.step, ua.VariantType.Int64))
            await s_stat.write_value(sh.status)
            await s_ok.write_value(bool(sh.healthy))
            await asyncio.sleep(min(0.1, a.dt / 4))


async def ua_client(a, tags, sh):
    from asyncua import Client, ua
    vt = {"float": ua.VariantType.Double, "int": ua.VariantType.Int32, "bool": ua.VariantType.Boolean}
    ns = a.ua_ns
    def nid(t):
        return t.ua or f"ns={ns};s={t.name}"
    while not sh.stop.is_set():
        try:
            async with Client(url=a.ua_client, timeout=5) as c:
                print(f"# OPC UA клиент подключён к {a.ua_client}", flush=True)
                nodes = {t.name: c.get_node(nid(t)) for t in tags}
                rn = [t for t in tags if t.dir == "R"]
                wn = [t for t in tags if t.dir == "W"]
                seen = {}
                for t in wn:                       # начальное значение команд ПЛК — из модели
                    try:
                        await nodes[t.name].write_value(ua.Variant(t.cast(t.plc), vt[t.type]))
                    except Exception as ex:
                        print(f"   !! запись начального {t.name} ({nid(t)}): {ex}", flush=True)
                    seen[t.name] = t.plc
                last = {}
                while not sh.stop.is_set():
                    if wn:
                        vals = await c.read_values([nodes[t.name] for t in wn])
                        for t, v in zip(wn, vals):
                            if v != seen.get(t.name):
                                seen[t.name] = v
                                sh.put_write(t.name, v)
                    ch = [t for t in rn if t.plc is not None and t.plc != last.get(t.name)]
                    if ch:
                        await c.write_values([nodes[t.name] for t in ch],
                                             [ua.Variant(t.cast(t.plc), vt[t.type]) for t in ch])
                        for t in ch:
                            last[t.name] = t.plc
                    await asyncio.sleep(min(0.1, a.dt / 4))
        except Exception as ex:
            print(f"   !! OPC UA клиент: {ex!r} — переподключение через 3 с", flush=True)
            await asyncio.sleep(3)


async def modbus_server(a, tags, sh):
    from pymodbus.simulator import SimDevice, SimData, DataType
    from pymodbus.server import StartAsyncTcpServer
    mt = [t for t in tags if t.mb is not None]
    size = max([t.mb + nregs(t) for t in mt] + [1])
    regs = [0] * (size + 1)
    owner = {}
    for t in mt:
        for k in range(nregs(t)):
            if t.mb + k in owner:
                raise SystemExit(f"Modbus: адрес {t.mb + k} занят тегами {owner[t.mb + k]} и {t.name}")
            owner[t.mb + k] = t.name
    order = a.word_order
    for t in mt:
        regs[t.mb:t.mb + nregs(t)] = enc(t, t.plc, order)
    wmap = {t.name: t for t in mt if t.dir == "W"}

    async def action(fc, start_address, address, count, current, set_values):
        if set_values is None:
            for i in range(len(current)):
                j = start_address + i
                current[i] = regs[j] if j < len(regs) else 0
            return None
        touched = set()
        for i, v in enumerate(set_values):
            j = address + i
            if j < len(regs):
                regs[j] = int(v)
                if owner.get(j) in wmap:
                    touched.add(owner[j])
        for n in touched:
            t = wmap[n]
            sh.put_write(n, t.cast(dec(t, regs[t.mb:t.mb + nregs(t)], order)))
        return None

    async def refresh():
        while not sh.stop.is_set():
            for t in mt:
                if t.dir == "R" and t.plc is not None:
                    regs[t.mb:t.mb + nregs(t)] = enc(t, t.plc, order)
            await asyncio.sleep(min(0.1, a.dt / 4))

    dev = SimDevice(id=0, simdata=[SimData(0, count=size, datatype=DataType.REGISTERS)], action=action)
    print(f"# Modbus TCP: localhost:{a.modbus}, holding/input регистры 0..{size - 1}, float32 {order}", flush=True)
    asyncio.create_task(refresh())
    await StartAsyncTcpServer(context=dev, address=(a.host, a.modbus))


async def main_async(a, tags, sh):
    jobs = []
    if a.ua:
        jobs.append(asyncio.create_task(ua_server(a, tags, sh)))
    if a.ua_client:
        jobs.append(asyncio.create_task(ua_client(a, tags, sh)))
    if a.modbus:
        jobs.append(asyncio.create_task(modbus_server(a, tags, sh)))
    last = time.time()
    while not sh.stop.is_set():
        await asyncio.sleep(0.2)
        for j in jobs:
            if j.done() and j.exception():
                print("   !! сервер:", repr(j.exception()), flush=True)
                sh.stop.set()
        if time.time() - last >= a.status_every:
            last = time.time()
            vals = "  ".join(f"{t.name}={t.plc:.4g}" if isinstance(t.plc, float) else f"{t.name}={t.plc}"
                             for t in tags[:a.show])
            print(f"# t={sh.time:8.1f} s  шаг {sh.wall_ms:5.0f} мс  {sh.status}  {vals}", flush=True)
    await asyncio.sleep(0.3)
    for j in jobs:
        j.cancel()


def print_map(tags, order):
    print(f"{'тег':24s} {'R/W':3s} {'тип':5s} {'Modbus':>8s}  путь [ед.]  expr")
    for t in tags:
        mb = "" if t.mb is None else (f"{t.mb}-{t.mb + 1}" if t.type == "float" else str(t.mb))
        print(f"{t.name:24s} {t.dir:3s} {t.type:5s} {mb:>8s}  {t.path} [{t.unit}]  {t.expr}")
    print(f"float32 = 2 регистра, порядок слов {order}; адреса с 0 (в ПЛК часто +1 или 40001+)")


def main():
    argv = [sym.unmangle(x) for x in sys.argv[1:]]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--recall")
    ap.add_argument("--gui", type=int, default=0,
                    help="порт REST живого GUI (gui.py launch CASE): интегратор идёт в GUI в реальном времени")
    ap.add_argument("--script", action="append", default=[])
    ap.add_argument("--to-dynamics", action="store_true")
    ap.add_argument("--reinit", action="store_true")
    ap.add_argument("--pre", action="append", default=[])
    ap.add_argument("--tags", required=True)
    ap.add_argument("--ua", type=int, default=0, help="порт OPC UA сервера моста (4841; 4840 занят TreiUA)")
    ap.add_argument("--ua-client", help="URL OPC UA сервера ПЛК (мост — клиент)")
    ap.add_argument("--ua-ns", type=int, default=2, help="ns для NodeId без колонки ua (режим клиента)")
    ap.add_argument("--modbus", type=int, default=0, help="порт Modbus TCP сервера (502 / 5020)")
    ap.add_argument("--word-order", default="ABCD", choices=["ABCD", "CDAB"])
    ap.add_argument("--host", default="127.0.0.1",
                    help="адрес прослушивания: 127.0.0.1 — только этот ПК; 0.0.0.0 — для ПЛК в сети (брандмауэр!)")
    ap.add_argument("--dt", type=float, default=0.5, help="шаг обмена = шаг модели, с")
    ap.add_argument("--speed", type=float, default=1.0, help="темп: 1 — реальное время, 0 — как можно быстрее")
    ap.add_argument("--duration", type=float, default=0, help="остановиться через N с модельного времени")
    ap.add_argument("--log", help="CSV тренд всех тегов (значения ПЛК) по шагам")
    ap.add_argument("--save", help="сохранить кейс при остановке")
    ap.add_argument("--status-every", type=float, default=5.0)
    ap.add_argument("--show", type=int, default=6, help="сколько тегов печатать в строке статуса")
    ap.add_argument("--dry", action="store_true", help="только проверить карту тегов")
    a = ap.parse_args(argv)
    tags = load_tags(a.tags)
    print_map(tags, a.word_order)
    if a.dry:
        return
    if not (a.ua or a.modbus or a.ua_client):
        print("# нет --ua / --modbus / --ua-client: только прогон модели с журналом")
    sh = Shared(a.speed)
    sim = GuiSim(a, tags, sh) if a.gui else Sim(a, tags, sh)
    sim.start()
    while not sh.ready.wait(1):
        if not sim.is_alive():
            raise SystemExit("модель не запустилась")
    print(f"# модель готова, t = {sh.time:g} с; dt = {a.dt} с, темп ×{a.speed:g}. Ctrl+C — стоп", flush=True)
    try:
        asyncio.run(main_async(a, tags, sh))
    except KeyboardInterrupt:
        pass
    sh.stop.set()
    sim.join(timeout=30)
    print(f"# стоп: t = {sh.time:g} с, шагов {sh.step}", flush=True)
    sym.hard_exit(0)


if __name__ == "__main__":
    main()
