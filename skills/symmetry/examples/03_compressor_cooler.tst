# Компрессор (адиабатный КПД) + аппарат охлаждения + насос для жидкости.
units SI
hold
$RootThermo = VirtualMaterials.Advanced_Peng-Robinson
/ -> $RootThermo
$RootThermo + METHANE ETHANE PROPANE n-BUTANE WATER
go
/Gas = Stream.Stream_Material()
/Gas.In.T = 30 C
/Gas.In.P = 500 kPa
/Gas.In.MoleFlow = 300 kmol/h
/Gas.In.Fraction = 0.85 0.08 0.04 0.03 0
/K1 = Compressor.CompressorWithCurve("IgnoreCurve = 1; AdiabaticEff = None")
/K1.In -> /Gas.Out
/K1.Out.P = 2000 kPa
/K1.AdiabaticEff = 0.75
/W1 = Stream.Stream_Energy()
/W1.Out -> /K1.InQ
/S2 = Stream.Stream_Material()
/S2.In -> /K1.Out
/C1 = Heater.Cooler("NumberSegments = 1; DeltaP.DP = None")
/C1.In -> /S2.Out
/C1.DeltaP = 30 kPa
/C1.Out.T = 40 C
/QC = Stream.Stream_Energy()
/QC.In -> /C1.OutQ
/S3 = Stream.Stream_Material()
/S3.In -> /C1.Out
# насос для воды
/Wat = Stream.Stream_Material()
/Wat.In.T = 25 C
/Wat.In.P = 101.325 kPa
/Wat.In.MassFlow = 10000 kg/h
/Wat.In.Fraction = 0 0 0 0 1
/P1 = Pump.PumpWithCurve("IgnoreCurve = 1; Efficiency = None")
/P1.In -> /Wat.Out
/P1.Out.P = 1000 kPa
/P1.Efficiency = 0.7
/WP = Stream.Stream_Energy()
/WP.Out -> /P1.InQ
/Wat2 = Stream.Stream_Material()
/Wat2.In -> /P1.Out
/W1.Out.Energy
/K1.PolytropicEff
/QC.Out.Energy
/WP.Out.Energy
