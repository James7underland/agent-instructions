# Каталог unit operations Symmetry 2023.2 (снят движком)

Источник: `UI64\Symmetry.ini [UnitOperation]` (конструкторы с настройками GUI по умолчанию). Для каждой операции создан объект `/X = <конструктор>` и сняты `/X` и `dir /X` — полный вывод: `unitops/<Имя>.txt`.
M — материальные порты, E — энергетические, S — число сигнальных портов (задаваемые/расчётные величины, напр. DeltaP, OutT), P — число параметров (Param). Имена портов используются в командах `/X.In -> /S1.Out`.

## Основные

| Имя | Конструктор | M | E | S | P |
|---|---|---|---|---|---|
| Flowsheet | `Flowsheet.Flowsheet()` |  |  | 3 | 25 |
| SubFlowsheet | `Flowsheet.SubFlowsheet()` |  |  | 3 | 15 |
| Stream_Material | `Stream.Stream_Material()` | In Out |  | 0 | 9 |
| Stream_Energy | `Stream.Stream_Energy()` |  | In Out | 0 | 1 |
| Stream_Signal | `Stream.Stream_Signal()` |  |  | 2 | 1 |
| BalanceOp | `Balance.BalanceOp("BalanceType = 2; NumberStreamsInMat = 1; NumberStreamsOutMat = 1; Nu...` | In0 Out0 |  | 0 | 7 |
| Compressor | `Compressor.CompressorWithCurve("IgnoreCurve = 1; AdiabaticEff = None")` | In Out | InQ | 58 | 26 |
| Controller | `Controller.Controller()` |  |  | 62 | 33 |
| SurgeController | `Controller.SurgeController()` |  |  | 29 | 17 |
| CrossConnector | `CrossConnector.CrossConnector()` | In Out |  | 0 | 9 |
| ExcelUnitOp | `ComUnitOp.COMUnitOperation( ,VirtualMaterials.Sim.ExcelUnitOp.ExcelUnitOperation)` |  |  | 0 | 2 |
| Expander | `Compressor.ExpanderWithCurve("IgnoreCurve = 1; AdiabaticEff = None")` | In Out | OutQ | 53 | 20 |
| ElectricMotor | `ElectricMotor.ElectricMotor()` |  |  | 22 | 3 |
| Mixer | `Mixer.Mixer("NumberStreamsIn = 2")` | In0 In1 Out |  | 8 | 11 |
| PipeSegment | `PipeSegment.PipeSegment("PressureDropModel = ; PressureDropModel = PipeModels.VMGPressu...` | In Out | OutQ | 16 | 34 |
| Pump | `Pump.PumpWithCurve("IgnoreCurve = 1; Efficiency = None")` | In Out | InQ | 51 | 23 |
| SaturationOp | `Saturation.SaturationOp()` | MainFeed SaturateWith Saturated | OutQ | 1 | 10 |
| Set | `Set.Set()` |  |  | 4 | 2 |
| SelectorBlock | `SelectorBlock.SelectorBlock()` |  |  | 30 | 6 |
| Splitter | `Split.Splitter("NumberStreamsOut = 2")` | In Out0 Out1 |  | 10 | 8 |
| Valve | `Valve.Valve()` | In Out |  | 32 | 27 |
| ProTreat | `OGT.ProTreat()` |  |  | 0 | 1 |
| MembraneOp | `MembraneBase.MembraneOp()` | Feed Retentate Permeate | InQ | 10 | 21 |
| Source | `Node.Source()` | Source |  | 0 | 2 |
| Sink | `Node.Sink()` | Sink |  | 0 | 1 |
| Node | `Node.Node()` |  |  | 0 | 7 |
| Desalter | `Dehydrator.Desalter()` | OilIn WaterIn OilOut BrineOut | InQ | 5 | 4 |
| FractionationUnit | `Plants.FractionationUnit()` | In0 TopVap BtmLiq |  | 0 | 3 |
| TurboPlant | `Plants.TurboPlant()` | Feed GasProd LiqProd |  | 0 | 2 |
| DehyPlant | `Plants.DehyPlant()` | Feed Makeup GasProd Water |  | 0 | 2 |
| AminePlant | `Plants.AminePlant()` | Feed Makeup GasProd GasAcid |  | 0 | 2 |
| SulfurRecoveryUnit | `Plants.SulfurRecoveryUnit()` | Feed Fuel Air GasProd SulfurProd |  | 0 | 1 |
| OLGALink | `OLGALink.OLGALink()` |  |  | 0 | 1 |
| PIPESIMLink | `PIPESIMLink.PIPESIMLink()` |  |  | 0 | 1 |
| RemoteConnector | `RemoteConnector.RemoteConnector()` | Out |  | 0 | 1 |
| TOP_Prop | `Sensia.TOP_Prop()` | In_0 Conditioned_0 Out |  | 0 | 1 |

