# Symmetry как объект для ПЛК: мост OPC UA / Modbus TCP, софт-ПЛК, перечень сигналов

Проверено 2026-09-27 на примере 17 (сепаратор) и олимпиадной модели. Всё — через движок (COM), без GUI.

## 1. Что есть «из коробки» и чего нет
| Путь | Что это | Статус на этом ПК |
|---|---|---|
| **OPC DA сервер Symmetry** `OPCServer\vmgsimxopc.exe` (`OPC.VMGSim.1`, DA 2.0, COM) | GUI Symmetry отдаёт теги из XML-конфигурации (вкладка Symmetry OPC Server на форме flowsheet), связь GUI↔сервер — TCP 8080 localhost | **не зарегистрирован** (регистрация = `vmgsimxopc.exe /r` от администратора, пишет в реестр — только с разрешения пользователя); работает только из GUI, один экземпляр |
| **OPC Client** (unit op `OPCClient.OPCClientOp()`) | модель сама читает/пишет теги **OPC DA** сервера (DCS, KEPServer…) | OPC UA не умеет |
| **OPC UA** | в Symmetry 2023.2 **нет** | — |
| **TreiUA** (`C:\Program Files\UnimodPRO2\opc\opc\servopcua.exe`, служба `TreiUA`) | OPC UA сервер Unimod PRO 2 (на OpenOpcUa): переменные проекта ПЛК ТРЭИ | работает, **занимает порт 4840**, endpoint `opc.tcp://<ПК>:4840/OpenOpcUa`, анонимно, без шифрования разрешено; папки `TREI`, `TREIs` (пусты, пока проект ПЛК не загружен) |
| **plcbridge.py** (скилл) | движок Symmetry в динамике + OPC UA сервер / OPC UA клиент / Modbus TCP сервер | ✔ основной путь |

Вывод: для ПЛК с OPC UA (ТРЭИ, CODESYS, Siemens) — **plcbridge.py**. Нативный OPC DA сервер Symmetry — только если
нужна именно связка GUI + DA (как в олимпиадном стенде: Symmetry → OPC DA → шлюз → Modbus → ПЛК).

## 2. Архитектура моста
```
 Symmetry (COM, динамика)          plcbridge.py                         ПЛК / софт-ПЛК / SCADA
 ┌──────────────────────┐   шаг dt   ┌───────────────────┐  OPC UA сервер :4841 (ns=2;s=<тег>)
 │ W: команды → модель  │◄──────────│ поток модели       │◄─► Modbus TCP сервер :5020 (holding/input)
 │ интегратор +dt       │           │ asyncio: UA/Modbus │ ─► OPC UA клиент → сервер ПЛК (TreiUA…)
 │ R: показания → ПЛК   │──────────►│ журнал CSV         │
 └──────────────────────┘           └───────────────────┘
```
- Интегратор через COM в режиме `RealTime = 1` **блокирует вызов** `IntegRun = 1` до StopTime (20 с модели = 21 с
  стены) — обмениваться во время хода нельзя. Поэтому мост шагает сам: `StopTime = t + dt; IntegRun = 1` (≈20–30 мс на
  шаг у малой модели) и выдерживает темп `dt / speed` по **фактически пройденному** модельному времени.
- `dt < StepSize` → мост ставит `StepSize = dt` (иначе интегратор всё равно шагнёт на 1 с по умолчанию).
- Команды (W) применяются перед шагом, показания (R) — после; задержка ПЛК→модель ≤ dt.
- Тяжёлые модели (олимпиадная: 3–5 с стены на 1 с модели) в реальном времени **не успевают**: `--speed 0` (как можно
  быстрее) и ПЛК, работающий по модельному времени (softplc/тест), либо упростить модель.

