# Оптимизатор (Tools → Optimizer; объект CaseStudy.CaseStudy в /..CaseOptimizerManager, решатель IPOPT):
# максимизировать выход газа 3-фазного сепаратора температурой сырья 0–80 °C при плотности нефти ≥ 660 кг/м³.
# Ответ: T = 50,67 °C, газ 158,48 кмоль/ч, ρ = 660,0 (на границе). Результат — в IndVariable_0.ValForBestVal,
# в схему НЕ переносится: применить вручную "/Feed.In.T = 50.67 C".
# Ограничения по составу (CstCustomVariables + CompositionVariable) регистрируются, но границы не соблюдаются.
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
/..CaseOptimizerManager.Optimizer1 = CaseStudy.CaseStudy()
/..CaseOptimizerManager.Optimizer1.IndVariables + /Feed.In.T
/..CaseOptimizerManager.Optimizer1.IndVariable_0.MinValue = 0 C
/..CaseOptimizerManager.Optimizer1.IndVariable_0.MaxValue = 80 C
/..CaseOptimizerManager.Optimizer1.DepVariables + /Gas.In.MoleFlow
/..CaseOptimizerManager.Optimizer1.DepVariable_0.ObjFnMode = Maximize
/..CaseOptimizerManager.Optimizer1.CstVariables + /Oil.In.MassDensity
/..CaseOptimizerManager.Optimizer1.CstVariable_0.MinValue = 660 kg/m3
/..CaseOptimizerManager.Optimizer1.CstVariable_0.MaxValue = 1000 kg/m3
/..CaseOptimizerManager.Optimizer1.SetRegressedValuesAsSpecs = 1
/..CaseOptimizerManager.Optimizer1.Run = 1
/..CaseOptimizerManager.Optimizer1.IndVariable_0.ValForBestVal
/..CaseOptimizerManager.Optimizer1.DepVariable_0.OptimizerValue
/..CaseOptimizerManager.Optimizer1.CstVariable_0.ValForBestVal
