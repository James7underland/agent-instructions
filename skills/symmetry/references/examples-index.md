# Примеры Symmetry (296 кейсов из Documentation)

Корень: `C:\Program Files\VMG\Symmetry\Documentation\` (+ путь ниже). **Не менять оригиналы** — копировать в рабочую папку.
Текст кейса (команды) виден без движка: `python scripts/vsym.py tst <файл.vsym>`. Колонка «Динамика» — есть ли в кейсе
сохранённая динамика (`DynamicsCase.s2m`/движок Dynamics). Unit ops — типы (без потоков), в скобках — количество.

Искать пример под задачу: `grep -i "Tower.Distillation" references/examples-index.md`.


## Manual Examples\Claus

| Файл | Динамика | Unit ops |
|---|---|---|
| ClausCondenser.vsym |  | ClausOperations.ClausCondenser |
| ClausConverter.vsym |  | ClausReactors.ClausConverter |
| ClausCooler.vsym |  | ClausOperations.ClausCooler |
| ClausDirectFiredHeater.vsym |  | ClausReactors.ClausDirectFiredReheater |
| ClausHeater.vsym |  | ClausOperations.ClausHeater |
| ClausHydrogenator.vsym |  | ClausReactors.ClausHydrogenator |
| ClausMixer.vsym |  | ClausOperations.ClausMixer |
| ClausOxidationConverter.vsym |  | ClausReactors.ClausDirectOxidationConverter |
| ClausOxygenCalculator.vsym |  | ClausOperations.ClausOxygenCalculator |
| ClausReactionFurnace.vsym |  | ClausReactors.ClausReactionFurnace |
| ClausReducingGasGenerator.vsym |  | ClausReactors.ClausReducingGasGenerator |
| ClausSulfurPit.vsym |  | ClausOperations.ClausCondenser(3), ClausOperations.ClausHeater(2), Controller.Controller(2), ClausReactors.ClausConverter(2), ClausReactors.ClausReactionFurnace, Heater.Heater, ClausOperations.ClausOxygenCalculator, Saturation.SaturationOp, Mixer.Mixer, ClausOperations.ClausWasteHeatBoiler |
| ClausWasteHeatBoiler.vsym |  | ClausOperations.ClausWasteHeatBoiler |
| Dynamics\Claus Condenser Dynamic.vsym |  | ClausOperations.ClausCondenser |
| Dynamics\Claus Converter Dynamic.vsym |  | ClausReactors.ClausConverter |
| Dynamics\Claus Cooler Dynamic.vsym |  | ClausOperations.ClausCooler |
| Dynamics\Claus Direct Fired Heater Dynamic.vsym |  | ClausReactors.ClausDirectFiredReheater |
| Dynamics\Claus Heater Dynamic.vsym |  | ClausOperations.ClausHeater |
| Dynamics\Claus Hydrogenator Dynamic.vsym |  | ClausReactors.ClausHydrogenator |
| Dynamics\Claus Mixer Dynamic.vsym |  | ClausOperations.ClausMixer |
| Dynamics\Claus Oxidation Converter Dynamic.vsym |  | ClausReactors.ClausDirectOxidationConverter |
| Dynamics\Claus Oxygen Calculator Dynamic.vsym |  | ClausOperations.ClausOxygenCalculator |
| Dynamics\Claus Reducing Gas Generator Dynamic.vsym |  | ClausReactors.ClausReducingGasGenerator |
| Dynamics\Claus Sulfur Pit Dynamic.vsym |  | ClausOperations.ClausCondenser(3), ClausOperations.ClausHeater(2), Controller.Controller(2), ClausReactors.ClausConverter(2), ClausReactors.ClausReactionFurnace, ClausOperations.ClausSulfurPit, Heater.Heater, ClausOperations.ClausOxygenCalculator, Saturation.SaturationOp, Mixer.Mixer, ClausOperation |
| Dynamics\Claus Waste Heat Boiler Dynamic.vsym |  | ClausOperations.ClausWasteHeatBoiler |
| Dynamics\Direct Oxidation Dynamic.vsym |  |  |
| GPSAClausPlantExample.vsym |  | ClausOperations.ClausCondenser(3), ClausOperations.ClausHeater(2), Controller.Controller(2), ClausReactors.ClausConverter(2), ClausReactors.ClausReactionFurnace, ClausOperations.ClausSulfurPit, Heater.Heater, ClausOperations.ClausOxygenCalculator, Saturation.SaturationOp, Mixer.Mixer, ClausOperation |
| Templates\DirectOxidation.vsym |  | ClausOperations.ClausCondenser(4), ClausOperations.ClausHeater(3), Controller.Controller(3), Mixer.Mixer(3), ClausReactors.ClausConverter(2), Saturation.SaturationOp(2), ClausReactors.ClausReactionFurnace, ClausOperations.ClausSulfurPit, ClausOperations.ClausSulfurDetail, ClausReactors.ClausDirectOx |
| Templates\TrimAirThreestage.vsym |  | ClausOperations.ClausCondenser(4), ClausOperations.ClausHeater(3), ClausReactors.ClausConverter(3), Controller.Controller(3), Mixer.Mixer(2), ClausReactors.ClausReactionFurnace, ClausOperations.ClausSulfurPit, ClausOperations.ClausSulfurDetail, Heater.Heater, ClausOperations.ClausOxygenCalculator, S |

## Manual Examples\Depressuring

| Файл | Динамика | Unit ops |
|---|---|---|
| Depressuring Example 1-1.vsym | да |  |
| Depressuring Example 1-2.vsym | да |  |
| Depressuring Example 1.vsym |  |  |
| Depressuring Example 2-1.vsym | да |  |
| Depressuring Example 2.vsym | да |  |
| Depressuring Example 3-1.vsym | да |  |
| Depressuring Example 3.vsym | да |  |
| Depressuring Example 4-1.vsym | да |  |
| Depressuring Example 4-2.vsym | да |  |
| Depressuring Example 4.vsym |  |  |
| Depressuring Example 5.vsym | да |  |
| Depressuring Example 6.vsym | да |  |
| Depressuring Example 7.vsym | да |  |
| Depressuring Example 8.vsym | да |  |
| Depressuring Example 9.vsym |  |  |
| Depressuring Example Input Fire.vsym |  |  |
| Depressuring Example N2 BlowDown.vsym |  |  |
| Depressuring Heat Loss U.vsym |  |  |

## Manual Examples\Economics

| Файл | Динамика | Unit ops |
|---|---|---|
| DpGasPlant(Econ).vsym |  |  |

## Manual Examples\Emissions

| Файл | Динамика | Unit ops |
|---|---|---|
| AP 42 Chapter 7 2019 case examples.vsym |  |  |
| AP 42 Chapter 7 2019 Example 1 Standalone.vsym |  |  |
| EmissionsFactorCalculationBoiler.vsym |  |  |
| EmissionsWithVMGSim.vsym |  |  |
| TankEmissions 2006.vsym |  | Flash.SimpleFlash(5), Oil.PIONAFeed |
| Utility Emissions.vsym |  |  |

## Manual Examples\Extensions and Links

| Файл | Динамика | Unit ops |
|---|---|---|
| Extension Unit Operation\Shortcut Distillation\ExtensionOperationExample_ShortcutDistillation.vsym |  | Distillation.ShortcutDist |
| MySep Link\MySep Link dynamics.vsym |  |  |
| MySep Link\MySep Link.vsym |  |  |
| OLGA Link\Tutorial 1\ModifyValve.vsym |  |  |
| OLGA Link\Tutorial 2\pig-comp.vsym | да |  |
| OLGA Link\Tutorial 2\pig-comp6.vsym |  |  |
| OLGA Link\Tutorial 3\SimpleProcess.vsym |  |  |
| OLGA Link\Tutorial 3\SimpleProcess_OLGA.vsym |  |  |
| OLGA Link\Tutorial 4\Tutorial 4.vsym |  |  |
| OLI Link\AcAcidTitration.vsym |  |  |
| OLI Link\BFW_Softening.vsym |  |  |
| OLI Link\Corrosion.vsym |  |  |
| PIPESIM Link\PIPLink Manual Example.vsym |  |  |
| PIPESIM Link\PIPLink Manual Example2.vsym |  |  |
| ProTreat\High Pressure MDEA Loop-Connected.vsym |  | OGT.ProTreat |

## Manual Examples\Flowsheet Tools

| Файл | Динамика | Unit ops |
|---|---|---|
| Information Operations\CarbonNumberAnalysis.vsym |  | Oil.PIONAFeed, Oil.CnAnalysis |
| Information Operations\Confined PVT Example.vsym |  |  |
| Information Operations\DistCurve.vsym |  | Properties.VectorProps |
| Information Operations\Envelope 3 Phase.vsym |  | Envelope.PTEnvelope |
| Information Operations\envelope.vsym |  | Envelope.PTEnvelope(3), Controller.Controller, Mixer.Mixer |
| Information Operations\GibbsCurve.vsym |  | Envelope.GibbsCurve |
| Information Operations\Hydrate.vsym |  |  |
| Information Operations\OilAnalysis.vsym |  | Oil.PIONAFeed, Oil.OilAnalysis |
| Information Operations\PropertyTable.vsym |  | Properties.PropertyTable |
| Information Operations\Psychrometric.vsym |  | Saturation.PsychrometricOp(2) |
| Information Operations\PXY.vsym |  | Envelope.XYCurve |
| Information Operations\SaturationOp Dynamic.vsym | да | Saturation.SaturationOp |
| Information Operations\SaturationOp.vsym |  | Saturation.SaturationOp |
| Information Operations\SelectorBlock.vsym |  | SelectorBlock.SelectorBlock |
| Information Operations\SelectorBlockDyn.vsym | да | SelectorBlock.SelectorBlock |
| Information Operations\SelectorBlockOnnxDynAirCoolerUA.vsym | да |  |
| Information Operations\SelectorBlockOnnxMultiply.vsym |  |  |
| Information Operations\SpecialProperties.vsym |  | Properties.SpecialProps(2) |
| Information Operations\TXY.vsym |  | Envelope.XYCurve |
| Information Operations\WaterDewPoint.vsym |  | WaterDewPoint.WaterDewPoint |
| Logical\BalanceOp.vsym |  | Balance.BalanceOp |
| Logical\Cause Effect 1.vsym | да | Valve.Valve, CauseEffect.CauseEffectOp, Pump.PumpWithCurve |
| Logical\Controller.vsym |  | Heater.Cooler, Controller.Controller, Flash.SimpleFlash |
| Logical\CrossConnector.vsym |  | Flowsheet.SubFlowsheet, Heater.Heater, CrossConnector.CrossConnector |
| Logical\DataFilter.vsym | да |  |
| Logical\Event Scheduler Example.vsym |  |  |
| Logical\ExcelUnitOp.vsym |  | Heater.Cooler, ComUnitOp.COMUnitOperation, Envelope.PTEnvelope |
| Logical\ProcCalc_Functions.vsym |  | ProCalc.ProCalcOp(2) |
| Logical\PropertyReconciliation.vsym |  |  |
| Logical\Set.vsym |  | Valve.Valve, Set.Set |

## Manual Examples\Flowsheeting Examples

| Файл | Динамика | Unit ops |
|---|---|---|
| AmmoniaRefrigeration.vsym |  | Compressor.CompressorWithCurve, Heater.Heater, Heater.Cooler, Valve.Valve |
| Atmospheric Crude Tower.vsym |  | MultifeedSeparator.MultifeedSep2, Tower.RefluxedAbsorber, Heater.Heater, Mixer.Mixer |
| DehydrationwithCoastalAGR.vsym |  | Flash.SimpleFlash(3), Valve.Valve(3), Mixer.Mixer(2), Tower.Absorber, Heater.Cooler, ComUnitOp.COMUnitOperation, Controller.Controller, Pump.PumpWithCurve |
| example1.vsym |  | Heater.Cooler |
| FlowSheeting.vsym |  | Flash.SimpleFlash(4), Heater.Cooler(3), Compressor.CompressorWithCurve(3), Mixer.Mixer(3) |
| GuntherRecycleMixer.vsym |  | Flash.SimpleFlash(4), Mixer.Mixer(3), Compressor.CompressorWithCurve(2), Valve.Valve(2), Heater.Cooler |
| GuntherRecycleStreams.vsym |  | Flash.SimpleFlash(4), Mixer.Mixer(3), Compressor.CompressorWithCurve(2), Valve.Valve(2), Heater.Cooler |
| Manual-Tutorial1.vsym |  | Heater.Heater(10), Set.Set(8), Pump.PumpWithCurve(5), Mixer.Mixer(5), Heater.HeatExchangerUA(4), Split.Splitter(3), Balance.BalanceOp(2), Tower.RefluxedAbsorber, Tower.Absorber, Properties.VectorProps, Tower.DistillationColumn, VMGSim.ThreePhaseSeparator |
| MDEAExample.vsym |  | Flash.SimpleFlash(2), AmineOperations.AmineDetail, Tower.DistillationColumn, Heater.HeatExchangerUA, Tower.Absorber, Heater.Cooler, Valve.Valve, ComUnitOp.COMUnitOperation, Controller.Controller, Mixer.Mixer, Pump.PumpWithCurve |
| MDEAExample_Makeup.vsym |  | Flash.SimpleFlash(2), AmineOperations.AmineDetail, Tower.DistillationColumn, Heater.HeatExchangerUA, Tower.Absorber, Heater.Cooler, Valve.Valve, Makeup.Makeup, Controller.Controller, Pump.PumpWithCurve |
| PEGDMELaureanceReid.vsym |  | Flash.SimpleFlash(8), Valve.Valve(5), Mixer.Mixer(5), Heater.Cooler(4), Split.Splitter(2), Tower.Absorber(2), ComponentSplitter.ComponentSplitter(2), Pump.PumpWithCurve(2), Tower.DistillationColumn, Heater.HeatExchangerUA, ComUnitOp.COMUnitOperation, Saturation.SaturationOp, Heater.Heater, Controlle |
| pikespeakManual.vsym |  | Flash.SimpleFlash(4), Mixer.Mixer(4), Pump.PumpWithCurve(4), Compressor.ExpanderWithCurve(3), Heater.Cooler(2), Compressor.CompressorWithCurve, Heater.HeatExchangerUA, Tower.Absorber, Valve.Valve, ComUnitOp.COMUnitOperation, Heater.Heater |
| RefrigerationBase.vsym |  |  |
| SimulatorBrand-H-ACT.vsym |  |  |
| TEGCase.vsym |  | Flash.SimpleFlash(2), Heater.HeatExchangerUA(2), Tower.DistillationColumn, Tower.Absorber, Valve.Valve, Mixer.Mixer, Pump.PumpWithCurve |
| TEGCase_Makeup.vsym |  | Flash.SimpleFlash(2), Heater.HeatExchangerUA(2), Tower.DistillationColumn, Tower.Absorber, Valve.Valve, Makeup.Makeup, Pump.PumpWithCurve |

## Manual Examples\Heat Exchange

| Файл | Динамика | Unit ops |
|---|---|---|
| ACDetailedGeometryCondenser.vsym |  | DetailedCoolers.DetailedAirCooler |
| AirCooler.vsym |  | DetailedCoolers.DetailedAirCooler |
| BoilerExample.vsym |  |  |
| Cooler.vsym |  | Heater.Cooler |
| FiredEquipment.vsym |  |  |
| Heater.vsym |  | Heater.Heater |
| HeatExchanger.vsym |  | Heater.HeatExchangerUA |
| HTRICase1a.vsym |  | Heater.HeatExchangerUA |
| HTRICase1b.vsym |  | Heater.HeatExchangerUA |
| HTRICase2.vsym |  | Heater.HeatExchangerUA(2) |
| HTRICase3.vsym |  | Pump.PumpWithCurve, Heater.HeatExchangerUA, Split.Splitter, Mixer.Mixer, Flash.SimpleFlash |
| HTRICaseAirCooler.vsym |  | DetailedCoolers.DetailedAirCooler |
| HTRIExample1.vsym |  | Heater.HeatExchangerUA(2) |
| Multisidedexchanger.vsym |  | Heater.MultiSidedHeatExchangerOp |
| MultisidedHeatExchangerHTRI.vsym |  | Heater.MultiSidedHeatExchangerOp |
| PinchUtility.vsym |  | Heater.Cooler(2), Heater.Heater(2), CompositeCurve.PinchUtility |
| VMGSimDetailedGeometryCase1.vsym |  | Heater.HeatExchangerUA |
| VMGSimDetailedGeometryCase2.vsym |  | Heater.HeatExchangerUA |
| VMGSimMultisidedRating1.vsym |  | Heater.MultiSidedHeatExchangerOp |
| VMGSimMultisidedRating2.vsym |  |  |

## Manual Examples\Hybrid Modeling

| Файл | Динамика | Unit ops |
|---|---|---|
| Air Membrane Tutorial\Nitrogen_Membrane_Initial.vsym |  |  |
| Air Membrane Tutorial\Results\Nitrogen_Membrane_Learned.vsym |  |  |
| Fractionation Plant Tutorial\amine_plant_Initial.vsym |  |  |
| Fractionation Plant Tutorial\regen_synthetic_data_Final.vsym |  |  |
| Fractionation Plant Tutorial\regen_synthetic_data_Initial.vsym |  |  |
| Fractionation Plant Tutorial\Results\amine_plant_Learned.vsym |  |  |

## Manual Examples\Oil Data Regressions

| Файл | Динамика | Unit ops |
|---|---|---|
| Oil Prop\OilRegressionMixturesMode.vsym |  | Oil.OilMixProps |
| Oil Prop\OilRegressionOilSolventMode.vsym |  | Oil.OilMixProps |
| Oil Source\PIONAOilSourceAsphPrecipExample.vsym |  | Oil.PIONAFeed, Mixer.Mixer |
| Oil Source\PIONAOilSourceAsphPrecipLiveOilExample.vsym |  |  |
| Oil Source\PIONAOilSourceBOCharacterizationExample.vsym |  |  |
| Oil Source\PIONAOilSourceCnAnalysisExample.vsym |  | Oil.PIONAFeed(3), Properties.VectorProps(3) |
| Oil Source\PIONAOilSourceExample.vsym |  |  |
| Oil Source\PIONAOilSourceLightBPFractionExample.vsym |  |  |
| Oil Source\PIONAOilSourceWaxPrecipExample.vsym |  |  |
| Oil Source\PIONASlateExample.vsym |  |  |

## Manual Examples\Piping and Flow

| Файл | Динамика | Unit ops |
|---|---|---|
| EjectorDesign.vsym |  | Ejector.EjectorOp |
| EjectorRating.vsym |  | Ejector.EjectorOp |
| FlareTip-Flaresim.vsym |  |  |
| GasOrifice-Dynamics.vsym | да | OrificeMetering.GasOrifice |
| GasOrifice.vsym |  | OrificeMetering.GasOrifice |
| MakeupUnit.vsym |  | Makeup.Makeup(2) |
| Mixer.vsym |  | Mixer.Mixer |
| Orifice blowdown sizing.vsym |  |  |
| PipeSegment.vsym |  | PipeSegment.PipeSegment |
| PipeSegmentWithFittings.vsym |  | PipeSegment.PipeSegment(2), Pump.PumpWithCurve |
| ReliefValve.vsym |  |  |
| RuptureDisk.vsym |  |  |
| Splitter.vsym |  | Split.Splitter |
| Valve blowdown sizing.vsym |  |  |
| Valve.vsym |  | Valve.Valve |

## Manual Examples\Production Allocation

| Файл | Динамика | Unit ops |
|---|---|---|
| RefrigerationAllocation.vsym |  |  |

## Manual Examples\Productivity Tools

| Файл | Динамика | Unit ops |
|---|---|---|
| Case Study\CaseStudy Example.vsym |  | Flash.SimpleFlash |
| OPC Connectivity\OPCDyn_Finished.vsym | да | Valve.Valve |
| OPC Connectivity\OPCDyn_Finished_Client.vsym | да | Valve.Valve, OPCClient.OPCClientOp |
| OPC Connectivity\OPCDynTest.vsym | да | Valve.Valve |
| OPC Connectivity\OPCSSTest.vsym |  | Valve.Valve |
| Optimization\DistOpt.vsym |  | Tower.DistillationColumn, SelectorBlock.SelectorBlock |
| Optimization\OptPipe.vsym |  |  |
| Optimization\OptPipe_Int.vsym |  |  |
| Optimization\PlantOptFinal.vsym |  |  |
| Optimization\PlantOptInit.vsym |  | Heater.HeatExchangerUA(5), Split.Splitter(3), Pump.PumpWithCurve(2), Mixer.Mixer(2), Compressor.CompressorWithCurve, MultifeedSeparator.MultifeedSep3, Compressor.ExpanderWithCurve, MultifeedSeparator.MultifeedSep2, SelectorBlock.SelectorBlock, Set.Set |
| Regression\Regression Viscosity.vsym |  |  |

## Manual Examples\PVT Analysis

| Файл | Динамика | Unit ops |
|---|---|---|
| PVT Analysis Example (Ahmed).vsym |  |  |
| PVT Analysis Example Swelling Test (Pedersen).vsym |  |  |
| PVT Analysis Example with Viscosity (McCain).vsym |  |  |

## Manual Examples\Reactors

| Файл | Динамика | Unit ops |
|---|---|---|
| CCR(PIONA).vsym |  | Heater.HeatExchangerUA(2), Compressor.CompressorWithCurve, VMGSim.ThreePhaseSeparator, Reactors.CCR, Heater.Cooler, Split.Splitter, EthyleneCracker.Burner, DetailedCoolers.DetailedAirCooler, Properties.SpecialProps, Oil.PIONAFeed, Properties.VectorProps, Mixer.Mixer, Tower.DistillationColumn, Pump.P |
| CCR-Platforming(Pure Components).vsym |  | Heater.HeatExchangerUA(3), Split.Splitter(3), Mixer.Mixer(3), Compressor.CompressorWithCurve, Flash.SimpleFlash, Reactors.CCR, Heater.Cooler, EthyleneCracker.Burner, DetailedCoolers.DetailedAirCooler, Properties.SpecialProps, Tower.ReboiledAbsorber, Pump.PumpWithCurve |
| conv reac dyn.vsym | да | ConvRxn.ConvReactor(2) |
| ConversionReactor.vsym |  | ConvRxn.ConvReactor |
| cstr liq dyn.vsym |  | KineticReactor.CSTR |
| CSTR1 Dyn.vsym |  | KineticReactor.CSTR |
| CSTR1.vsym |  | KineticReactor.CSTR |
| CSTR2.vsym |  | KineticReactor.CSTR |
| Electrolyzer(PEM).vsym |  |  |
| eqReac Liq Dyn.vsym |  | EquiliReactor.EquilibriumReactor |
| eqReactor dyn.vsym |  | EquiliReactor.EquilibriumReactor |
| eqReactor.vsym |  | EquiliReactor.EquilibriumReactor |
| EthyleneCracker.vsym |  | EthyleneCracker.Burner, Mixer.Mixer, Heater.Heater, Set.Set, EthyleneCracker.EthyleneCracker |
| FCC.vsym |  |  |
| FCC_Double_Riser.vsym |  |  |
| FischerTropschReactor.vsym |  | Mixer.Mixer(3), Flash.SimpleFlash(2), Heater.Cooler(2), Compressor.CompressorWithCurve, Split.Splitter, EquiliReactor.EquilibriumReactor, Reactors.FTR |
| HT-HCC(PIONA).vsym |  | Properties.VectorProps(8), Mixer.Mixer(4), Split.Splitter(2), Reactors.Hydrocracker, ProCalc.ProCalcOp, ComponentSplitter.ComponentSplitter, Pump.PumpWithCurve, MultifeedSeparator.MultifeedSep3, MultifeedSeparator.MultifeedSep2, Heater.Heater, PipeSegment.PipeSegment, Monitor.MonitorOp, Compressor.C |
| Isomerization.vsym |  | Reactors.Isomerization |
| PFR1 Dyn.vsym |  | KineticReactor.PFR |
| PFR1.vsym |  | KineticReactor.PFR |
| PlasmaGasification.vsym |  | Gasification.PlasmaGasificationOp, Balance.BalanceOp, Controller.Controller, Mixer.Mixer |
| Refinery-Component-Slate.vsym |  |  |
| SOFC_Turbine-Example.vsym |  | Compressor.CompressorWithCurve(2), Compressor.ExpanderWithCurve(2), Heater.HeatExchangerUA(2), Split.Splitter(2), VCM.FuelCell(2), Mixer.Mixer(2), EquiliReactor.EquilibriumReactor |
| SteamCrackingFurnaceConfigurations.vsym |  |  |
| Visbreaker.vsym |  | Oil.PIONAFeed, Reactors.Visbreaker |

## Manual Examples\Recombination

| Файл | Динамика | Unit ops |
|---|---|---|
| Recombination.vsym |  | Recombination.RecombinationOp |

## Manual Examples\Rotating Equipment

| Файл | Динамика | Unit ops |
|---|---|---|
| Compressor Train\Compressor Train Example.vsym |  |  |
| Compressor Train\CompressorTrain.vsym |  | Flash.SimpleFlash(4), Heater.Cooler(3), Compressor.CompressorWithCurve(3), Mixer.Mixer(3) |
| CompressorCurve.vsym |  | Controller.Controller, Compressor.CompressorWithCurve |
| expander.vsym |  | Compressor.ExpanderWithCurve |
| Pump.vsym |  | Pump.PumpWithCurve |
| ReciprocatingCompressor.vsym |  |  |

## Manual Examples\Separators

| Файл | Динамика | Unit ops |
|---|---|---|
| Air_Separation_Henry_Isotherm.vsym |  |  |
| ComponentSplitter.vsym |  | ComponentSplitter.ComponentSplitter |
| Cyclone.vsym |  | Solids.Cyclone |
| Desalter.vsym |  |  |
| Dryer.vsym |  | Solids.Dryer |
| ElectrostaticPrecipitator.vsym |  | Solids.ElectrostaticPrecip |
| KOD Manual Example.vsym |  |  |
| Membrane Example 1.vsym |  |  |
| Separator 2ph Example 1.vsym |  |  |
| Separator 2ph Example 2.vsym |  |  |
| Separator 3ph Example 1.vsym |  |  |
| Separator 3ph Example 2.vsym |  |  |
| SeparatorSizing.vsym |  | VMGSim.ThreePhaseSeparator |
| Simple_Adsorber.vsym |  |  |
| Steady State Sep.vsym |  | Flash.SimpleFlash |
| UtilityHV.vsym |  | Tank.Tank |

## Manual Examples\Streams

| Файл | Динамика | Unit ops |
|---|---|---|
| EnergyStreams.vsym |  | Heater.Cooler, Heater.Heater, Heater.HeatExchangerUA |
| MaterialAndEnergyStreams.vsym |  |  |
| MaterialStreams.vsym |  | Heater.Cooler |
| SignalStreams.vsym |  | Heater.HeatExchangerUA, Heater.Cooler, Heater.Heater |

## Manual Examples\Towers - Distillation

| Файл | Динамика | Unit ops |
|---|---|---|
| DirectColumnExample.vsym |  |  |
| DistSect Simple.vsym | да | TowerStages.DistillationSection |
| DistSect Standard.vsym | да | TowerStages.DistillationSection |
| Extractor.vsym |  | LiqLiqExt.LiqLiqEx |
| IntroductiontoVMGSimtowers.vsym |  | Tower.DistillationColumn |
| LLEX Example.vsym |  | LiqLiqExt.LiqLiqEx |
| Naptha stabilizer.vsym |  | Tower.DistillationColumn |
| PackedTowerSizing.vsym |  | Tower.DistillationColumn |
| TraySizing.vsym |  | Tower.DistillationColumn |

## Plant Examples\Alternative Energy and Fuels

| Файл | Динамика | Unit ops |
|---|---|---|
| SS-BiomassToPower.vsym |  | Mixer.Mixer(5), Compressor.CompressorWithCurve(4), Heater.HeatExchangerUA(4), DetailedCoolers.DetailedAirCooler(3), Compressor.ExpanderWithCurve(2), Split.Splitter(2), ComponentSplitter.ComponentSplitter(2), Pump.PumpWithCurve, Gasification.PlasmaGasificationOp, EquiliReactor.EquilibriumReactor, Pro |
| SS-Electrolyzer(SOEC).vsym |  |  |
| SS-NaphthaCrackingFurnace.vsym |  | Heater.HeatExchangerUA(4), Oil.PIONAFeed(3), EthyleneCracker.EthyleneCracker(3), Mixer.Mixer(2), EthyleneCracker.Burner, Flash.SimpleFlash, Set.Set |
| SS-ShellGasifier.vsym |  | Mixer.Mixer(4), ComponentSplitter.ComponentSplitter(2), Compressor.CompressorWithCurve, Heater.HeatExchangerUA, Gasification.PlasmaGasificationOp, Heater.Cooler, Split.Splitter, Controller.Controller |
| SS-SolidOxideFuelCell.vsym |  | Compressor.CompressorWithCurve(2), Compressor.ExpanderWithCurve(2), Heater.HeatExchangerUA(2), Split.Splitter(2), VCM.FuelCell(2), Mixer.Mixer(2), EquiliReactor.EquilibriumReactor |
| SS-SyngasProductionFromNaturalGasBySMR.vsym |  | EquiliReactor.EquilibriumReactor(5), Controller.Controller(3), Mixer.Mixer(3), Compressor.CompressorWithCurve(2), Heater.Cooler(2), Heater.Heater(2), Split.Splitter, Valve.Valve, ClausOperations.ClausOxygenCalculator, Set.Set, Saturation.PsychrometricOp |

## Plant Examples\Flare and Relief Systems

| Файл | Динамика | Unit ops |
|---|---|---|
| SS-SegregatedFlareSystem.vsym |  |  |
| SS-TypicalHeaderSystem.vsym |  |  |
| SSDyn-DepressuringVesselsIntoFlareHeader.vsym | да | Compressor.CompressorWithCurve(3), Heater.Cooler(3), MultifeedSeparator.MultifeedSep3(2), MultifeedSeparator.MultifeedSep2(2), Split.Splitter(2) |

## Plant Examples\Gathering and Distribution Networks

| Файл | Динамика | Unit ops |
|---|---|---|
| Dyn-GasGatheringAndProcessingAssetOLGALink.vsym |  |  |
| Dyn-OilProductionSystemOLGALink.vsym |  |  |
| SS-GasProductionSystem_PIPESIMIntegration.vsym |  |  |
| SS-MultipleFluids_LoopedNetwork.vsym |  | Oil.PIONAFeed(3), Saturation.SaturationOp(2) |
| SS-OilGatheringNetwork.vsym |  | Oil.PIONAFeed(3) |
| SSDyn-OilGatheringNetworkAndBattery.vsym | да |  |

## Plant Examples\Heavy Oil

| Файл | Динамика | Unit ops |
|---|---|---|
| SS-AthabascaBitumenDeAsphalting.vsym |  | Oil.PIONAFeed, Mixer.Mixer |

## Plant Examples\Natural Gas Processing

| Файл | Динамика | Unit ops |
|---|---|---|
| Dehydration\SS-BTEX-EmissionsInGasDehydrationUsingTEG.vsym |  | Flash.SimpleFlash(2), Heater.HeatExchangerUA(2), ProCalc.ProCalcOp, Tower.DistillationColumn, Tower.Absorber, Valve.Valve, Makeup.Makeup, Pump.PumpWithCurve |
| Dehydration\SS-GasDehydrationUsingTEG-StrippingGas.vsym |  | Flash.SimpleFlash(2), Heater.HeatExchangerUA(2), Properties.SpecialProps(2), ProCalc.ProCalcOp, Split.Splitter, Tower.DistillationColumn, Tower.Absorber, Valve.Valve, Mixer.Mixer, Pump.PumpWithCurve |
| Dehydration\SS-GasDehydrationUsingTEG.vsym |  | Flash.SimpleFlash(2), Heater.HeatExchangerUA(2), ProCalc.ProCalcOp, Tower.DistillationColumn, Tower.Absorber, Valve.Valve, Makeup.Makeup, Pump.PumpWithCurve |
| Dyn-CryogenicDemethanizer.vsym | да |  |
| Dyn-LNGProduction.vsym |  | Heater.MultiSidedHeatExchangerOp(4), Split.Splitter(3), Compressor.CompressorWithCurve(2), Heater.Cooler(2), Valve.Valve(2), Mixer.Mixer(2), ProCalc.ProCalcOp, Flash.SimpleFlash, Compressor.ExpanderWithCurve, Tower.ReboiledAbsorber, Monitor.MonitorOp, Controller.Controller, CompositeCurve.PinchUtili |
| Dyn-TwoStageEthyleneRefrigerationLoop.vsym |  | Valve.Valve(3), Compressor.CompressorWithCurve(2), Flash.SimpleFlash(2), Heater.Heater(2), Mixer.Mixer(2), Split.Splitter, Heater.Cooler |
| SS-GasProductionSystem.vsym |  |  |
| SS-GasSubcooledProcessForNGLRecovery.vsym |  | Heater.MultiSidedHeatExchangerOp(5), Compressor.CompressorWithCurve(2), Flash.SimpleFlash(2), Split.Splitter(2), Valve.Valve(2), ProCalc.ProCalcOp, Compressor.ExpanderWithCurve, Tower.Absorber, DetailedCoolers.DetailedAirCooler, Heater.Heater, Mixer.Mixer, Pump.PumpWithCurve |
| SS-LNGAPCIProcess.vsym |  |  |
| SS-MembraneForCO2RemovalFromLiquidNGL.vsym |  | Pump.PumpWithCurve(2), MembraneBase.MembraneOp, Flash.SimpleFlash, Split.Splitter, Heater.Cooler, Tower.ReboiledAbsorber, Valve.Valve |
| SS-NGLFractionationTrain.vsym |  | Tower.DistillationColumn(2), Valve.Valve, Tower.ReboiledAbsorber, Pump.PumpWithCurve |
| SS-SourWaterStrippingPlant.vsym |  | Pump.PumpWithCurve(3), DetailedCoolers.DetailedAirCooler(2), MultifeedSeparator.MultifeedSep3, Tower.ReboiledAbsorber, Heater.HeatExchangerUA, Valve.Valve, Set.Set |
| SS-TwoStageEthyleneRefrigerationLoop.vsym |  | Valve.Valve(3), Compressor.CompressorWithCurve(2), Flash.SimpleFlash(2), Heater.Heater(2), Mixer.Mixer(2), Split.Splitter, Heater.Cooler |
| Sweetening\SS-SourGasSweeteningUsingDEA.vsym |  | Flash.SimpleFlash(2), AmineOperations.AmineDetail, ProCalc.ProCalcOp, Tower.DistillationColumn, Heater.HeatExchangerUA, Tower.Absorber, Heater.Cooler, Valve.Valve, Controller.Controller, Mixer.Mixer, Pump.PumpWithCurve |
| Sweetening\SS-SourGasSweeteningUsingDGA.vsym |  | Flash.SimpleFlash(2), AmineOperations.AmineDetail, ProCalc.ProCalcOp, Tower.DistillationColumn, Heater.HeatExchangerUA, Tower.Absorber, Heater.Cooler, Valve.Valve, Controller.Controller, Mixer.Mixer, Pump.PumpWithCurve |
| Sweetening\SS-SourGasSweeteningUsingMEA.vsym |  | Flash.SimpleFlash(2), AmineOperations.AmineDetail, ProCalc.ProCalcOp, Tower.DistillationColumn, Heater.HeatExchangerUA, Tower.Absorber, Heater.Cooler, Valve.Valve, Controller.Controller, Mixer.Mixer, Pump.PumpWithCurve |
| Sweetening\SSDyn-SourGasSweeteningUsingMDEA.vsym |  |  |

## Plant Examples\Refinery

| Файл | Динамика | Unit ops |
|---|---|---|
| Catalytic Reforming\SS-Kaes03-NaphthaDesulfurizer-CCR-OilAssay.vsym |  | Mixer.Mixer(6), Heater.HeatExchangerUA(4), Balance.BalanceOp(4), Heater.Heater(4), Pump.PumpWithCurve(3), Split.Splitter(3), VMGSim.ThreePhaseSeparator(3), Compressor.CompressorWithCurve(2), Heater.Cooler(2), Tower.DistillationColumn(2), DetailedCoolers.DetailedAirCooler(2), ComponentSplitter.Compon |
| Catalytic Reforming\SS-Kaes03-NaphthaDesulfurizer-CCR-PIONA-Reactive.vsym |  |  |
| Catalytic Reforming\SS-Kaes03-NaphthaDesulfurizer-CCR-PIONA.vsym |  | Mixer.Mixer(5), Heater.HeatExchangerUA(4), Balance.BalanceOp(4), Heater.Heater(4), Pump.PumpWithCurve(3), Split.Splitter(3), VMGSim.ThreePhaseSeparator(3), Oil.PIONAFeed(2), Compressor.CompressorWithCurve(2), Heater.Cooler(2), Tower.DistillationColumn(2), DetailedCoolers.DetailedAirCooler(2), Compon |
| Crude Distillation\SS-Kaes01-CrudeVacuumDistillation-OilAssay.vsym |  | Heater.Heater(10), Set.Set(8), Properties.VectorProps(7), Pump.PumpWithCurve(5), Mixer.Mixer(5), Heater.HeatExchangerUA(4), Split.Splitter(3), Balance.BalanceOp(2), Tower.RefluxedAbsorber, Tower.Absorber, Tower.DistillationColumn, VMGSim.ThreePhaseSeparator |
| Crude Distillation\SS-Kaes01-CrudeVacuumDistillation-PIONA.vsym |  |  |
| Delayed Coking\SS-Kaes04-DelayedCoking-OilAssay.vsym |  | Pump.PumpWithCurve(6), Mixer.Mixer(6), Heater.HeatExchangerUA(3), Properties.VectorProps(3), Compressor.CompressorWithCurve(2), Heater.Cooler(2), Split.Splitter(2), Balance.BalanceOp(2), Heater.Heater(2), VMGSim.ThreePhaseSeparator(2), MultifeedSeparator.MultifeedSep2, Tower.RefluxedAbsorber, Set.Se |
| Delayed Coking\SS-Kaes04-DelayedCoking-PIONA-Reactive.vsym |  |  |
| Delayed Coking\SS-Kaes04-DelayedCoking-PIONA.vsym |  | Pump.PumpWithCurve(6), Oil.PIONAFeed(6), Mixer.Mixer(6), Properties.VectorProps(4), Heater.HeatExchangerUA(3), Compressor.CompressorWithCurve(2), Heater.Cooler(2), Split.Splitter(2), Balance.BalanceOp(2), Heater.Heater(2), VMGSim.ThreePhaseSeparator(2), MultifeedSeparator.MultifeedSep2, Tower.Reflux |
| Distillate Hydrotreating\SS-Kaes05-DistillateHydrotreater-OilAssay.vsym |  | Mixer.Mixer(7), Flash.SimpleFlash(4), Heater.HeatExchangerUA(3), DetailedCoolers.DetailedAirCooler(3), ComponentSplitter.ComponentSplitter(3), Compressor.CompressorWithCurve(2), Pump.PumpWithCurve(2), Valve.Valve(2), Properties.VectorProps(2), ProCalc.ProCalcOp, VMGSim.ThreePhaseSeparator, Multifeed |
| Distillate Hydrotreating\SS-Kaes05-DistillateHydrotreater-PIONA-Reactive.vsym |  |  |
| Distillate Hydrotreating\SS-Kaes05-DistillateHydrotreater-PIONA.vsym |  | Oil.PIONAFeed(5), Mixer.Mixer(4), Flash.SimpleFlash(4), Heater.HeatExchangerUA(3), DetailedCoolers.DetailedAirCooler(3), ComponentSplitter.ComponentSplitter(3), Compressor.CompressorWithCurve(2), Pump.PumpWithCurve(2), Valve.Valve(2), Properties.VectorProps(2), ProCalc.ProCalcOp, VMGSim.ThreePhaseSe |
| Fluid Catalytic Cracking\SS-Kaes02-FCC-OilAssay.vsym |  | Pump.PumpWithCurve(9), Mixer.Mixer(7), Properties.VectorProps(5), Heater.Cooler(4), Split.Splitter(3), Heater.HeatExchangerUA(3), Tower.Absorber(3), Compressor.CompressorWithCurve(2), VMGSim.ThreePhaseSeparator(2), Tower.DistillationColumn(2), DetailedCoolers.DetailedAirCooler(2), Balance.BalanceOp( |
| Fluid Catalytic Cracking\SS-Kaes02-FCC-PIONA-Reactive.vsym |  |  |
| Fluid Catalytic Cracking\SS-Kaes02-FCC-PIONA.vsym |  | Pump.PumpWithCurve(9), Mixer.Mixer(7), Properties.VectorProps(6), Oil.PIONAFeed(5), Heater.Cooler(4), Split.Splitter(3), Heater.HeatExchangerUA(3), Tower.Absorber(3), Compressor.CompressorWithCurve(2), VMGSim.ThreePhaseSeparator(2), Properties.SpecialProps(2), Tower.DistillationColumn(2), DetailedCo |
| HF Alkylation\SS-Kaes06-HFAlkylation-OilAssay.vsym |  | Pump.PumpWithCurve(6), Heater.Cooler(4), Mixer.Mixer(4), Tower.DistillationColumn(3), Split.Splitter(2), Controller.Controller, Heater.HeatExchangerUA, Flash.SimpleFlash, ComponentSplitter.ComponentSplitter, Valve.Valve, Set.Set, Properties.VectorProps, ConvRxn.ConvReactor, VMGSim.ThreePhaseSeparato |
| HF Alkylation\SS-Kaes06-HFAlkylation-PIONA.vsym |  |  |
| Sour Water Stripper\SS-SWS-Optimization.vsym |  |  |

## VMG Automation\Cases

| Файл | Динамика | Unit ops |
|---|---|---|
| Ammonia Synthesis PFR.vsym |  | Heater.Heater, KineticReactor.PFR |
| AmmoniaRefrigeration.vsym |  | Compressor.CompressorWithCurve, Heater.Heater, Heater.Cooler, Valve.Valve |
| Dyn-FlowControl.vsym | да | Valve.Valve, Controller.Controller |
| HCRefrigerationLoop.vsym |  | Compressor.CompressorWithCurve, Heater.Heater, Heater.Cooler, Valve.Valve |
