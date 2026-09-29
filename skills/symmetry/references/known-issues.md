# Известные грабли Symmetry 2023.2 (читать перед работой)

## Лицензия и запуск
1. **Без `SLBSLS_LICENSE_FILE=27000@localhost` ничего не работает**: GUI — окно «Symmetry License: No license was
   found. The program will be terminated», движок — `[Error] Failed to get VMG license: EOS Package [FlexLMKey check]`
   на `$RootThermo = …` (поток создаётся, но не считается — все None). Сервер лицензий — служба
   «Schlumberger Flexnet Server» (`C:\Schlumberger_Licensing\lmgrd.exe`, порт 27000). Скрипты скилла ставят
   переменную только своим процессам; системные переменные и реестр НЕ менять. Если служба остановлена — сказать
   пользователю (запуск служб — его решение).
2. `VMGStandaloneServer.exe` требует прав администратора (WinError 740 / «Permission denied» из Bash) — не использовать.
3. Из Git Bash exe в `Program Files\VMG` иногда «Permission denied» — запускать через Python `subprocess`.
4. COM-движок только 64-битный (in-process .NET): Python 3.14 x64 + pywin32 — ок.

## Движок (COM)
5. `Eval()` **не пересчитывает** — нужен `Solve()` (sym.py делает после каждой команды). Ошибки команд не бросают
   исключений: только сообщения callback `[Error] …` (sym.py печатает `!! [Error] …` и считает их).
6. «Нет значения» через COM = **−12321.0** (sym.py → None). В тексте ответов — `None`.
7. После динамики Python падает при выгрузке COM (exit 139, segfault) — вывод уже сделан; скрипты выходят
   `os._exit` (`sym.hard_exit`). Своих скриптов это тоже касается.
8. Текст ответов с десятичной **запятой** (локаль ru). Числа брать через `GetVMGVariable` (`sym.py get`), не парсить.
9. Имена компонентов в ответах с пробелом (`CARBON DIOXIDE`), в командах — с `_`. Алиасов `O2`, `CO` нет.
10. `help`, `alias`, `unitsets` через COM бесполезны (None). Единицы: `e.UnitSystem.GetUnitSetNames()`.
11. Недоопределённость молчит (None), переопределение — `ConsistencyError: /V1.Out - T 30,00 [C] vs 23,93 [C]`.
12. Энтальпия без теплот образования → энергобаланс реактора по потокам не сходится (это норма, см. thermo.md).

## Колонны
13. `Stage_0 + N` → N+3 ступени (0…N+2); питание по умолчанию на ступени N+1 (`Stage_<N+1>.feed.ParentStage = k`
    переносит). Без `/T1.TryToSolve = 1` колонна висит «Info - Not Converged» и не пытается решаться.
14. Q конденсатора `EnergyFeed_0_condenserQ` — положительное число = отводимое тепло.

## Рециклы
15. Нужны оценки `~=` на разрывном потоке, **включая давление** — без P смеситель не считает (все None, без ошибок).
    Сходимость ~1e-4 (MaxError) → баланс схемы сходится на ~1e-4, check.py допуск 5e-4.

## Динамика
16. Регулятор, подключённый после `init / / SteadyState`, стартует с OP = 0 — провал в начале (dyn.py `--settle`).
    `Mode` по умолчанию `Off`. В динамике снять спецификацию расхода, задать давления на границах.
17. `IntegRun = 1` блокирует до `StopTime` только при `RealTime = 0` (dyn.py ставит).

## GUI / REST
18. REST `/actions/eval` не решает — `/actions/json` с `"solve":1`. `/values` отдаёт числа в единицах GUI (по
    умолчанию **Field**!) — сначала `units SI`.
19. curl из Git Bash портит `/S1.In.T` → `C:/Program Files/Git/S1.In.T` (сообщение `Unknown operator Files/Git/...`).
    `MSYS_NO_PATHCONV=1` или Python (gui.py/sym.py сами чинят такие аргументы).
20. `SymmetryApp.Symmetry.InitializeFromRunning(rot)` работает один раз: когда клиент отключается, **GUI закрывается**
    (и при os._exit тоже). Для постоянной связи — только REST.
