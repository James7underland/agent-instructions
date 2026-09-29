# Стационарная подгонка (Adjust) регулятором: подобрать T сырья трёхфазного сепаратора, чтобы нефть = 84 кмоль/ч.
# Ответ: T ≈ 38,75 °C. Ключевое — начальное значение ВЫХОДА регулятора (/ADJ.Out = 30 C), Minimum/Maximum/StepSize.
# Трёхфазный сепаратор: газ / углеводородная жидкость / вода (метан + н-гексан + н-декан + вода).
units SI
hold
$RootThermo = VirtualMaterials.APRNGL2
/ -> $RootThermo
$RootThermo + METHANE n-HEXANE n-DECANE WATER
go
/Feed = Stream.Stream_Material()
/Feed.In.T = 30 C
/Feed.In.P = 3000 kPa
/Feed.In.MoleFlow = 300 kmol/h
/Feed.In.Fraction = 0.55 0.15 0.1 0.2
/V3 = VMGSim.ThreePhaseSeparator("KeyCmp_Liq1 = WATER 0.5")
/V3.In -> /Feed.Out
/Gas = Stream.Stream_Material()
/Gas.In -> /V3.Vap
/Oil = Stream.Stream_Material()
/Oil.In -> /V3.Liq0
/Water = Stream.Stream_Material()
/Water.In -> /V3.Liq1
/Feed.In.T =
/ADJ = Controller.Controller()
/ADJ.In ->> /Oil.In.MoleFlow
/ADJ.Out ->> /Feed.In.T
/ADJ.Target = 84 kmol/h
/ADJ.Minimum = 0 C
/ADJ.Maximum = 100 C
/ADJ.StepSize = 10 C
/ADJ.Out = 30 C
/Feed.Out.T
/Oil.Out.MoleFlow
