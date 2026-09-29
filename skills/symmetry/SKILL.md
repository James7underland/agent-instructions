---
name: symmetry
description: Работа в симуляторе ХТП Symmetry 2023.2 (SLB, бывший VMGSim) без мыши: расчёт схем (потоки, теплообменники, клапаны, сепараторы, насосы, компрессоры, колонны, реакторы, рециклы) через COM-движок и язык .tst (sym.py), разбор кейсов .vsym, динамика и ПИД (dyn.py), модель как объект для ПЛК — мост OPC UA/Modbus TCP (plcbridge.py), софт-ПЛК (softplc.py), перечень сигналов/ST (tags.py), живой GUI через REST (gui.py), схемы, отчёты Word/Excel, балансы, руководство (helpdoc.py). Используй ВСЕГДА, когда речь о Symmetry, VMGSim, .vsym/.vmp/.tst, моделировании установки, лабе/курсовой по ХТП, даже если просят «посчитать схему», «поменять давление в кейсе», «скрин схемы», «переходный процесс регулятора», «таблицу потоков», «данные для ПЛК», «OPC UA», «Modbus». Перед работой прочитай references/known-issues.md; после задачи допиши находки в references/ и строку в references/session-log.md.
---

# Symmetry 2023.2 — рабочий процесс