## ClausPlant

| Имя | Конструктор | M | E | S | P |
|---|---|---|---|---|---|
| ClausReactionFurnace | `ClausReactors.ClausReactionFurnace("DeltaP = 0.5 psi; OutQ = 0 Btu/hr; COS_Model = SRE-...` | In Out | OutQ | 17 | 46 |
| ClausWasteHeatBoiler | `ClausOperations.ClausWasteHeatBoiler("DeltaP = 1.0 psi")` | In Out | OutQ | 16 | 14 |
| ClausCondenser | `ClausOperations.ClausCondenser("DeltaP = 0.25 psi")` | In Vap Liq | OutQ | 24 | 3 |
| ClausConverter | `ClausReactors.ClausConverter("DeltaP = 0.25 psi; OutQ = 0 Btu/hr; NumberSegments = 5; C...` | In Out | OutQ | 31 | 40 |
| ClausOxidationConverter | `ClausReactors.ClausDirectOxidationConverter("DeltaP = 0.25 psi; OutQ = 0 Btu/hr; Number...` | In Out | OutQ | 29 | 35 |
| ClausHeater | `ClausOperations.ClausHeater("DeltaP = 0.25 psi")` | In Out | InQ | 13 | 14 |
| ClausDirectFiredReheater | `ClausReactors.ClausDirectFiredReheater("DeltaP = 0.25 psi; OutQ = 0 Btu/hr")` | Process Fuel Air Out | OutQ Burner_OutQ | 12 | 10 |
| ClausSulfurPit | `ClausOperations.ClausSulfurPit("DeltaP = 0 psi; OutQ = 0 Btu/hr;")` | SweepGas In0 In1 In2 In3 Vap Liq | OutQ | 27 | 15 |
| ClausOxygenCalculator | `ClausOperations.ClausOxygenCalculator()` | AcidGasIn AirIn AcidGasOut AirOut |  | 4 | 10 |
| ClausSulfurDetail | `ClausOperations.ClausSulfurDetail()` | In Out |  | 16 | 2 |
| ClausHydrogenator | `ClausReactors.ClausHydrogenator("DeltaP = 0.25 psi; OutQ = 0 Btu/hr")` | In Out | OutQ | 21 | 39 |
| ClausReducingGasGenerator | `ClausReactors.ClausReducingGasGenerator("DeltaP = 0.25 psi; OutQ = 0 Btu/hr")` | Process Fuel Air Out | OutQ Burner_OutQ | 12 | 10 |
| ClausCooler | `ClausOperations.ClausCooler("DeltaP = 0.25 psi")` | In Out | OutQ | 13 | 14 |
| ClausMixer | `ClausOperations.ClausMixer()` | In0 In1 Out |  | 3 | 11 |

## Heating/Cooling

| Имя | Конструктор | M | E | S | P |
|---|---|---|---|---|---|
| AirCooler | `DetailedCoolers.DetailedAirCooler()` | In Out | QFan OutQ | 70 | 25 |
| Cooler | `Heater.Cooler("NumberSegments = 5; DeltaP.DP = None")` | In Out | OutQ | 14 | 11 |
| Heater | `Heater.Heater("NumberSegments = 5; DeltaP.DP = None")` | In Out | InQ | 14 | 11 |
| HeatExchanger | `Heater.HeatExchangerUA("NumberSegments = 5; AppT = Heater.TemperatureApproachVar(0,1) ;...` | InTube InShell OutTube OutShell |  | 96 | 74 |
| MultiSidedHeatExchanger | `Heater.MultiSidedHeatExchangerOp("NumberSegments = 5; DeltaP0.DP = None; DeltaP1.DP = N...` | In0 In1 Out0 Out1 |  | 14 | 33 |

## Oil Data Regressions

| Имя | Конструктор | M | E | S | P |
|---|---|---|---|---|---|
| OilProp | `Oil.OilMixProps()` |  |  | 0 | 1 |
| OilSource | `Oil.PIONAFeed("DistCrvCalcMode = Direct")` | In Out |  | 171 | 94 |