21. Сохранение из GUI: кнопка Save → диалог «Save Project … overwrite?» → Yes (gui.py save). Save As не автоматизирован.
22. Окна свойств аппаратов открыть без реальной мыши нельзя (двойной щелчок PostMessage игнорируется, Invoke у
    узлов дерева нет). Не трогать мышь/фокус пользователя.
23. PFD кейсов, собранных скриптом, «рассыпан» (значки в ряд, потоки не соединены); `UpdateCase` координаты не
    применяет. Для отчёта — `pfd.py`.
24. `pywinauto top_window()` может вернуть всплывающее окно-счётчик ошибок (450×67) — искать окно по заголовку.
    `descendants()` теряет узлы — рекурсивный `children()`.
25. Окно GUI по умолчанию 1200×750: PFD мелкий, `shot --pfd` лучше после растяжения (gui.py делает 1700×1050).

28. Команды через REST без `solve` (напр. `units SI`) GUI может не применить — gui.py шлёт каждую команду с
    `"solve":1` (и в `eval`, и в `run`).

29. Третий формат `_metadata.json` (2023, MetaVersion 2 из старых кейсов): `RootFlowsheet.unitOps{тип:{имя:{matPortsIn:{…}}}}`
    — vsym.load_meta нормализует все три.
30. В динамическом кейсе **не вызывать `Solve()`** (sym.run_commands делает это после команд): интегратор потом
    «застревает» (время стоит, IntegRun возвращается сразу). dyn.py шлёт команды без Solve и ждёт/повторяет до StopTime.
31. Большие динамические модели медленные: олимпиадная схема (140 потоков, 73 клапана, трубы по 25–27 секций) —
    3–5 с реального времени на 1 с модели. Длинные прогоны — в фоне, dt 10–20 с.
32. os._exit после динамики иногда всё равно даёт код 139 (segfault при выходе) — вывод к этому моменту готов.
33. Кейс из GUI открывается с сохранёнными окнами (калькуляторы, тренды) — это не ошибки; `gui.py popups` их покажет.
34. Главное окно может называться просто «Symmetry» (без «| файл») — main_hwnd ищет по префиксу.

35. Интегратор может молча встать (IntegRun → 0, время не растёт) из-за сбоя расчёта аппарата — причина только в
    Info-сообщениях `DYNMsg ('Composition Calculations Failed For /.Pipe2',)`; в GUI — окно Integrator
    «Composition Calcs Failed - See Log For Details». Уменьшение StepSize не помогает. dyn.py печатает причину и
    прерывает прогон. Смотрите баланс аппарата (вход/выход по массе) в первые секунды — несогласованное
    сохранённое динамическое состояние (труба «выливается»). **Лечение (олимпиадная схема): `dyn.py --reinit
    --pre "/Integrator.IntegMeth = BDF2"`** — по отдельности не помогают (Euler+reinit падал на 88 с, BDF2 — на 39 с).
36. `gui.py eval` в динамике — только с `--no-solve`; `IntegRun = 1` через REST блокирует HTTP-запрос до остановки.

37. **После `init / / SteadyState` у динамической копии Cv клапанов = 1 и уровень ёмкостей ≈ 0** — стационарные
    значения не переносятся. Задавать явно: `/V.Cv = …` (взять из стационара при %Opening = 50), `/SEP.Liq0Level% = 50`.
38. **Controller.Action задавать всегда явно.** Direct = OP растёт при PV > SP (уровень/давление выходным клапаном);
    Reverse = расход собственным клапаном. Значение по умолчанию в динамике не совпадает с «Direct» из каталога
    (пример 08 без Action работал как Reverse, с явным Direct — разваливался).
39. PV регулятора через `->>` — только переменная ПОТОКА (`/G1.In.P`); `/SEP.Vap.P` даёт «Can't add P to SEP».
    До подключения PV единицы Min/MaxInput/Target неоднозначны («Ambiguous unit kPa») — сначала `->>`, потом уставки.
