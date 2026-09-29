# Насосная станция для ПЛК: ёмкость (сепаратор с азотной «подушкой» и дыхательным клапаном) → насос с характеристикой
# (Simple Curve) → обратный клапан → напорная задвижка. Пуск/останов насоса — /P1.Switch = On|Off.
# Проверка: python scripts/dyn.py --script examples/19_pump_station.tst --tend 900 --dt 5
#   --event "60:/P1.Switch = Off" --event "400:/P1.Switch = On"
#   --rec "/TK.Liq0Level%=Уровень" --rec "/P1.In.MassFlow@t/h=G насоса" --rec "/Feed.In.MassFlow@t/h=G притока" --rec "/P1.PumpSpeed@rpm=n"
#   --rec "/S4.In.P@kPa=P нагнетания" --png pump.png
# ---------- стационар ----------
units SI
hold
$RootThermo = VirtualMaterials.Advanced_Peng-Robinson
/ -> $RootThermo
$RootThermo + WATER NITROGEN
go
/Feed = Stream.Stream_Material()
/Feed.In.T = 20 C
/Feed.In.P = 200 kPa
/Feed.In.Fraction = 0.999 0.001
/Feed.In.MassFlow = 30000 kg/h
/VIN = Valve.Valve()
/VIN.In -> /Feed.Out
/VIN.Out.P = 110 kPa
/VIN.%Opening = 50
/S1 = Stream.Stream_Material()
/S1.In -> /VIN.Out
/TK = Flash.SimpleFlash("LiquidPhases = 1")
/TK.In -> /S1.Out
/TK.Orientation = Vertical
/TK.Diameter = 2.0 m
/TK.Length = 5.0 m
/G1 = Stream.Stream_Material()
/G1.In -> /TK.Vap
/VV = Valve.Valve()
/VV.In -> /G1.Out
/VV.Out.P = 101.325 kPa
/VV.%Opening = 50
/Vent = Stream.Stream_Material()
/Vent.In -> /VV.Out
/L1 = Stream.Stream_Material()
/L1.In -> /TK.Liq0
/P1 = Pump.PumpWithCurve("IgnoreCurve = 1; Efficiency = None")
/P1.In -> /L1.Out
/P1.UseDesignPoint = 1
/P1.DesSpeed = 2950 rpm
/P1.DesFlow = 35 m3/h
/P1.DesHead = 40 m
/P1.DesEfficiency = 70 %
/P1.PumpSpeed = 2950 rpm
/S3 = Stream.Stream_Material()
/S3.In -> /P1.Out
/VCHK = Valve.Valve()
/VCHK.In -> /S3.Out
/VCHK.CheckValve = 1
/VCHK.Cv = 200
/S4 = Stream.Stream_Material()
/S4.In -> /VCHK.Out
/VD = Valve.Valve()
/VD.In -> /S4.Out
/VD.Out.P = 300 kPa
/VD.%Opening = 50
/Out = Stream.Stream_Material()
/Out.In -> /VD.Out
# в стационаре: Cv VIN 94.49, VV 10.96, VD 45.63; напор 43.3 м при 30 т/ч, P нагнетания 534 кПа
# ---------- динамика ----------
/ActiveEngine = 2
init / / SteadyState
/VIN.Cv = 94.49
/VV.Cv = 10.96
/VD.Cv = 45.63
/TK.Liq0Level% = 50
/Feed.In.MassFlow =
/Vent.In.P = 101.325 kPa
/Out.In.P = 300 kPa
# ВНИМАНИЕ: init сбрасывает характеристику насоса на умолчания (DesFlow 3600 м3/ч, DesHead 10 м, DesSpeed 3600)
# и выключает обратный клапан (CheckValve показывает 1, но InternalVal = 0) — задать заново:
/P1.DesSpeed = 2950 rpm
/P1.DesFlow = 35 m3/h
/P1.DesHead = 40 m
/P1.DesEfficiency = 70 %
/P1.PumpSpeed = 2950 rpm
/VCHK.CheckValve = 1
/VCHK.Cv = 200
# ---------- КИП для ПЛК ----------
/LT200 = Controller.Controller()
/LT200.In ->> /TK.Liq0Level%
/LT200.MinInput = 0 %
/LT200.MaxInput = 100 %
/LT200.Mode = Indicator
/FT201 = Controller.Controller()
/FT201.In ->> /S3.In.MassFlow
/FT201.MinInput = 0 kg/h
/FT201.MaxInput = 60000 kg/h
/FT201.Mode = Indicator
