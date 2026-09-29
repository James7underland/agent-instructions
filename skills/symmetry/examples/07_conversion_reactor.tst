# Конверсионный реактор: горение метана CH4 + 2 O2 -> CO2 + 2 H2O, конверсия 95 %, адиабатный (OutQ = 0).
units SI
hold
$RootThermo = VirtualMaterials.Advanced_Peng-Robinson
/ -> $RootThermo
$RootThermo + METHANE OXYGEN NITROGEN CARBON_DIOXIDE WATER
go
/Feed = Stream.Stream_Material()
/Feed.In.T = 25 C
/Feed.In.P = 200 kPa
/Feed.In.MoleFlow = 100 kmol/h
/Feed.In.Fraction = 0.08 0.19 0.73 0 0
/R1 = ConvRxn.ConvReactor("SimultaneousRxn = 0")
/R1.In -> /Feed.Out
/R1.NumberRxn = 1
# Formula = Имя:коэф*индекс ... ; индекс = номер компонента в $RootThermo с 0 (METHANE=0, OXYGEN=1, N2=2, CO2=3, H2O=4)
# продукты со знаком +, реагенты со знаком -, '!' — базовый компонент (к нему относится конверсия), коэф. 1 можно опустить
/R1.Rxn0.Formula = Combustion:3+2*4-!0-2*1
/R1.Rxn0.Conversion = 0.95
/R1.Rxn0.RxnOrder = 0
/R1.DeltaP = 0 kPa
/R1.OutQ = 0 W
/Prod = Stream.Stream_Material()
/Prod.In -> /R1.Out
/R1.Out.T
/R1.Rxn0_Conversion
