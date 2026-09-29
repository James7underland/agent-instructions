# Нагреватель в динамике + регулятор температуры (TIC → тепловая нагрузка InQ).
# Как заставить Heater/Cooler работать в динамике (known-issues 47, решено 2026-09-27):
#   1) НЕ подключать энергопоток Stream_Energy к InQ/OutQ — нагрузку задавать прямо на порту (/H.InQ = 50 kW)
#      или регулятором (/TIC.Out -> /H.InQ); с энергопотоком — «Pressure flow solver - Unit Op /.H cannot solve»;
#   2) после init снять DeltaP и задать проводимость k не меньше ~0.01 m2 (k из стационара ~6e-5 → тот же сбой);
#      нужный перепад давления моделировать клапаном;
#   3) снять Out.T (в динамике T выхода — результат баланса тепла в объёме Volume).
# Запуск: python scripts/dyn.py --script examples/18_dyn_heater_tic.tst --tend 900 --dt 5
#   --event "300:/TIC.Target = 70 C" --event "600:/VIN.%Opening = 80"
#   --rec "/S2.In.T@C=T выхода" --rec "/TIC.Target@C=SP" --rec "/H.InQ@kW=Q" --rec "/Feed.In.MassFlow@kg/h=F" --png heater.png
# ---------- стационар ----------
units SI
hold
$RootThermo = VirtualMaterials.Advanced_Peng-Robinson
/ -> $RootThermo
$RootThermo + WATER
go
/Feed = Stream.Stream_Material()
/Feed.In.T = 20 C
/Feed.In.P = 300 kPa
/Feed.In.Fraction = 1
/Feed.In.MassFlow = 1000 kg/h
/VIN = Valve.Valve()
/VIN.In -> /Feed.Out
/VIN.Out.P = 250 kPa
/VIN.%Opening = 50
/S1 = Stream.Stream_Material()
/S1.In -> /VIN.Out
/H = Heater.Heater("NumberSegments = 1; DeltaP.DP = None")
/H.In -> /S1.Out
/H.DeltaP = 0 kPa
/H.Out.T = 60 C
/H.Volume = 0.1 m3
/S2 = Stream.Stream_Material()
/S2.In -> /H.Out
/VOUT = Valve.Valve()
/VOUT.In -> /S2.Out
/VOUT.Out.P = 150 kPa
/VOUT.%Opening = 50
/Prod = Stream.Stream_Material()
/Prod.In -> /VOUT.Out
# в стационаре: Cv VIN = 3.275, VOUT = 2.334, нагрузка ≈ 46.9 kW
# ---------- динамика ----------
/ActiveEngine = 2
init / / SteadyState
/VIN.Cv = 3.275
/VOUT.Cv = 2.334
/Feed.In.MassFlow =
/Prod.In.P = 150 kPa
/H.DeltaP =
/H.k = 1 m2
/H.Out.T =
/H.Volume = 0.1 m3
/H.InQ = 46.9 kW
# TIC: T выхода ниже задания → больше тепла: Reverse. Шкала OP — в единицах нагрузки (Minimum/Maximum)
/TIC = Controller.Controller()
/TIC.In ->> /S2.In.T
/TIC.Out -> /H.InQ
/TIC.MinInput = 0 C
/TIC.MaxInput = 120 C
/TIC.Minimum = 0 kW
/TIC.Maximum = 150 kW
/TIC.Action = Reverse
/TIC.Kp = 3
/TIC.Ti = 5 min
/TIC.Target = 60 C
/TIC.Mode = Manual
/TIC.OP = 31 %
/TIC.Mode = Automatic
