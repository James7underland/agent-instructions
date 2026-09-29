# Динамика и регулирование в Symmetry

Лицензия динамики (VMG_Dynamics) на этом ПК есть — проверено на примере регулирования расхода (08).

## Перевод кейса в динамику
1. Движку нужна поддержка динамики: COM `AddDynamicsSupport2()` (dyn.py делает сам; в GUI — «Simulation Engine Selection»).
2. Стационар должен быть решён. Затем `/ActiveEngine = 2` и `init / / SteadyState` (инициализация динамической модели
   из стационара). Для готового стационарного кейса — ключ `dyn.py --to-dynamics`.
3. В динамике расходы определяются перепадами давлений: **снимите спецификации расхода** на входах
   (`/S1.In.VolumeFlow =`) и задайте давления на границах (`/S2.In.P = 190 kPa`). У клапанов нужен `Cv`, у ёмкостей —
   объём/геометрия (у Flash/Tank — `Volume`, `Diameter`, `Length`, уровни `Liq0Level`).
4. Регуляторы ставят после init (или с `/CN1.SSActive = 0`, чтобы не мешали стационару).

## Перевод стационара в динамику — чек-лист (проверено на примере 09)
1. В стационаре задать клапанам `%Opening = 50` (+ `Out.P`) → движок рассчитает Cv под рабочую точку; ёмкостям —
   геометрию (`Diameter`, `Length`, `Orientation`).
2. `/ActiveEngine = 2`, `init / / SteadyState`.
3. **Сразу после init задать Cv всех клапанов и начальные уровни** (`/SEP.Liq0Level% = 50`) — у динамической копии
   Cv = 1, уровень ≈ 0.
4. Снять спецификации расходов на границах (`/Feed.In.MoleFlow =`), задать давления: `/Gas.In.P = 3000 kPa` и т.п.
5. Регуляторы: PV через `->>` на переменную потока, OP через `->`, **Action явно**, уставки после подключения PV,
   безударно: Manual → OP = 50 % → Automatic.

## Регулятор Controller.Controller()
```
/CN1 = Controller.Controller()
/CN1.SSActive = 0
/CN1.In ->> /S1.In.VolumeFlow        # PV: '->>' — к переменной (любой: T, P, уровень /V1.Liq0Level, состав…)
/CN1.Out -> /V1.%Opening             # OP: к сигнальному порту исполнительного органа (открытие клапана, Q и т.п.)
/CN1.Mode = Automatic                # Off | Indicator | Manual | Automatic | Cascade (по умолчанию Off!)
/CN1.Kp = 2                          # Kc, безразмерный (в % шкалы OP на % шкалы PV)
/CN1.Ti = 0.3 min                    # интегральное время; Td — дифференциальное
/CN1.MinInput = 0 m3/h               # шкала PV (от неё зависит смысл Kp!)
/CN1.MaxInput = 4 m3/h
/CN1.Target = 2 m3/h                 # задание SP
```
Порты регулятора (62): OP%, PV, SP (Target), Kp/Ti/Td, OPMin/OPMax, фильтры, FeedForward (FFwd*), AutoTune*,
шум (NoiseMag) — `references/unitops/Controller.txt`. Направление действия — параметр `Action` (Direct по умолчанию / Reverse); для регулирования расхода клапаном
Direct работает правильно (OP растёт при PV < SP). Алгоритм `Positional`, антивиндап включён.
Руководство: `helpdoc.py show "Controller"`, `"Controller Dynamics"`, туториал `"Process Control"`.

## Интегратор (`/Integrator`)
| Переменная | Смысл |
|---|---|
| `StepSize` | шаг интегрирования (напр. `0.1 s`) |
| `StopTime` | абсолютное время остановки |
| `IntegRun` | 1 — пуск, 0 — стоп. При `RealTime = 0` присваивание `IntegRun = 1` блокирует до `StopTime` |
| `IntegratorTime` | текущее модельное время (можно обнулить `= 0 s`) |
| `RealTime`, `RtFac` | режим реального времени и его коэффициент (для расчётов держать `RealTime = 0`) |
| `IntegMode`, `StepMode` | Fixed/…, Auto/… |
Снапшоты: `dstoresnpsht /Flowsheet`, `dloadsnpsht /Flowsheet 0`; COM `SaveDynSnapshot`, `RecoverDynSnapshot`.