40. Безударный пуск регулятора: `Mode = Manual` → `OP = 50 %` → `Mode = Automatic`.
41. Hydrate (`HydrateThermoBased.Hydrate()`, встраивается в поток) работает: HydrateTemp, HydrateAppT (запас),
    HydrateForm. WaterDewPoint на насыщенном водой газе: «Failed to converge water dew point» (не разобрано).
    Envelope: Crit_T считается, Cricondenbar/therm = None для CH4+H2O (DryBasis=1) — не разобрано.

42. Git Bash превращает однобуквенный путь `/G` в `G:/` — sym.unmangle чинит; лучше давать потокам имена длиннее 1 буквы.
43. Envelope: точки кривых — только в `/ENV.Q1.Results` (`/ENV.Q1` — одна строка); объект считается, если после
    каждой команды вызывать Solve (props.py так делает). WaterDewPoint: подбирать StartingT (props.py перебирает).
44. Кривая гидратов (Hydrate) ниже ~2,5 МПа для газа с малым содержанием воды уходит в сильный минус — расчёт для
    фактического влагосодержания; при ≥3 МПа совпадает со справочными данными для метана (6,4 °C при 5 МПа).
45. Стационарный регулятор-подгонка не работает, пока не задано начальное значение ВЫХОДА: `/ADJ.Out = 30 C`
    (оценка `~=` на потоке не помогает), плюс `Minimum`/`Maximum`/`StepSize`.
46. Единица `t/h` у движка — `ton(metric)/h` (sym.py понимает `t/h`, `т/ч`, `кПа`, `м3/ч`); список допустимых —
    `GetVMGVariable(p)[0].GetValidUnitNames()`.

47. **РЕШЕНО 2026-09-27 (пример 18):** Heater/Cooler в динамике работает, если (1) к InQ/OutQ НЕ подключён Stream_Energy
    (нагрузка — прямо на порту `/H.InQ = 50 kW` или регулятором `/TIC.Out -> /H.InQ`), (2) после init снят DeltaP и
    `k` ≥ ~0.01 m2 (k из стационара ~6e-5 → сбой; перепад давления — клапаном), (3) снят `Out.T`. После init T в
    объёме сбрасывается к T входа и растёт заново. Схема, построенная сразу в динамике, тоже работает.
    Прежняя запись: **Heater/Cooler в динамике через COM не запускается** («Pressure flow solver - Unit Op /.H cannot solve»,
    «Problem with Model Specification»). Проверено безуспешно: вода/метан/смесь; с входным клапаном и без; внутри
    рабочей схемы 09 перед сепаратором; снятие DeltaP / k / Out.T, задание Q, Volume 0,2–1 м³; заводской Heater.vsym
    (k и Volume после init = None). Не разобрано — вероятно, нужна настройка PF-спецификаций в GUI (Integrator →
    Spec Analysis) или UA-режим. Для температурных контуров пока использовать GUI / другой аппарат.
    Дополнительно проверено: объём/геометрия нагревателя до init, NumberSegments 5, Cooler вместо Heater, голый init —
    везде та же ошибка. В GUI: `/ActiveEngine = 2` через REST открывает модальный диалог «Do you want to initialize
    dynamics with the values from Steady State?» (Yes/No/Cancel Change) — `gui.py answer Yes`; но лента не
    переключается в режим Dynamics (нет вкладки Dynamics, время 0,00 с) — полноценно динамику в GUI включает кнопка
    «Simulation Engine Selection» (панель выбора движков, UIA Toggle — не разобрано).

48. Кинетика: `RxnK.FwdA/FwdE` — только поля GUI (в журнале .tst они есть), движок берёт **`RxnK.A`, `RxnK.E`**
    (сигнальные порты). `E = 0` → «Missing E in …» — задавайте малое E (1 кДж/кмоль).
49. CSTR с `UseLevel = 1` (по умолчанию) считает реакционный объём по уровню жидкости (50 %) — конверсия
    занижена как для V/2. Для сравнения с учебником `UseLevel = 0`.