## 3. Карта тегов (CSV `;`, UTF-8) — общий формат plcbridge / softplc / tags.py
```
tag;path;unit;dir;type;mb;expr;ua;desc
LT100.PV;/LT100.In;%;R;float;0;;;Уровень, %
LT100.RAW;/LT100.In;%;R;int;12;x/100*27648;;Код АЦП 4–20 мА (S7: 0..27648)
XV100.ZSO;/VIN.Actual_Pos;%;R;bool;13;x>98;;Концевик «открыт»
LV100.CMD;/ZVL.OPTarget;%;W;float;100;;;Задание позиционеру
XV100.OPEN;/ZVIN.OPTarget;%;W;bool;104;50*x;;Открыть (1 → 50 %)
P1.RUN;/P1.Switch;;W;bool;;'On' if x else 'Off';;Пуск насоса (строковый параметр)
LT100.PV;…;…;R;float;;;"ns=4;s=|var|PLC.GVL.LT100";…   ← колонка ua для режима клиента (NodeId в кавычках!)
```
- `dir`: R — модель→ПЛК (вход ПЛК), W — ПЛК→модель (выход ПЛК). **Команду и обратную связь разделять**
  (CMD → `%Opening`/`OPTarget`, POS ← `Actual_Pos`) — как в реальном перечне сигналов.
- `type`: float → OPC UA Double / Modbus float32 (2 регистра, `--word-order ABCD|CDAB`); int → Int32 / int16;
  bool → Boolean / регистр 0/1.
- `expr` (Python от `x`): для R — из модели в ПЛК (масштаб, пороги), для W — из ПЛК в модель (строки On/Off).
  Начальное значение W-тега = значение модели, обращённое через expr (линейно).
- `unit` — единицы Symmetry (`kPa`, `C`, `m3/h`, `kmol/h`, `%`, `%/s`); пусто — SI.
- Строка с `#` в начале — комментарий. NodeId с `;` — в двойных кавычках.

## 4. Команды
```bash
# перечень сигналов по модели (+ адреса Modbus: входы с 0, выходы с 1000), экспорт
python scripts/tags.py scan CASE.vsym -o tags.csv [--streams]
python scripts/tags.py xlsx tags.csv -o io_list.xlsx        # перечень для программиста ПЛК
python scripts/tags.py st tags.csv -o gvl.st                # VAR_GLOBAL … END_VAR (REAL/INT/BOOL + комментарии)
python scripts/tags.py from-xml OPC_DA.XML -o tags.csv      # из конфигурации OPC сервера Symmetry
python scripts/tags.py to-xml tags.csv -o OPC.xml           # обратно (для нативного OPC DA сервера)
python scripts/tags.py mb tags.csv                          # раздать недостающие адреса Modbus
python scripts/tags.py browse opc.tcp://localhost:4840      # узлы OPC UA сервера (TreiUA) → NodeId для колонки ua

# мост: сервер OPC UA + Modbus (модель в реальном времени, шаг 0,5 с)
python scripts/plcbridge.py --recall CASE.vsym --tags tags.csv --ua 4841 --modbus 5020 --dt 0.5 --log trend.csv
#   --host 0.0.0.0 — слушать сеть (реальный ПЛК; Windows спросит про брандмауэр), по умолчанию 127.0.0.1
#   --to-dynamics (стационарный кейс) | --reinit (переинициализировать динамику) | --pre "/Integrator.IntegMeth = BDF2"
#   --speed 2 — вдвое быстрее реального; 0 — без пауз; --duration 600 — стоп через 600 с модели; --save out.vsym
# мост: клиент к OPC UA серверу ПЛК (TreiUA / CODESYS): R-теги пишутся в ПЛК, W-теги читаются из ПЛК
python scripts/plcbridge.py --recall CASE.vsym --tags tags.csv --ua-client opc.tcp://localhost:4840/OpenOpcUa
python scripts/plcbridge.py --tags tags.csv --dry            # только проверить карту и адреса

# софт-ПЛК: отладка логики на Python до переноса в ST
python scripts/softplc.py --ua opc.tcp://localhost:4841/symmetry/ --tags tags.csv --program prog.py --log plc.csv
python scripts/softplc.py --modbus localhost:5020 --tags tags.csv --program prog.py
python scripts/trend.py plc.csv --x "sim_t, s" --cols LT100.PV,LV100.CMD,ALM.LV_FAULT --png plc.png --mark 110:"отказ"
```
**Режим живого GUI** (видно PFD, пока ПЛК управляет процессом): `gui.py launch CASE.vsym` (динамический кейс, лучше
собранный `gui.py build` — с настоящей схемой) → `plcbridge.py --gui 18686 --tags map.csv --ua 4841 --dt 1`.
Интегратор идёт в GUI (RealTime = 1, темп RtScale = --speed), мост раз в dt читает пакетом (REST `Values`,
~50–200 мс) и пишет командами Eval. Шаг обмена ≥ 0,5–1 с. Проверено на примере 19 (снимок `examples/19_gui_live.png`).
**Ускоренный прогон логики**: мост `--speed 5` + `softplc.py --sim-time` (таймеры/ПИД по модельному времени Sim.Time).