## FiredEquipment

| Имя | Конструктор | M | E | S | P |
|---|---|---|---|---|---|
| FiredHeater | `EthyleneCracker.FiredHeater()` | In FuelIn OxidantIn Out FlueGasOut | Rad_AmbientHeatLoss Conv_AmbientHeatLoss | 109 | 62 |
| BathHeater | `EthyleneCracker.BathHeater()` | In FuelIn OxidantIn Out FlueGasOut | AmbientHeatLoss | 15 | 51 |
| Burner | `EthyleneCracker.Burner()` | FuelIn OxidantIn FlueGasOut | HeatLoss | 0 | 3 |
| Boiler | `Boiler.Boiler()` | Fuel Air BFW Flue SteamOut Blowdown | HeatingDuty | 3 | 7 |

## Reactor

| Имя | Конструктор | M | E | S | P |
|---|---|---|---|---|---|
| CCR | `Reactors.CCR()` | FeedIn CatalystIn FurnaceIn ProductOut CatalystOut FurnaceOut | AmbientHeatLoss | 66 | 35 |
| ConvReactor | `ConvRxn.ConvReactor("SimultaneousRxn = 0")` | In Out | OutQ | 22 | 20 |
| CSTR | `KineticReactor.CSTR()` | In Out | OutQ | 22 | 27 |
| DelayedCoker | `Reactors.DelayedCoker()` | FeedIn SteamIn AccumIn VaporOut PitchOut AccumOut | AmbientHeatLoss | 61 | 29 |
| EqmReactor | `EquiliReactor.EquilibriumReactor("CalculationOption = 1")` | In Out | OutQ | 28 | 35 |
| FCC | `Reactors.FCC()` | FeedIn AddCatalystIn CombustionAirIn DispersionSteamIn StrippingSteamIn ProductOut WithdrawCatalystOut FlueGasOut | AmbientHeatLoss RegAmbientHeatLoss RegCoolerQ | 147 | 49 |
| Hydrocracker | `Reactors.Hydrocracker()` | FeedIn CatalystIn HydrogenIn WashWaterIn ProductOut CatalystOut SourWaterOut AcidGasOut OffgasOut | RecCompQ RecPreheatQ AmbientHeatLoss RecCompCoolerQ RecLPSepCoolerQ RecHPSepCoolerQ | 78 | 48 |
| Hydrotreater | `Hydrotreater.Hydrotreater()` | CrudeIn HydrogenIn ProductOut AccumulationOut | AmbientHeatLoss | 114 | 49 |
| PFR | `KineticReactor.PFR("NumberSections = 10; Roughness = 0.045 mm")` | In Out | OutQ | 19 | 27 |
| PlasmaGasification | `Gasification.PlasmaGasificationOp()` | TorchAirIn FluxIn SteamIn OxidantIn CokeIn FeedIn RawGasOut SlagOut LiquidMetalOut ParticulatesOut | PlasmaDuty FreeboardHeatLoss BedHeatLoss | 127 | 15 |
| FTR | `Reactors.FTR()` | MainFeedIn RecycleIn CoolingIn WaxOut LiquidOut VaporOut CoolingOut | AmbientHeatLoss | 39 | 18 |
| FTRRating | `Reactors.FTRRating()` | MainFeedIn RecycleIn CoolingIn WaxOut LiquidOut VaporOut CoolingOut | AmbientHeatLoss | 85 | 18 |
| FuelCell | `VCM.FuelCell()` | In UtilityIn Out UtilityOut | AmbientHeatLoss VoltageDC | 113 | 29 |
| Electrolyzer | `Electrolyzer.Electrolyzer()` | In UtilityIn Out UtilityOut | TotalPower AmbientHeatLoss FurnaceHeat VoltageDC | 3 | 6 |
| EthyleneCracker | `EthyleneCracker.EthyleneCracker()` | In FurnaceIn Out FurnaceOut | AmbientHeatLoss | 233 | 51 |
| QuenchBoiler | `EthyleneCracker.QuenchBoiler()` | ProcessIn UtilityIn ProcessOut UtilityOut | AmbientHeatLoss | 73 | 45 |
| VCM | `VCM.VCM()` | In UtilityIn Out UtilityOut | AmbientHeatLoss | 70 | 23 |
| Visbreaker | `Reactors.Visbreaker()` | In Out | QIn QLoss | 65 | 47 |
| Isomerization | `Reactors.Isomerization()` | FeedIn CatalystIn ProductOut CatalystOut | AmbientHeatLoss | 76 | 43 |