50. Оптимизатор/Case Study — объект `CaseStudy.CaseStudy()` в `/..CaseOptimizerManager` (IPOPT):
    `IndVariables + путь` (+ `IndVariable_0.MinValue/MaxValue`), `DepVariables + путь` (`DepVariable_0.ObjFnMode =
    Maximize|Minimize`), `CstVariables + путь` (`CstVariable_0.MinValue/MaxValue`), `Run = 1`. Итог — в
    `IndVariable_0.ValForBestVal`, `DepVariable_0.OptimizerValue`; схема НЕ меняется (применить вручную).
    Ограничение по доле компонента (`CstCustomVariables + X CompositionVariable`, `X.CompositionPath + …`) не
    соблюдается — ограничивать скалярными величинами. Пример 16.

## Связь с ПЛК, реальное время, КИП (2026-09-27, см. plc-bridge.md)
51. **`Ignored = 1` в выводе `dir`/`/X.Ignored` — у ЛЮБОГО объекта** (в т.ч. только что созданного): это отображение;
    фактическое значение — `InternalVal` (0/None — работает, 1 — выключен). Из-за этого в первом разборе олимпиадной
    схемы калькуляторы ошибочно названы выключенными (исправлено).
52. **Привод клапана (`ActuatorType` Linear/FirstOrder/Hybrid + `Linear_Speed`/`Time_Constant`) работает только при
    отказе** (`ActuatorFailed = 1`). Смена `%Opening` — напрямую или от регулятора — отрабатывается мгновенно (6
    вариантов, до и после init). Время хода по команде — «позиционер»: Controller в Manual,
    `Setpoint_Ramp_Mode = Output`, `SPRateLim = 5 %/s`, `Ramping_Active = 1`, команда в `OPTarget` (пример 17).
53. `SPRateLim` (и др. величины LinearRate) — **только с единицами** `%/s` или `%/min`; `= 5 %` → «Ambiguous unit %»,
    значение остаётся незаданным (рампа тогда идёт с 5 %/s по умолчанию).
54. `%Opening` — это **команда**, фактическое положение — `Actual_Pos`. Обратную связь в ПЛК брать с `Actual_Pos`.
55. **`RealTime = 1` через COM: `IntegRun = 1` блокирует до StopTime** (20 с модели ≈ 21 с стены), читать/писать во
    время хода нельзя. Для обмена с ПЛК — шаги `StopTime = t + dt` и свой темп (plcbridge.py).
    `StepMode = Manual` + `Steps` через COM — **зависание** (не использовать).
56. Шаг обмена меньше `StepSize` (по умолчанию 1 с) → интегратор всё равно шагает на StepSize; ставить
    `/Integrator.StepSize = dt` (plcbridge делает сам).
57. `sym.py run` скрипта с `/ActiveEngine = 2` раньше сохранял **нединамический** кейс (не было AddDynamicsSupport2 —
    «Dynamics is required to run this flowsheet» при прогоне). Исправлено: run_commands сам вызывает
    AddDynamicsSupport2 и после `/ActiveEngine = 2` больше не делает Solve().
58. Переменную, которую ведёт калькулятор/регулятор модели (олимпиада: `MNA_Parameters.B ->> /01MNA-04.Switch`),
    бесполезно писать напрямую — на следующем шаге затрётся. Писать в ведущую ячейку/задание.
59. **Порт 4840 занят службой TreiUA** (OPC UA сервер Unimod PRO 2, `servopcua.exe`): свой OPC UA сервер — на 4841.
    В TreiUA узел `OpenOpcUaSystem.Shutdown` доступен на запись — **никогда не писать** (остановит сервер).
60. CauseEffect: матрицу задавать целиком `/CE.Active = 1 0 …` (N×M); `/CE.Active.Item_0 = 1` → «Failed in
    SynchValToDynMatrix». Причина — `/X ->> /CE.CauseVar_k` + `MinVal_k`/`MaxVal_k`, следствие —
    `/Y ->> /CE.Effect.Item_k` (ставится в 1 при срабатывании).
