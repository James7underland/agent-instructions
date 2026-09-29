# PFR с кинетикой (тот же пример, что 14): изомеризация н-бутан → изобутан, 1-й порядок, k = A·exp(-E/RT) = 0,002 1/с (E = 0),
# жидкая фаза 2 МПа, изотермически 30 °C, Ø0,5 × 5,093 м (V = 1 м³), 20 участков.
# Проверка: X = 1 − exp(−kτ) = 0,506 (по входному расходу), Symmetry 0,498 (−1,5 %: объёмный расход меняется по длине).
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
/R1 = KineticReactor.PFR("NumberSections = 20; Roughness = 0.045 mm")
/R1.In -> /Feed.Out
/R1.Diameter = 0.5 m
/R1.Length = 5.093 m
/R1.DeltaP = 0 kPa
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