## dyn.py — прогон с записью
```
python scripts/dyn.py --script examples/08_dyn_flow_control.tst --settle 300 --tend 600 --dt 2 \
  --event "60:/CN1.Target = 3 m3/h" --event "300:/CN1.Target = 1.5 m3/h" \
  --rec "/CN1.In@m3/h=PV" --rec "/CN1.Target@m3/h=SP" --rec "/CN1.OP=OP" --png flow.png --csv flow.csv
```
- `--settle S` — прогнать S секунд без записи (регулятор, подключённый после init, стартует с OP = 0);
- `--event T:CMD` — в момент T (от начала записи) выполнить команду (скачок SP, возмущение, смена Kp, Cv…);
- `--rec PATH[@unit][=Метка]` — что писать; график группирует кривые по единицам (отдельная ось на каждую);
- `--recall case.vsym --to-dynamics` — готовый стационарный кейс; `--save` — сохранить после прогона.
Результат примера: `examples/08_dyn_flow_control.png` (PI Kp=2, Ti=0,3 мин: на скачок SP 2→3 м³/ч перерегулирование ≈21 %, время
регулирования в зону ±2 % ≈56 с — посчитано по CSV).

## Скорость и надёжность прогона
Маленькие схемы — 60 с модели за ~1 с. Большие (олимпиадная схема нефтепровода) — 3–5 с на 1 с модели.
`dyn.py` в динамике не вызывает Solve(), после `IntegRun = 1` ждёт `IsIntegratorRunning == False` и повторяет, если
время не дошло до StopTime. Длинные прогоны запускать в фоне.

## Если интегратор встал
1. `dyn.py` напишет «интегратор остановился на X с … Сообщения: [DYNMsg …]». В GUI — окно Integrator (Integrator Log).
2. Найти аппарат из сообщения и посмотреть его вход/выход по массе в первые секунды (`sym.value`): расход на
   выходе ≫ входа — ёмкость/труба опорожняется (состояние не согласовано).
3. Переинициализация + неявный метод: `dyn.py --recall CASE --reinit --pre "/Integrator.IntegMeth = BDF2" …`
   (методы: Euler | BDF2). На олимпиадной схеме только эта связка дала устойчивые 300 с.
4. Меньший StepSize сбой композиционного расчёта не лечит (проверено).

## Реальное время, КИП, приводы (подробно — plc-bridge.md)
- `RealTime = 1` через COM блокирует `IntegRun = 1` до StopTime (идёт 1:1 со стеной) — для обмена с внешним миром
  шагать `StopTime = t + dt` (plcbridge.py). `StepSize` ≤ dt. `StepMode = Manual` через COM зависает.
- Датчик = Controller `Mode = Indicator` (+ `NoiseActive/NoiseMag`, `PVFailActive`, `PVFreezeActive`, `PVBias*`,
  `PVDrift*`, `SampleHoldTime`, векторы уставок `PVAlarms` и др.).
- Время хода клапана по команде — только «позиционером» (Controller Manual + `Setpoint_Ramp_Mode = Output`,
  `SPRateLim = 5 %/s`, команда `OPTarget`); `ActuatorType`/`Linear_Speed` работают лишь при `ActuatorFailed = 1`.
- Внешний регулятор: `ExecMode = External`, выход — `ExtOP`. Период выполнения регулятора — `CycleTime`.
- ПАЗ в модели: `CauseEffect` (проверено), `DigitalLogic`, `Scheduler` (события по времени/условию).

## Нагреватели и насосы в динамике (примеры 18, 19)
- Heater/Cooler: без Stream_Energy на InQ/OutQ; после init `/H.DeltaP =`, `/H.k = 1 m2`, `/H.Out.T =`, `/H.Volume = …`,
  нагрузка `/H.InQ = … kW` или TIC `/TIC.Out -> /H.InQ` (OP-шкала `Minimum/Maximum` в kW, `Action = Reverse`).
- Насос: после init заново DesSpeed/DesFlow/DesHead/DesEfficiency, PumpSpeed; обратному клапану — `CheckValve = 1`.

## Проверено / не проверено
✔ регулирование расхода клапаном (пример 08 + пример `VMG Automation\Cases\Dyn-FlowControl.vsym`); уровень и давление
сепаратора (09); внешний ПЛК по OPC UA/Modbus, позиционеры, отказ привода, Cause-Effect (17); нагреватель + TIC (18);
насосная станция с пуском/остановом и ПЛК (19).
◯ уровень в ёмкости, давление, температура, каскады, динамические колонны — есть в примерах: `examples-index.md`
(колонка «Динамика»: Claus\Dynamics, Depressuring, Plant Examples\…\Dyn-*.vsym). Начинайте с их .tst.