## Separator

| Имя | Конструктор | M | E | S | P |
|---|---|---|---|---|---|
| MultifeedSep2 | `MultifeedSeparator.MultifeedSep2()` | In0 Vap Liq0 | InQ | 28 | 18 |
| MultifeedSep3 | `MultifeedSeparator.MultifeedSep3("KeyCmp_Liq1 = WATER 0.5")` | In0 Vap Liq0 Liq1 | InQ | 28 | 18 |
| Separator | `Flash.SimpleFlash("LiquidPhases = 1;KeyCmp_Liq1 = WATER 0.5")` | In Vap Liq0 |  | 27 | 16 |
| SeparatorLLV | `VMGSim.ThreePhaseSeparator("KeyCmp_Liq1 = WATER 0.5")` | In Vap Liq0 Liq1 |  | 27 | 16 |
| Recombination | `Recombination.RecombinationOp()` | Gas Condensate Water |  | 0 | 1 |
| DirectColumn | `DirectSeparator.DirectSeparator()` | In0 Out0 Out1 Out2 Out3 Out4 Out5 Out6 Out_Decant | InQ0 | 0 | 17 |
| ComponentSplitter | `ComponentSplitter.ComponentSplitter(DefaultSplit = 1.0)` | In0 Out0 Out1 | InQ0 | 13 | 9 |
| Adsorber | `PSA.AdsorptionSplitter()` | In Out Accumulation | QLoss | 1 | 3 |

## Solids

| Имя | Конструктор | M | E | S | P |
|---|---|---|---|---|---|
| Cyclone | `Solids.Cyclone()` | Feed Gas Solids | OutQ | 11 | 3 |
| ElectrostaticPrecipitator | `Solids.ElectrostaticPrecip()` | Feed Gas Solids | OutQ | 5 | 4 |
| RotaryDryer | `Solids.Dryer()` | SolidIn GasIn SolidOut GasOut | OutQ | 4 | 3 |

## Specialty

| Имя | Конструктор | M | E | S | P |
|---|---|---|---|---|---|
| Ejector | `Ejector.EjectorOp()` | Process Motive Discharge |  | 3 | 12 |
| GasOrificeMeter | `OrificeMetering.GasOrifice()` | In Out |  | 7 | 16 |
| HoneyCombeDehumidifier | `Desiccant.DehumidifierInterface()` |  |  | 0 | 0 ⚠ No valid license for unit operation 'Desiccant.DehumidifierInterface()' |
| Psychrometric | `Saturation.PsychrometricOp()` | DryAir Water SaturatedAir ProcessAir |  | 6 | 3 |
| ReliefValve | `Valve.ReliefValve()` | In Out |  | 24 | 22 |
| RuptureDisk | `Valve.RuptureDisk()` | In Out |  | 24 | 22 |
| UtilityHV | `Tank.Tank()` | In0 Vap Liq0 Liq1 | InQ | 3 | 5 |

## Tool/Property