Установка: `C:\Program Files\VMG\Symmetry` (**не менять**; примеры в `Documentation\` только копировать).
Скилл: папка этого файла, далее `<скилл>` (обычно `~/.claude/skills/symmetry/`, часто это ссылка на папку в репозитории скиллов).
Рабочая папка для кейсов/проб: папка задачи пользователя; для своих проб — отдельная папка `Работа\` вне скилла.
Python 3.14 x64 (pywin32, pywinauto, pillow, matplotlib, openpyxl, python-docx). Из Bash: `PYTHONIOENCODING=utf-8`.
Лицензия: локальный Schlumberger Flexnet Server (порт 27000); скрипты сами ставят `SLBSLS_LICENSE_FILE=27000@localhost`
своим процессам — без этого «No license was found» (known-issues №1).

## В начале каждой задачи
1. Прочитай `references/known-issues.md` (обязательно) и хвост `references/session-log.md`.
2. По задаче: `references/command-language.md` (синтаксис команд — главное), `references/unit-ops.md` (что задавать
   аппаратам) + `unit-ops-catalog.md`/`unitops/<Имя>.txt` (порты и параметры всех 133 операций), `references/thermo.md`
   (пакеты свойств, имена компонентов), `references/dynamics.md`, `references/gui.md`, `references/automation-api.md`,
   `references/vsym-format.md`, **`references/plc-bridge.md` (модель ⇄ ПЛК: мост OPC UA/Modbus, КИП и приводы в модели, софт-ПЛК, TreiUA)**, `references/opc-plc.md` (нативный OPC DA Symmetry, олимпиадный стенд), `references/examples-index.md` (296 примеров по темам), `references/help/index.md`
   (руководство, читать через helpdoc.py). Готовые проверенные сценарии — `examples/*.tst`.

## Правила безопасности
- Оригиналы в `Program Files` и примеры не трогать; кейс пользователя перед изменением — копия `имя.bak-ГГГГММДД-ЧЧММСС.vsym`.
- Не запускать RegisterSymmetry/unregister/SwitchToLegacy/SwitchToFlex, не трогать службы лицензий, реестр, `MSI.ini`.
- **Symmetry всегда открывать на весь экран**: `gui.py launch` разворачивает окно (по умолчанию `--size max`).
- GUI — только свой экземпляр (`gui.py launch`), закрывать только его (`gui.py close` проверяет, что pid — Symmetry.exe).
  Если пользователь сам работает в Symmetry — его окно не трогать, свой запуск — отдельно (другой порт `--port`).
- Мышь и фокус пользователя не использовать (только UIA Invoke/Select, REST, COM).

## Инструменты (`scripts/`, запуск: `python "<скилл>/scripts/<x>.py" …`)
```
sym.py run a.tst [-e CMD]... [--recall CASE] [--save OUT.vsym] [--units SI] [--batch] [--streams [F.csv|.xlsx|-]]
            [--get "/S1.Out.T@C"]...        # команды → движок (Solve после каждой), ответы запросов, ошибки !!
sym.py streams CASE [--units SI] [--props T,P,...] [--comp mole|mass|none] [--out t.xlsx]   # таблица потоков
sym.py get CASE "/V1.Out.T@C" "/Feed.Out.Fraction"      # числа JSON;  sym.py tree CASE / info CASE /T1
dyn.py [--recall CASE [--to-dynamics|--reinit] | --script x.tst] --tend 600 --dt 1 [--settle 300]
       [--pre "/Integrator.IntegMeth = BDF2"]   # BDF2 — для длинных труб/жёстких моделей
       --event "60:/CN1.Target = 3 m3/h" --rec "/CN1.In@m3/h=PV" --rec "/CN1.OP=OP" --png f.png --csv f.csv
gui.py build model.tst OUT.vsym [--shot pfd.png]   # кейс с НАСТОЯЩЕЙ PFD (аппараты строятся в GUI, динамика — движком)
gui.py launch CASE | eval "CMD"... | run x.tst | get /S1.Out.T | case OUT.json | recall CASE | save |
       shot OUT.png [--pfd] | popups [DIR] | answer Yes | ui | click "Command Line" [--type Button|TabItem] | close
pfd.py CASE OUT.png [--values] [--title ...]            # схема по топологии кейса (без Visio), подписи T/P/F
report.py CASE OUT.docx [--auto-pfd] [--streams A,B] [--extra "/Q1.Out.Energy@kW=Нагрузка"] [--xlsx OUT.xlsx]
check.py CASE                                           # балансы массы/энергии по аппаратам и схеме, статусы
props.py envelope CASE /G out.png | hydrate CASE /G --p 500:10000:500 --png f | dew CASE /G --p 1000,3000 --kind dew|bubble|water
props.py sweep CASE --set /Feed.In.T --range 0:80:10 --unit C --get "/Gas.Out.MoleFlow@kmol/h=Газ" --png f   # «Case Study»
vsym.py tst CASE [--clean] | specs CASE | meta CASE | list | extract CASE DIR   # без движка
vsym.py visio CASE pfd.png [--parts 4]                  # настоящая PFD из GUI целиком (Visio, невидимо)
helpdoc.py search слова | show "Heater" | toc [подстрока]                        # руководство HTML5 (703 стр.)
catalog.py OUT_DIR [--only X]; catalog.py OUT_DIR --md F.md                      # переснять каталог операций
plcbridge.py --recall CASE --tags map.csv --ua 4841 --modbus 5020 --dt 0.5 [--speed 1] [--log t.csv]
             [--ua-client opc.tcp://localhost:4840/OpenOpcUa] [--host 0.0.0.0] [--dry]   # модель ⇄ ПЛК
plcbridge.py --gui 18686 --tags map.csv --ua 4841        # то же, но модель идёт в открытом GUI (видна схема)
softplc.py --ua opc.tcp://localhost:4841/symmetry/ | --modbus host:5020  --tags map.csv --program prog.py --log plc.csv [--sim-time]
tags.py scan CASE -o map.csv | xlsx map.csv -o io.xlsx | st map.csv -o gvl.st | from-xml OPC_DA.XML | to-xml |
        mb map.csv | browse opc.tcp://host:4840                              # перечень сигналов, адреса, ST
trend.py LOG.csv --png f.png [--cols A,B] [--x "sim_t, s"] [--mark 110:"отказ"]  # графики журналов
visio_layout.py model.tst -o model_vis.tst      # координаты PFD (Info.Visio) в конструкторы (использует gui.py build)
```
В Git Bash аргументы вида `/S1.Out.T` портятся — скрипты это чинят сами; для curl — `MSYS_NO_PATHCONV=1`.

## Типовые сценарии
**Расчёт «с нуля» (лаба/курсовая):** написать `.tst` по образцу `examples/0N_*.tst` (units → thermo → компоненты →
потоки → аппараты → соединения `->` → спецификации) → `sym.py run x.tst --streams --save x.vsym` → ошибки `!!`
исправить (ConsistencyError = лишняя спецификация; None = не хватает) → `check.py x.vsym` → `report.py x.vsym
отчёт.docx --auto-pfd` / `pfd.py`. Сепаратор + клапаны + LIC/PIC в динамике — `09_separator_methane_water.tst`; 3-фазный — 11; труба — 12;
подгонка регулятором в стационаре — 13; огибающая/гидраты — 10 (props.py); кинетика CSTR/PFR — 14/15;
оптимизатор (IPOPT) — 16; объект для ПЛК (КИП, позиционеры, отказы) + софт-ПЛК — 17; нагреватель + TIC в динамике — 18;
насосная станция (пуск/стоп насоса ПЛК) — 19. Схема для показа в GUI — `gui.py build` (не `sym.py run --save`).
Колонна — только по образцу `05_column_depropanizer.tst` (ступени, питание,
2 спецификации, P-профиль, `TryToSolve = 1`). Рецикл — оценки `~=` (T, P, F, состав) на потоке рецикла (06).

**Готовый кейс:** `vsym.py meta CASE` (аппараты и связи) → `vsym.py specs CASE` (что задано) → копия →
`sym.py run --recall копия.vsym -e "/V1.Out.P = 2000 kPa" --streams --save копия.vsym` → `check.py`.
Старые кейсы (2018–2020) пересохранятся в новом формате при `--save`.

**Чужая модель (разобрать схему):** копия → `vsym.py meta` → `vsym.py visio копия.vsym pfd.png --parts 4` →
`gui.py launch копия.vsym` (на весь экран, снимок) → движком: датчики/регуляторы (`dir /X`, `/X.In`), насосы, трубы,
ёмкости, положения арматуры, калькуляторы (Ignored — смотреть InternalVal!) → при наличии OPC/Modbus — opc-plc.md → короткий `dyn.py`
без управления (большие модели медленные: 3–5 с на 1 с модели — запускать в фоне) → отчёт `Разбор схемы.md`.
Образец: `references/cases/olympiad-2025.md`.

**Динамика/регулирование:** стационар → `/ActiveEngine = 2`, `init / / SteadyState` → снять спецификации расходов,
задать давления → `Controller` (`->>` PV, `->` OP, Kp/Ti, `Mode = Automatic`) → `dyn.py … --settle … --event … --png`
(образец 08, dynamics.md). Готовые динамические примеры: `examples-index.md`, колонка «Динамика».

**Модель как объект для ПЛК (OPC UA / Modbus, данные для логики ПЛК):** plc-bridge.md. Модель без регуляторов
Symmetry в контурах ПЛК; датчики — Controller `Indicator` (шум, отказы, уставки); клапаны — позиционер (регулятор
Manual + рампа выхода, ПЛК пишет `OPTarget`), обратная связь `Actual_Pos` (образец `examples/17_plc_separator.tst`)
→ `sym.py run model.tst --save m.vsym` → `tags.py scan m.vsym -o map.csv` (+ `xlsx`, `st` для программиста ПЛК) →
`plcbridge.py --recall m.vsym --tags map.csv --ua 4841 --modbus 5020` (или `--ua-client` к TreiUA: порт 4840 его) →
логику сначала отладить в `softplc.py` (`examples/17_softplc_program.py`), потом перенести в ST/Unimod. Тренды —
`--log` + `trend.py`. Большие модели в реальном времени не успевают — `--speed 0`.

**В живом GUI (показать пользователю / скриншоты / сохранить с PFD):** скопировать кейс под нужным именем →
`gui.py launch копия.vsym` → `gui.py eval "units SI" "/V1.Out.P = 2000 kPa" "/Gas.Out"` (с пересчётом) →
`gui.py shot окно.png` / `shot pfd.png --pfd` → `gui.py save` → `gui.py close`. Окна аппаратов открыть не можем
(нужна мышь) — попросить пользователя или брать данные из движка. Tools → Command Line в GUI принимает те же
команды и Run Script… (.tst) — можно предложить пользователю.

## После задачи
Допиши новые грабли в `references/known-issues.md`, проверенные сценарии — в `examples/` (+ unit-ops.md статус ✔),
строку «дата — задача — итог» в `references/session-log.md`. В репозиторий скиллов изменения попадают по правилам
его `CLAUDE.md`: ветка, `python tools/pack_skills.py`, пул-реквест.