61. Свои Python-скрипты с путями Symmetry в argv из Git Bash — прогонять аргументы через `sym.unmangle` (иначе
    `/VL.%Opening` → `C:/Program Files/Git/VL.%Opening`, «Unknown operator Files/Git/…»).
62. Вывод скриптов в конвейер (`| tail`) шёл в cp1251 и падал на «→» — sym.py/softplc/trend/tags/helpdoc теперь
    переключают stdout на UTF-8. Пакеты pip — в `%APPDATA%\Python\Python314\site-packages` (asyncua 2.0.1,
    pymodbus 3.15: новый API SimDevice/SimData + action; старые примеры с ModbusSlaveContext не работают).
63. Ячейка Process Calculator со связью `->>`: запись в ячейку сразу передаётся в модель, но **сама ячейка при
    чтении остаётся прежней** — обратную связь брать с фактической переменной.

64. **init / / SteadyState сбрасывает характеристику насоса** (DesFlow 3600 м3/ч, DesHead 10 м, DesSpeed 3600 об/мин,
    КПД 85 %) и **выключает обратный клапан** (`CheckValve` показывает 1, `InternalVal = 0`) — после init задать
    Des* и `CheckValve = 1` заново (пример 19), иначе поток идёт через насос обратно. Как и Cv клапанов, уровни.
65. Насос с характеристикой: `Pump.PumpWithCurve("IgnoreCurve = 1; …")` + `UseDesignPoint = 1` + DesSpeed, DesFlow,
    DesHead, DesEfficiency + `PumpSpeed`. `IgnoreCurve = 0` вместе с UseDesignPoint → «User Curves and Simple Curves
    Both Active». Пуск/стоп — `Switch = On|Off` (без двигателя; при заданной PumpSpeed выбега нет — расход падает за шаг).
66. В динамике учитывается статический напор (Do Static Head Calcs = Internal по умолчанию): расходы через клапаны
    к/от ёмкостей отличаются от стационара (в примере 19 приток 30 → 23 т/ч). VolumeFlow двухфазного потока включает газ.
67. Уставки сигнализаций регулятора — **только поэлементно** `/LT100.PVAlarms.Item_2 = 50.5 %` (0 LL, 1 L, 2 H, 3 HH
    по форме GUI). `/LT100.PVAlarms = 10 20 80 90` опустошает вектор и **интегратор молча стоит на t = 0**;
    `PVAlarms[2] = …` создаёт мусорный параметр. Состояние сигнализации движком не читается (не найдено) —
    сигнализации формировать в ПЛК.
68. REST GUI: `IntegRun = 1` не возвращает ответ, пока интегратор идёт (запускать в фоновом потоке); чтение/запись на
    ходу работают (`Values` с полем `u` — единицы, иначе единицы GUI, по умолчанию Field). Ошибочная команда на ходу
    (напр. `/Integrator.StopTime =`) открывает **модальное окно, которое блокирует весь REST** — `gui.py answer OK`.
    Единицы REST — имена движка (`ton(metric)/h`, не `t/h`).
69. **PFD рисуется только если аппараты создаются командами в самом GUI** (gui.py run / build): тогда GUI строит
    фигуры и линии связей, координаты — `Info.Visio.X/Y` (аппарат) и `X0/Y0/X1/Y1` (поток) в строке параметров
    конструктора (дюймы, Y вверх). Кейс, созданный движком, открывается с аппаратами в ряд и потоками списком без линий.
    Движок при recall+save сохраняет .vsd/.GUI (PFD не теряется), но дублирует `_metadata.json` в архиве (GUI открывает).
70. Новый кейс в GUI («Create New Case») сразу открывает модальное «Configure Property Package» — команды через REST
    при этом проходят; для сборки удобнее открывать GUI с «пустым» кейсом, сохранённым движком (gui.py build).

## Прочее
26. `_metadata.json` старых примеров (2018–2020) другого формата — `vsym.load_meta()` нормализует; статус в нём —
    текст на момент сохранения, живой статус — из движка (check.py).
27. Heredoc в Bash + Python-строки с `\n`/`\|` портятся — править файлы инструментом Edit/Write.