| Имя | Конструктор | M | E | S | P |
|---|---|---|---|---|---|
| AmineDetail | `AmineOperations.AmineDetail()` | In Out |  | 15 | 17 |
| DistCurve | `Properties.VectorProps("BoilingCurve_TBP_Active = 1")` | In Out |  | 0 | 18 |
| Envelope | `Envelope.PTEnvelope("InitPressures = 1000 2000 3000 4000 5000 6000 7000 8000 9000 10000...` | In Out |  | 11 | 16 |
| GibbsCurve | `Envelope.GibbsCurve()` | In Out |  | 0 | 11 |
| Hydrate | `HydrateThermoBased.Hydrate()` | In Out |  | 7 | 17 |
| OverallBalance | `OverallBalance.OverallBalance("BalanceType = Energy+Mass+Mole")` |  |  | 0 | 12 |
| PropertyTable | `Properties.PropertyTable()` | In Out |  | 4 | 17 |
| SpecialProp | `Properties.SpecialProps()` | In Out |  | 1 | 140 |
| WaterDewPoint | `WaterDewPoint.WaterDewPoint("StartingT = 260.0 K; StepT = 20.0 K")` | In Out |  | 4 | 4 |
| XYCurve | `Envelope.XYCurve()` | In Out |  | 0 | 15 |
| Scheduler | `Scheduler.SchedOp()` |  |  | 0 | 1 |
| ProcessCalculator | `ProCalc.ProCalcOp()` |  |  | 0 | 2 |
| PropertyRecon | `DataRecon.PropertyRecon()` | In Out |  | 11 | 1 |
| TOP | `Sensia.TOP_Prop()` | In_0 Conditioned_0 Out |  | 0 | 1 |
| OPCClient | `OPCClient.OPCClientOp()` |  |  | 0 | 1 |
| PinchUtility | `CompositeCurve.PinchUtility()` |  |  | 13 | 10 |
| CauseEffect | `CauseEffect.CauseEffectOp()` |  |  | 9 | 2 |
| Makeup | `Makeup.Makeup()` | In Makeup Out Blowdown | OutQ | 5 | 8 |
| PVTAnalysis | `Oils.PVTAnalysis()` | In Out |  | 0 | 1 |
| CnAnalysis | `Oil.CnAnalysis("CnAnalysisCalc.CalcMode = Distillation Curve")` | In Out |  | 0 | 1 |
| OilAnalysis | `Oil.OilAnalysis()` | In Out |  | 0 | 1 |
| ConfinedPVT | `Oil.ConfinedPVT()` | In Out |  | 0 | 1 |
| DigitalLogic | `DigitalLogic.DigitalLogic()` |  |  | 0 | 2 |
| PipeLeakLocator | `PipeSegment.PipeLeakLocator()` |  |  | 0 | 2 |
| DataFilter | `DataFilter.DataFilter()` |  |  | 0 | 2 |

## Tower

| Имя | Конструктор | M | E | S | P |
|---|---|---|---|---|---|
| DistillationColumn | `Tower.DistillationColumn("Stage_0.dsc = Tower.DegSubCooling(); Stage_0.dsc.Port = 0.0; ...` | Feed_1_feed VapourDraw_0_condenserV LiquidDraw_0_condenserL LiquidDraw_2_reboilerL | EnergyFeed_2_reboilerQ EnergyFeed_0_condenserQ | 2 | 44 |
| RefluxedAbsorber | `Tower.RefluxedAbsorber("Stage_0.dsc = Tower.DegSubCooling(); Stage_0.dsc.Port = 0.0; In...` | Feed_1_bottomFeed VapourDraw_0_condenserV LiquidDraw_0_condenserL LiquidDraw_1_bottomL | EnergyFeed_0_condenserQ | 2 | 44 |
| ReboiledAbsorber | `Tower.ReboiledAbsorber("Stage_0.dsc = Tower.DegSubCooling(); Stage_0.dsc.Port = 0.0; In...` | Feed_0_overheadFeed VapourDraw_0_overheadV LiquidDraw_1_reboilerL | EnergyFeed_1_reboilerQ | 1 | 42 |
| Absorber | `Tower.Absorber("Stage_0.dsc = Tower.DegSubCooling(); Stage_0.dsc.Port = 0.0; InitTowerA...` | Feed_0_overheadFeed Feed_1_bottomFeed VapourDraw_0_overheadV LiquidDraw_1_bottomL |  | 1 | 42 |
| DistSection | `TowerStages.DistillationSection("Stage_0.dsc = Tower.DegSubCooling(); Stage_0.dsc.Port ...` | Feed_0_Ovhd Feed_1_Bottom VapourDraw_0_OvhdV LiquidDraw_1_BottomL |  | 1 | 33 |
| LiqLiqExtractor | `LiqLiqExt.LiqLiqEx("NumberStages = 5")` | Feed Solvent Extract Raffinate |  | 0 | 24 |

## UreaPlant

| Имя | Конструктор | M | E | S | P |
|---|---|---|---|---|---|
| UreaReactor | `VCM.UreaReactor()` | Feed Product Vent | AmbientHeatLoss | 44 | 16 |
| UreaCondenser | `VCM.UreaCondenser()` | Feed1 Feed2 UtilityIn LiquidOut VaporOut UtilityOut | AmbientHeatLoss | 55 | 19 |
| UreaStripper | `VCM.UreaStripper()` | LiquidFeed GasFeed UtilityIn Product StripGas UtilityOut | AmbientHeatLoss | 54 | 19 |
| UreaScrubber | `VCM.UreaScrubber()` | LiquidFeed GasFeed UtilityIn Product Vent UtilityOut | AmbientHeatLoss | 55 | 19 |
