# Нагреватель -> дроссель -> двухфазный сепаратор (типовая цепочка).
units SI
hold
$RootThermo = VirtualMaterials.Advanced_Peng-Robinson
/ -> $RootThermo
$RootThermo + METHANE ETHANE PROPANE n-BUTANE n-PENTANE n-HEXANE WATER
go
/Feed = Stream.Stream_Material()
/Feed.In.T = 15 C
/Feed.In.P = 6000 kPa
/Feed.In.MoleFlow = 500 kmol/h
/Feed.In.Fraction = 0.65 0.10 0.08 0.06 0.04 0.04 0.03
# нагреватель: вход соединяем с выходом потока, задаём dP и T на выходе
/H1 = Heater.Heater("NumberSegments = 1; DeltaP.DP = None")
/H1.In -> /Feed.Out
/H1.DeltaP = 50 kPa
/H1.Out.T = 40 C
/Q1 = Stream.Stream_Energy()
/Q1.Out -> /H1.InQ
/S2 = Stream.Stream_Material()
/S2.In -> /H1.Out
# дроссель: задаём давление на выходе
/V1 = Valve.Valve()
/V1.In -> /S2.Out
/V1.Out.P = 2500 kPa
/S3 = Stream.Stream_Material()
/S3.In -> /V1.Out
# сепаратор (газ / одна жидкость)
/Sep = Flash.SimpleFlash("LiquidPhases = 1")
/Sep.In -> /S3.Out
/Gas = Stream.Stream_Material()
/Gas.In -> /Sep.Vap
/Liq = Stream.Stream_Material()
/Liq.In -> /Sep.Liq0
/Q1.Out.Energy
/S3.Out.VapFrac
