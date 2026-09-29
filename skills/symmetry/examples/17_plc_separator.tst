# Объект для ПЛК: сепаратор метан/вода БЕЗ встроенных регуляторов — управлять будет внешний ПЛК (через plcbridge.py).
# Клапаны с реальными приводами (время хода, положение при отказе), датчики — Controller в режиме Indicator
# (шкала, шум, уставки сигнализаций), как КИП на реальном объекте. Карта тегов: examples/17_plc_tags.csv.
# Сборка и сохранение:  python scripts/sym.py run examples/17_plc_separator.tst --save plc_sep.vsym
#   (команды после "/ActiveEngine = 2" выполняются без Solve — sym.py сам не пересчитывает в динамике)
# Запуск моста:  python scripts/plcbridge.py --recall plc_sep.vsym --tags examples/17_plc_tags.csv --ua 4840 --modbus 5020
# ---------- стационар ----------
units SI
hold
$RootThermo = VirtualMaterials.APRNGL2
/ -> $RootThermo
$RootThermo + METHANE WATER
go
/Feed = Stream.Stream_Material()
/Feed.In.T = 25 C
/Feed.In.P = 5000 kPa
/Feed.In.MoleFlow = 500 kmol/h
/Feed.In.Fraction = 0.6 0.4
/VIN = Valve.Valve()
/VIN.In -> /Feed.Out
/VIN.Out.P = 4000 kPa
/VIN.%Opening = 50
/S1 = Stream.Stream_Material()
/S1.In -> /VIN.Out
/SEP = Flash.SimpleFlash("LiquidPhases = 1")
/SEP.In -> /S1.Out
/SEP.Orientation = Vertical
/SEP.Diameter = 1.0 m
/SEP.Length = 3.0 m
/G1 = Stream.Stream_Material()
/G1.In -> /SEP.Vap
/L1 = Stream.Stream_Material()
/L1.In -> /SEP.Liq0
/VG = Valve.Valve()
/VG.In -> /G1.Out
/VG.Out.P = 3000 kPa
/VG.%Opening = 50
/Gas = Stream.Stream_Material()
/Gas.In -> /VG.Out
/VL = Valve.Valve()
/VL.In -> /L1.Out
/VL.Out.P = 1000 kPa
/VL.%Opening = 50
/Water = Stream.Stream_Material()
/Water.In -> /VL.Out
# ---------- динамика ----------
/ActiveEngine = 2
init / / SteadyState
/VIN.Cv = 24.90
/VG.Cv = 25.32
/VL.Cv = 1.524
/SEP.Liq0Level% = 50
/Feed.In.MoleFlow =
/Gas.In.P = 3000 kPa
/Water.In.P = 1000 kPa
# ---------- исполнительные механизмы ----------
# ВНИМАНИЕ (2023.2): ActuatorType/Linear_Speed/Time_Constant клапана работают ТОЛЬКО при отказе (ActuatorFailed = 1),
# на смену %Opening клапан переходит мгновенно. Время хода по команде моделируем «позиционером» — регулятор в Manual
# с рампой выхода: ПЛК пишет OPTarget, OP (= %Opening клапана) идёт к нему со скоростью SPRateLim (единицы %/s или %/min; без единиц — ошибка «Ambiguous unit %»; не задана — 5 %/s).
/ZVL = Controller.Controller()
/ZVL.Out -> /VL.%Opening
/ZVL.Mode = Manual
/ZVL.OP = 50 %
/ZVL.Setpoint_Ramp_Mode = Output
/ZVL.SPRateLim = 5 %/s
/ZVL.Ramping_Active = 1
/ZVL.OPTarget = 50 %
/ZVG = Controller.Controller()
/ZVG.Out -> /VG.%Opening
/ZVG.Mode = Manual
/ZVG.OP = 50 %
/ZVG.Setpoint_Ramp_Mode = Output
/ZVG.SPRateLim = 3.333 %/s
/ZVG.Ramping_Active = 1
/ZVG.OPTarget = 50 %
/ZVIN = Controller.Controller()
/ZVIN.Out -> /VIN.%Opening
/ZVIN.Mode = Manual
/ZVIN.OP = 50 %
/ZVIN.Setpoint_Ramp_Mode = Output
/ZVIN.SPRateLim = 20 %/s
/ZVIN.Ramping_Active = 1
/ZVIN.OPTarget = 50 %
# положение при отказе привода (для проверки реакции ПЛК): /VL.ActuatorFailed = 1 → клапан уходит в FailClosed
# со скоростью Linear_Speed (это работает)
/VL.ActuatorType = Linear
/VL.Linear_Speed = 20 s
/VL.ActuatorFailPosition = FailClosed
/VG.ActuatorType = Linear
/VG.Linear_Speed = 30 s
/VG.ActuatorFailPosition = FailOpen
/VIN.ActuatorType = Linear
/VIN.Linear_Speed = 5 s
/VIN.ActuatorFailPosition = FailClosed
# ---------- датчики (КИП) ----------
# Indicator: PV = шкалированное значение, шкала MinInput..MaxInput; шум NoiseMag (в единицах PV)
/LT100 = Controller.Controller()
/LT100.In ->> /SEP.Liq0Level%
/LT100.MinInput = 0 %
/LT100.MaxInput = 100 %
/LT100.Mode = Indicator
/PT100 = Controller.Controller()
/PT100.In ->> /G1.In.P
/PT100.MinInput = 0 kPa
/PT100.MaxInput = 6000 kPa
/PT100.Mode = Indicator
/FT100 = Controller.Controller()
/FT100.In ->> /Feed.In.MoleFlow
/FT100.MinInput = 0 kmol/h
/FT100.MaxInput = 1000 kmol/h
/FT100.Mode = Indicator
