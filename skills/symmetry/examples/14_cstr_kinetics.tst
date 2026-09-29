# CSTR с кинетикой: изомеризация н-бутан → изобутан, 1-й порядок, k = A·exp(-E/RT) = 0,002 1/с (E = 0),
# жидкая фаза 2 МПа, изотермически 30 °C, V = 1 м³. Проверка: X = kτ/(1+kτ), τ = V/Qвых = 352,5 с →
# X = 0,4134 (аналитика), Symmetry 0,4120 (−0,3 %). Если UseLevel не выключить — 0,2605 (половина объёма).
units SI
hold
$RootThermo = VirtualMaterials.Advanced_Peng-Robinson
/ -> $RootThermo
$RootThermo + n-BUTANE ISOBUTANE
go
/Feed = Stream.Stream_Material()
/Feed.In.T = 30 C
/Feed.In.P = 2000 kPa
/Feed.In.MoleFlow = 100 kmol/h
/Feed.In.Fraction = 1 0
/R1 = KineticReactor.CSTR()
/R1.In -> /Feed.Out
/R1.Volume = 1 m3
/R1.DeltaP = 0 kPa
# UseLevel = 1 (по умолчанию): реакция только в жидкости при уровне 50 % → реакционный объём = 0,5·Volume!
/R1.UseLevel = 0
/R1.Out.T = 30 C
/R1.NumberRxn = 1
/R1.Rxn0.Formula = Isom:1-!0
/R1.CustomEquationUnitSet = SI
# кинетика задаётся СИГНАЛЬНЫМИ портами Rxn0.A / Rxn0.E (Ar/Er — обратная); FwdA/FwdE — лишь поля GUI, движок их не берёт
# E = 0 считается «не задано» (Missing E) — даём 1 кДж/кмоль: exp(-1/(R·T)) = 0,9996
/R1.Rxn0.A = 0.002
/R1.Rxn0.E = 1 kJ/kmol
/R1.Rxn0.Ar = 0
/R1.Rxn0.Er = 1 kJ/kmol
/R1.Rxn0.FwdOrder_n-BUTANE = 1
/R1.Rxn0.FwdOrder_ISOBUTANE = 0
/Prod = Stream.Stream_Material()
/Prod.In -> /R1.Out
/Q = Stream.Stream_Energy()
/Q.In -> /R1.OutQ
/Prod.Out.Fraction
/Prod.Out.VolumeFlow
/Prod.Out.VapFrac
/Q.In.Energy
