# Рецикл: смеситель -> охладитель -> сепаратор; часть жидкости через делитель возвращается в смеситель.
# Оценки (~=) на потоке рецикла задают начальное приближение, решатель (Broyden по умолчанию) сводит цикл.
units SI
hold
$RootThermo = VirtualMaterials.Advanced_Peng-Robinson
/ -> $RootThermo
$RootThermo + METHANE ETHANE PROPANE n-BUTANE n-PENTANE
go
/Feed = Stream.Stream_Material()
/Feed.In.T = 30 C
/Feed.In.P = 3000 kPa
/Feed.In.MoleFlow = 200 kmol/h
/Feed.In.Fraction = 0.6 0.15 0.12 0.08 0.05
hold
/M1 = Mixer.Mixer("NumberStreamsIn = 2")
/M1.In0 -> /Feed.Out
/S1 = Stream.Stream_Material()
/S1.In -> /M1.Out
/C1 = Heater.Cooler("NumberSegments = 1; DeltaP.DP = None")
/C1.In -> /S1.Out
/C1.DeltaP = 0 kPa
/C1.Out.T = -20 C
/S2 = Stream.Stream_Material()
/S2.In -> /C1.Out
/V1 = Flash.SimpleFlash("LiquidPhases = 1")
/V1.In -> /S2.Out
/Gas = Stream.Stream_Material()
/Gas.In -> /V1.Vap
/L1 = Stream.Stream_Material()
/L1.In -> /V1.Liq0
/SP1 = Split.Splitter("NumberStreamsOut = 2")
/SP1.In -> /L1.Out
/SP1.FlowFraction1 = 0.3
/Prod = Stream.Stream_Material()
/Prod.In -> /SP1.Out0
/Rec = Stream.Stream_Material()
/Rec.In -> /SP1.Out1
/Rec.Out -> /M1.In1
# начальные оценки рецикла
/Rec.In.T ~= -20 C
/Rec.In.P ~= 3000 kPa
/Rec.In.MoleFlow ~= 20
/Rec.In.Fraction ~= 0.1 0.2 0.3 0.25 0.15
go
/Rec.Out.MoleFlow
/Gas.Out.MoleFlow
/Prod.Out.MoleFlow
