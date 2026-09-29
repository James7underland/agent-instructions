# Однократное испарение (flash) газоконденсатной смеси и свойства потока.
# Запуск: python scripts/sym.py run examples/01_flash.tst --streams
units SI
hold
$RootThermo = VirtualMaterials.Advanced_Peng-Robinson
/ -> $RootThermo
$RootThermo + METHANE ETHANE PROPANE n-BUTANE n-PENTANE n-HEXANE
go
/Feed = Stream.Stream_Material()
/Feed.In.T = -10 C
/Feed.In.P = 4000 kPa
/Feed.In.MoleFlow = 1000 kmol/h
/Feed.In.Fraction = 0.70 0.12 0.08 0.05 0.03 0.02
# запросы (печатают ответ движка):
/Feed.Out.VapFrac
/Feed.Out