Служебные узлы OPC UA моста: `Sim.Time` (модельное время), `Sim.Run` (запись False — пауза, True — пуск),
`Sim.Speed`, `Sim.Step`, `Sim.Status`, `Sim.Healthy` (False — интегратор встал; мост ставит паузу).

## 5. Программа софт-ПЛК (`--program prog.py`)
```python
from softplc import PID, TON, TOF, SR, RS, R_TRIG, F_TRIG, RAMP
lic = PID(kp=2.0, ti=300.0, pv_lo=0, pv_hi=100, direct=True)   # direct: выход растёт при PV > SP
t_hh = TON(3.0)
def init(io):                     # один раз после первого чтения
    lic.bumpless(io["LV100.CMD"])  # безударный пуск: первый выход = текущей команде
def scan(io, dt):                 # каждый цикл (--scan 0.2 с)
    io["ALM.LSHH"] = t_hh(io["LT100.PV"] > 85, dt)          # ALM.* — внутренняя память (только журнал)
    io["LV100.CMD"] = lic(50.0, io["LT100.PV"], dt)
```
PID — зависимая форма как у Symmetry (Kp безразмерный: % выхода на % шкалы PV; Ti, Td в секундах), anti-windup.
Блоки 1:1 переносятся в ST (TON/SR — стандартные, ПИД — блок ПИД библиотеки ПЛК; у ТРЭИ — см. скилл
unimod-pro-trei, fb-library.md). Пример: `examples/17_softplc_program.py` (LIC, PIC, LSHH с TON, диагностика
«команда ≠ положение» → авария и отсечка).

## 6. Как делать модель «под ПЛК» (шаблон — examples/17_plc_separator.tst)
1. **Без регуляторов Symmetry** в контурах, которые реализует ПЛК (иначе два регулятора на один клапан).
2. **Датчики** — `Controller` в режиме `Indicator`: `/LT100.In ->> /SEP.Liq0Level%`, шкала `MinInput/MaxInput`.
   Даёт шум (`NoiseActive = 1`, `NoiseMag = 2 %`), неисправности датчика (`PVFailActive`/`PVFreezeActive`/
   `PVBiasActive`/`PVDriftActive` + `PVBias`/`PVDrift`), выборку анализатора (`SampleHoldTime`, `IsAnalyzer`),
   уставки сигнализаций — векторы `PVAlarms`/`DVAlarms`/`SPAlarms`/`OPAlarms`/`RateAlarms` (4 значения: LL, L, H, HH —
   порядок по форме GUI, числом не проверен).
   Датчик давления — к переменной **потока** (`/G1.In.P`), не порта аппарата.
3. **Исполнительные механизмы.** В 2023.2 `ActuatorType = Linear|FirstOrder|Hybrid` + `Linear_Speed`/`Time_Constant`
   у Valve **работают только при отказе** (`ActuatorFailed = 1` → уход в `ActuatorFailPosition` с заданной
   скоростью). На смену `%Opening` (прямо или от регулятора) клапан переходит **мгновенно** (проверено 6 вариантами).
   Время хода по команде → **позиционер**: регулятор в Manual с рампой выхода, ПЛК пишет `OPTarget`:
   ```
   /ZVL = Controller.Controller()
   /ZVL.Out -> /VL.%Opening
   /ZVL.Mode = Manual
   /ZVL.OP = 50 %
   /ZVL.Setpoint_Ramp_Mode = Output
   /ZVL.SPRateLim = 5 %/s          # 100 % за 20 с; ЕДИНИЦЫ ОБЯЗАТЕЛЬНЫ (%/s, %/min), «5 %» → Ambiguous unit
   /ZVL.Ramping_Active = 1
   /ZVL.OPTarget = 50 %
   ```
   Обратная связь положения — `/VL.Actual_Pos` (при отказе привода ≠ команде — ПЛК это видит), `%Opening` — это
   команда. Концевики — bool-теги с `expr` `x>98` / `x<2`.
4. **Насосы**: `Switch` = On/Off (строковый параметр; bool-тег с `expr` `'On' if x else 'Off'`), `PumpSpeed`
   (об/мин), `InQ` — мощность. **Если переменную ведёт калькулятор/регулятор модели** (олимпиадная схема:
   `MNA_Parameters.B ->> Switch`), прямая запись затирается на следующем шаге — писать в ведущую ячейку (D).
