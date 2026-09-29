# Динамика: регулирование расхода воды клапаном (PI-регулятор).
# Стационар строится командами ниже, перевод в динамику — "/ActiveEngine = 2" и "init / / SteadyState"
# (для готового стационарного кейса то же делает ключ dyn.py --to-dynamics).
# Регулятор подключается после init и стартует с OP = 0 — ключ --settle 300 даёт ему выйти на режим до записи.
# Запуск (одной строкой): python scripts/dyn.py --script examples/08_dyn_flow_control.tst --settle 300 --tend 600 --dt 2
#   --event "60:/CN1.Target = 3 m3/h" --event "300:/CN1.Target = 1.5 m3/h"
#   --rec "/CN1.In@m3/h=PV" --rec "/CN1.Target@m3/h=SP" --rec "/CN1.OP=OP" --png flow.png
units SI
hold
$RootThermo = VirtualMaterials.Advanced_Peng-Robinson
/ -> $RootThermo
$RootThermo + WATER
go
/S1 = Stream.Stream_Material()
/S1.In.T = 15 C
/S1.In.P = 200 kPa
/S1.In.Fraction = 1
/S1.In.VolumeFlow = 2 m3/h
/V1 = Valve.Valve()
/V1.In -> /S1.Out
/V1.Cv = 20
/S2 = Stream.Stream_Material()
/S2.In -> /V1.Out
# в динамике расход определяется перепадом давления: снимаем спецификацию расхода, задаём давление после клапана
/ActiveEngine = 2
init / / SteadyState
/S1.In.VolumeFlow =
/S2.In.P = 190 kPa
# PI-регулятор: PV = объёмный расход S1 (->> — подключение к переменной), OP -> открытие клапана
/CN1 = Controller.Controller()
/CN1.SSActive = 0
/CN1.In ->> /S1.In.VolumeFlow
/CN1.Out -> /V1.%Opening
/CN1.Action = Reverse            # расход клапаном: PV растёт → OP уменьшать. Direct = OP растёт при PV > SP
/CN1.Mode = Automatic
/CN1.Kp = 2
/CN1.Ti = 0.3 min
/CN1.MinInput = 0 m3/h
/CN1.MaxInput = 4 m3/h
/CN1.Target = 2 m3/h
