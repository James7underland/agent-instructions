# Сепаратор метан/вода с клапанами и регулированием уровня (LIC) и давления (PIC) — стационар + динамика.
# Сырьё 5 МПа → VIN (50 %) → вертикальный сепаратор Ø1,0×3,0 м (4 МПа) → газ через VG (→ 3 МПа), вода через VL (→ 1 МПа).
# Запуск: python scripts/dyn.py --script examples/09_separator_methane_water.tst --tend 900 --dt 5
#   --event "60:/Feed.In.P = 5500 kPa" --event "300:/LIC.Target = 65 %" --event "600:/PIC.Target = 3800 kPa"
#   --rec "/SEP.Liq0Level%=Уровень" --rec "/LIC.Target=SP уровня" --rec "/G1.In.P@kPa=P сепаратора"
#   --rec "/PIC.Target@kPa=SP давления" --rec "/LIC.OP=OP LV" --rec "/PIC.OP=OP PV" --png sep.png
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
# в стационаре при заданных P и открытии 50 % движок рассчитал Cv: VIN 24.90, VG 25.32, VL 1.524
# ---------- динамика ----------
/ActiveEngine = 2
init / / SteadyState
# ВНИМАНИЕ: после init у динамической копии Cv = 1 и уровень 0 — задать явно
/VIN.Cv = 24.90
/VG.Cv = 25.32
/VL.Cv = 1.524
/SEP.Liq0Level% = 50
# граничные условия по давлению (расходы теперь определяют клапаны)
/Feed.In.MoleFlow =
/Gas.In.P = 3000 kPa
/Water.In.P = 1000 kPa
# LIC: уровень воды → клапан воды (PV растёт → открывать: Direct)
/LIC = Controller.Controller()
/LIC.In ->> /SEP.Liq0Level%
/LIC.Out -> /VL.%Opening
/LIC.MinInput = 0 %
/LIC.MaxInput = 100 %
/LIC.Action = Direct
/LIC.Kp = 2
/LIC.Ti = 5 min
/LIC.Target = 50 %
/LIC.Mode = Manual
/LIC.OP = 50 %
/LIC.Mode = Automatic
# PIC: давление газа (переменная ПОТОКА /G1.In.P — не /SEP.Vap.P) → клапан газа (Direct)
/PIC = Controller.Controller()
/PIC.In ->> /G1.In.P
/PIC.Out -> /VG.%Opening
/PIC.MinInput = 3000 kPa
/PIC.MaxInput = 5000 kPa
/PIC.Action = Direct
/PIC.Kp = 1
/PIC.Ti = 1 min
/PIC.Target = 4000 kPa
/PIC.Mode = Manual
/PIC.OP = 50 %
/PIC.Mode = Automatic