5. **Возмущения и отказы для испытаний ПЛК** — W-теги `SIM.*`: давление на границе (`/Feed.In.P`), отказ привода
   (`/VL.ActuatorFailed`), неисправность датчика (`/LT100.PVFailActive`, `PVFreezeActive`), остановка насоса.
6. **Внутренняя ПАЗ модели** (имитация независимой защиты): `CauseEffect`:
   ```
   /CE = CauseEffect.CauseEffectOp()
   /CE.CauseCount = 1
   /CE.EffectCount = 1
   /SEP.Liq0Level% ->> /CE.CauseVar_0
   /CE.MaxVal_0 = 51 %                  # MinVal_k — нижний порог
   /VIN.ActuatorFailed ->> /CE.Effect.Item_0
   /CE.Active = 1                       # матрица причин×следствий целиком (N×M значений); Item_k — ошибка
   ```
   Проверено: при уровне > 51 % VIN «отказал» и закрылся за ≈2 с. `CE.EffectInvert`, `CE.CauseOverride` — векторы.
7. **Прочие логические блоки** (не прогонялись командами): `DigitalLogic` (AND/OR/XOR/NOT/SR/D-латч/On-/Off-Delay/
   счётчики; векторы `DLGate_In1/In2/Op/IsExtOut/UserName`), `Scheduler` (последовательности событий по времени/
   условию; настройка в GUI), `SelectorBlock` (формула `Equation = I[0]…`, задержка `DelayTime`, шум), `DataFilter`.
   Регулятор: `ExecMode = External` + `ExtOP` — выход задаёт внешний контроллер (альтернатива позиционеру),
   `SplitRange`, `FeedForward`, `AutoTune ATV1/ATV2`, `CycleTime` (период ПЛК), `GainSched`.

## 7. Проверенный сценарий (examples/17_plc_loop.png)
Мост (OPC UA 4841 + Modbus 5020, dt 0,5 с, реальное время 1:1, шаг модели 22–30 мс) ⇄ софт-ПЛК по OPC UA (скан
0,2 с) + возмущения по Modbus: P сырья 5000→5600 кПа (41 с) — PIC отработал (≈4040 кПа, SP 4000, ПИ ещё сходится);
отказ привода LV-100 (110 с) — положение 50→0 %, команда ≈51 %, через 15 с авария `ALM.LV_FAULT`, ПЛК закрыл
XV-100, приток 0, уровень остановился на 50,65 %. Режим клиента проверен на фиктивном OPC UA «ПЛК» (узлы
`ns=2;s=PLC.GVL.*`): мост пишет измерения, подхватывает команду ПЛК 50→70 %.

## 7а. Насосная станция (examples/19_*)
Ёмкость с азотной подушкой и дыхательным клапаном, насос с характеристикой, обратный клапан, напорная задвижка,
датчики LT200/FT201. ПЛК (`19_softplc_program.py`): насос по уровню 60/40 % (SR с гистерезисом), LAHH, «насос в работе
без расхода 10 с». Прогон ×5 (`19_plc_loop.png`): останов на 40 %, пуск на 60 %. После init — восстановить
характеристику насоса и CheckValve (known-issues 64).

## 8. TreiUA / Unimod: план подключения реального проекта
1. В Unimod включить OPC-сервер контроллера (скилл unimod-pro-trei, gui-guide «Внешние коммуникации и OPC»),
   загрузить проект/симулятор → в TreiUA появятся узлы под `TREI`/`TREIs`.
2. `python scripts/tags.py browse opc.tcp://localhost:4840/OpenOpcUa --depth 6` → NodeId переменных.
3. В карте тегов колонка `ua` = NodeId (в кавычках), R — входы ПЛК (AI/DI), W — выходы (AO/DO).
4. `plcbridge.py --ua-client opc.tcp://localhost:4840/OpenOpcUa --tags map.csv --recall model.vsym`.
Не проверено: запись в узлы TreiUA (права/типы), формат NodeId ТРЭИ. Альтернатива — Modbus TCP: мост —
slave (`--modbus 502`/5020), ПЛК — master (блоки MB_TCP_MST + MB_R_F16/MB_W_F, float = 2 регистра; порядок слов
подобрать `--word-order`).
