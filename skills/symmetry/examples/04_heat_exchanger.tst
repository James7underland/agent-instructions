# Кожухотрубчатый теплообменник HeatExchangerUA: горячая нефть в трубах, холодная вода в межтрубье.
units SI
hold
$RootThermo = VirtualMaterials.Advanced_Peng-Robinson
/ -> $RootThermo
$RootThermo + n-HEPTANE n-DECANE WATER
go
/Hot = Stream.Stream_Material()
/Hot.In.T = 150 C
/Hot.In.P = 800 kPa
/Hot.In.MassFlow = 20000 kg/h
/Hot.In.Fraction = 0.5 0.5 0
/Cold = Stream.Stream_Material()
/Cold.In.T = 20 C
/Cold.In.P = 400 kPa
/Cold.In.MassFlow = 15000 kg/h
/Cold.In.Fraction = 0 0 1
/E1 = Heater.HeatExchangerUA("NumberSegments = 5; AppT = Heater.TemperatureApproachVar(0,1) ; Q0 = Heater.EnergySideVar(0,1); DeltaP0.DP = None; DeltaP1.DP = None")
/E1.InTube -> /Hot.Out
/E1.InShell -> /Cold.Out
/E1.DeltaP0 = 30 kPa
/E1.DeltaP1 = 20 kPa
# одна спецификация теплообмена: T горячего на выходе (можно вместо неё UA или Q)
/E1.OutTube.T = 70 C
/HotOut = Stream.Stream_Material()
/HotOut.In -> /E1.OutTube
/ColdOut = Stream.Stream_Material()
/ColdOut.In -> /E1.OutShell
/E1.UA
/E1.Q0
/E1
