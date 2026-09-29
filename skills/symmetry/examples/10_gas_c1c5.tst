# Газ C1–nC5 для props.py: envelope examples/10_gas_c1c5.tst /G out.png
units SI
$RootThermo = VirtualMaterials.Advanced_Peng-Robinson
/ -> $RootThermo
$RootThermo + METHANE ETHANE PROPANE n-BUTANE n-PENTANE
/G = Stream.Stream_Material()
/G.In.T = 20 C
/G.In.P = 5000 kPa
/G.In.MoleFlow = 100
/G.In.Fraction = 0.8 0.08 0.06 0.04 0.02
