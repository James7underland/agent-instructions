# Основные unit operations: что задавать

Полный список (133 операции, порты, число параметров) — `unit-ops-catalog.md`; сырой вывод движка по каждой —
`unitops/<Имя>.txt` (все порты с подписями GUI и параметры с умолчаниями). Описание в руководстве:
`python scripts/helpdoc.py show "<Имя операции>"` (напр. `Heater`, `Compressor`, `Distillation Column`).
✔ — проверено расчётом в сессии 2026-09-26 (пример в `examples/`), ◯ — по каталогу/руководству, не прогонялось.

Общее правило: входной поток полностью задан → операции нужна столько спецификаций, сколько у неё степеней свободы
(обычно 1–2: ΔP и одна тепловая/давленческая величина). Перебор даёт ConsistencyError, недобор — None.

| Операция (конструктор) | Порты | Что задать | Статус |
|---|---|---|---|
| Материальный поток `Stream.Stream_Material()` | In, Out | на `In`: 2 из (T, P, VapFrac) + расход (MoleFlow / MassFlow / VolumeFlow / StdGasVolumeFlow…) + `Fraction`/`MassFraction` | ✔ 01 |
| Энергопоток `Stream.Stream_Energy()` | In, Out | обычно ничего (считается); можно задать `Energy` вместо спецификации на аппарате | ✔ 02,03 |
| Нагреватель `Heater.Heater("NumberSegments = 1; DeltaP.DP = None")` | In, Out, InQ | `DeltaP` + одно из: `Out.T`, `DeltaT`, `Out.VapFrac`, `InQ` (энергия); **динамика** — без энергопотока, `k`, `Volume`, нагрузка InQ (known-issues 47) | ✔ 02, 18 |
| Охладитель `Heater.Cooler(...)` | In, Out, OutQ | то же, энергия отводится через `OutQ` | ✔ 03,06 |
| Теплообменник `Heater.HeatExchangerUA(... AppT ... Q0 ...)` | InTube, OutTube, InShell, OutShell | `DeltaP0` (трубы), `DeltaP1` (межтрубье) + одно: `OutTube.T` / `OutShell.T` / `UA` / `Q0` / подход температур `AppT` | ✔ 04 (T на выходе) |
| АВО `DetailedCoolers.DetailedAirCooler()` | In, Out, OutQ, QFan | `Out.T`, ΔP; вентиляторы/геометрия — для рейтинга | ◯ |
| Клапан `Valve.Valve()` | In, Out | стационар: `Out.P` или `DeltaP` (+ `%Opening`, по умолчанию 100) → Cv **рассчитывается** (это и есть подбор Cv; для регулирования задавать %Opening = 50); `CheckValve = 1` — обратный клапан; динамика — `Cv` задать явно после init; факт. положение `Actual_Pos`; привод `ActuatorType`/`Linear_Speed` — только при `ActuatorFailed = 1` (known-issues 52) | ✔ 02, 08, 09, 17 |
| Сепаратор 2ф `Flash.SimpleFlash("LiquidPhases = 1")` | In, Vap, Liq0 (Liq1 при 2 жидк.) | ничего (адиабатно, P = P входа); можно задать `OutT` | ✔ 02,06 |
| Сепаратор 3ф `VMGSim.ThreePhaseSeparator("KeyCmp_Liq1 = WATER 0.5")` | In, Vap, Liq0 (УВ), Liq1 (вода) | ничего; ключевой компонент тяжёлой жидкости — параметр | ✔ 11 |
| Смеситель `Mixer.Mixer("NumberStreamsIn = 2")` | In0..InN-1, Out | ничего (P = min входных) | ✔ 06 |
| Делитель `Split.Splitter("NumberStreamsOut = 2")` | In, Out0..OutN-1 | доли `FlowFraction1` (N−1 штук) или расходы выходов | ✔ 06 |
| Компонентный делитель `ComponentSplitter.ComponentSplitter(...)` | In0, Out0, Out1, InQ0 | доли по компонентам | ◯ |
| Насос `Pump.PumpWithCurve("IgnoreCurve = 1; Efficiency = None")` | In, Out, InQ | `Out.P` (или DeltaP/Head) + `Efficiency` (доля, 0.7); **с характеристикой** — `UseDesignPoint = 1` + DesSpeed/DesFlow/DesHead/DesEfficiency + `PumpSpeed`; `Switch = On/Off`; после init Des* заново | ✔ 03, 19 |
| Компрессор `Compressor.CompressorWithCurve("IgnoreCurve = 1; AdiabaticEff = None")` | In, Out, InQ | `Out.P` (или DeltaP/P_Ratio) + `AdiabaticEff` (или `PolytropicEff`); мощность — `InQ` | ✔ 03 |
| Детандер `Compressor.ExpanderWithCurve(...)` | In, Out, OutQ | `Out.P` + `AdiabaticEff` | ◯ |
| Колонна `Tower.DistillationColumn(...)`, `Absorber`, `ReboiledAbsorber`, `RefluxedAbsorber` | Feed_k_*, LiquidDraw_0_condenserL, VapourDraw_0_condenserV, LiquidDraw_N_reboilerL, EnergyFeed_* | ступени, питание, 2 спецификации (флегмовое число + расход дистиллята/куба или состав), профиль давления, `TryToSolve = 1` — см. command-language.md | ✔ 05 |
| Упрощённая колонна `Distillation.ShortcutDist` / `DirectSeparator.DirectSeparator()` | In0, Out0.. | ключевые компоненты/извлечения | ◯ |
| Конверсионный реактор `ConvRxn.ConvReactor("SimultaneousRxn = 0")` | In, Out, OutQ | `NumberRxn`, `RxnK.Formula`, `RxnK.Conversion`, `DeltaP`, `OutQ` (0 = адиабатный) или `Out.T` | ✔ 07 |
| Равновесный `EquiliReactor.EquilibriumReactor("CalculationOption = 1")` | In, Out, OutQ | реакции + T/Q | ◯ |
| CSTR / PFR `KineticReactor.CSTR()`, `KineticReactor.PFR("NumberSections = 20; …")` | In, Out, OutQ | `NumberRxn`, `RxnK.Formula` (как у ConvReactor), **`RxnK.A`, `RxnK.E` (сигнальные порты!)**, `Ar`/`Er` обратной, `RxnK.FwdOrder_<КОМП>`; `CustomEquationUnitSet = SI`; уравнение скорости генерируется само (`RxnK.ReactionRateEq`, r кмоль/(с·м³), C кмоль/м³); CSTR: `Volume`, **`UseLevel = 0`** (иначе реакционный объём = уровень 50 %·V); PFR: `Diameter`, `Length`; изотермически — `Out.T` | ✔ 14 (−0,3 %), 15 (−1,5 %) |
| Трубопровод `PipeSegment.PipeSegment(...)` | In, Out, OutQ | `Length`, `InnerDiameter`/`OuterDiameter`, `Roughness`, `Elevation1` (подъём), **теплообмен обязателен**: `U = 0 W/m2-K` (адиабатно) или U + ExternalT — иначе «Missing 1 specifications» | ✔ 12 (ΔP ≈ Дарси, 0,3 %) |
| Set `Set.Set()` | Signal0 (x) → Signal1 (y), multiplier, addition | y = m·x + b: связывает две переменные (`->>` на переменные) | ◯ |
| Balance `Balance.BalanceOp(...)` | In0.., Out0.. | тип баланса (1 масса, 2 моль, 4 энергия, 5/6 комбинации) | ◯ |
| Регулятор `Controller.Controller()` | In (PV), Out (OP) | динамика: `->>` PV, `->` OP, `Target`, Kp/Ti/Td, **Action явно**, Mode; стационар (подгонка, Adjust): `/ADJ.In ->> /Oil.In.MoleFlow`, `/ADJ.Out ->> /Feed.In.T`, `Target`, `Minimum`/`Maximum`/`StepSize` в единицах управляемой, **начальное значение `/ADJ.Out = 30 C`** (не `~=` на потоке) | ✔ 08, 09 (динамика), подгонка ✔; **датчик** `Mode = Indicator` (+шум/отказы) и **позиционер** (Manual + `Setpoint_Ramp_Mode = Output`, `SPRateLim` в %/s, `OPTarget`) ✔ 17 |
| Огибающая `Envelope.PTEnvelope("InitPressures = …; Starting_P = 500 kPa")` | In, Out | встраивается в поток; `Crit_P/T`, `Cricondenbar_P/T`, `Cricondentherm_P/T`; точки кривых — запрос `/ENV.Q1.Results` (таблица vapSat/liqSat) | ✔ props.py envelope |
| Гидраты `HydrateThermoBased.Hydrate()` | In, Out | `HydrateTemp`, `HydrateAppT` (запас), `HydrateForm` (0/1) при P потока | ✔ props.py hydrate |
| Точка росы по воде `WaterDewPoint.WaterDewPoint("StartingT = 280.0 K; StepT = 2.0 K")` | In, Out | `DewPoint`; чувствительна к StartingT (260/280/300 K) — иначе «Failed to converge» | ✔ props.py dew --kind water |
| Cause-Effect `CauseEffect.CauseEffectOp()` | — | `CauseCount`, `EffectCount`, `/X ->> /CE.CauseVar_k`, `MinVal_k`/`MaxVal_k`, `/Y ->> /CE.Effect.Item_k`, матрица `/CE.Active = 1 …` целиком | ✔ (plc-bridge.md) |
| Таблица свойств `Properties.PropertyTable()` | In, Out | XProperty/YProperty/ZProperty | ◯ |

## Где смотреть ещё
- Примеры под каждую операцию: `references/examples-index.md` (поиск по имени типа, напр. `Heater.HeatExchangerUA`),
  текст кейса примера — `python scripts/vsym.py tst "<путь>.vsym" --clean`.
- Имя порта/параметра для команды: `unitops/<Имя>.txt` (строки `Port: имя = MatPort|EnePort|SigPort (Подпись GUI)`,
  `Param: имя (Подпись GUI) = значение`).
