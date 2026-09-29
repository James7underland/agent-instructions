# Ректификационная колонна (депропанизатор): 20 теоретических ступеней (0 = конденсатор, 19 = куб),
# питание на 10-ю, полный конденсатор, флегмовое число 2.5, отбор дистиллята задан расходом.
units SI
hold
$RootThermo = VirtualMaterials.Advanced_Peng-Robinson
/ -> $RootThermo
$RootThermo + ETHANE PROPANE i-BUTANE n-BUTANE n-PENTANE
go
/Feed = Stream.Stream_Material()
/Feed.In.T = 50 C
/Feed.In.P = 1700 kPa
/Feed.In.MoleFlow = 100 kmol/h
/Feed.In.Fraction = 0.02 0.38 0.15 0.25 0.20
/T1 = Tower.DistillationColumn("Stage_0.dsc = Tower.DegSubCooling(); Stage_0.dsc.Port = 0.0; InitTowerAlgorithm = ; InitTowerAlgorithm = TowerModels.VMGInitTower(); Stage_0 + 0")
hold
# 'Stage_0 + N' даёт N+3 ступени: Stage_0 (конденсатор) .. Stage_N+2 (куб); питание по умолчанию на Stage_N+1
/T1.Stage_0 + 17
go
# после добавления ступеней вход питания по умолчанию висит на последней ступени — переносим на 10-ю
/T1.Stage_18.feed.ParentStage = 10
/T1.Feed_10_feed -> /Feed.Out
hold
/T1.Stage_0.TopReflux = Tower.RefluxRatioSpec()
/T1.Stage_0.TopReflux.Port = 2.5
/T1.Stage_0.condenserL.Port.MoleFlow = 40
/T1.Stage_0.condenserV.Port.MoleFlow = 0
/T1.P_Profile.Item0 = 1600 kPa
/T1.P_Profile.Item19 = 1650 kPa
# без этого колонна не пытается сходиться (Status: Not Converged)
/T1.TryToSolve = 1
go
/Dist = Stream.Stream_Material()
/Dist.In -> /T1.LiquidDraw_0_condenserL
/Bott = Stream.Stream_Material()
/Bott.In -> /T1.LiquidDraw_19_reboilerL
/T1.EnergyFeed_0_condenserQ
/T1.EnergyFeed_19_reboilerQ
/T1.Variable_0_Reflux
