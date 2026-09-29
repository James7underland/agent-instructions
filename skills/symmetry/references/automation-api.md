# Способы управлять Symmetry без мыши (проверено 2026-09-26)

Установка: `C:\Program Files\VMG\Symmetry` (2023.2.0.160). Лицензия: локальный **Schlumberger Flexnet Server**
(служба, `C:\Schlumberger_Licensing\lmgrd.exe`, порт 27000). Клиенту нужно `SLBSLS_LICENSE_FILE=27000@localhost`
в окружении процесса — без неё GUI показывает «No license was found», а движок падает на создании пакета свойств
(`Failed to get VMG license: EOS Package [FlexLMKey check]`). Все скрипты скилла ставят переменную сами.

| Способ | Когда | Состояние между вызовами | Статус |
|---|---|---|---|
| COM `VMGMasterInterfaceNet.VMGMainEngine` (in-process, sym.py/dyn.py) | расчёты, пакетная работа, динамика | нет (каждый вызов sym.py — новый движок; кейс хранить в .vsym) | ✔ основной |
| GUI `UI64\Symmetry.exe --HTTPServer 2 --HTTPServer_Port N` + REST (gui.py) | работа «в программе», скриншоты, сохранение с PFD | да (живой GUI) | ✔ |
| `UI64\VMGTaskRunner.exe script.tst -c case.vsym -l All -o log.txt` | прогнать .tst поверх кейса(ов) | нет; **ответы запросов не печатает**, кейс не сохраняет | ✔ (ограниченно) |
| `SymmetryApp.Symmetry` (COM к GUI по `--rotname`) | разово: SaveAs из живого GUI | **GUI закрывается, когда клиент отключается** | ⚠ одноразово |
| `UI64\VMGStandaloneServer.exe` | консольный сервер | — | ✗ требует прав администратора (WinError 740) |
| `VMGSim.engine64` (сырой Python-движок) | не нужен | — | не использовался |

## COM: VMGMainEngine (pywin32, 64-битный Python)
```python
os.environ["SLBSLS_LICENSE_FILE"] = "27000@localhost"
e = win32com.client.Dispatch("VMGMasterInterfaceNet.VMGMainEngine")   # ~1 с
e.SetCallBackCOMObject(win32com.server.util.wrap(CB()), "CB")        # сообщения: CB.PyInfoMessage(msg, args, type)
e.Eval("/S1.In.T = 20 C")      # -> (текст_ответа | None, ...) ; ошибки команд — ТОЛЬКО через callback ([Error] …)
e.Solve()                       # Eval сам не пересчитывает!
v = e.GetVMGVariable("/S1.Out.T")[0]; v.GetValue(0); v.GetValueAtUnits("C", 0)[0]; v.GetValues(); v.GetValuesAtUnits("kg/h")
e.RecallFile(abs_path) -> 0;  e.SaveFile(abs_path) -> (0, path);  e.ClearCase();  e.ReadScript(path)
e.IsOnHold, e.SolverState, e.UnitSystem (GetUnitSetNames, ActiveUnitSet), e.ThermoAdmin (AvPropPkgNames, AddThermoCase),
e.RootFlowsheet (AddUnitOp, GetUnitOp, GetMatStreams, GetCompoundNames, ...), e.GetIntegrator("/"), e.AddDynamicsSupport2()
```
- Методы с byref-параметрами возвращают кортежи (`GetVMGVariable` → `(obj, path)`), берите `[0]`.
- Свойства-геттеры в pywin32 без `Get`: `e.IsOnHold` (не `GetIsOnHold()`), `e.SolverState`, `e.RootFlowsheet`.
- `RenderMessage(msg, args)` превращает код сообщения в текст (кортеж, текст — `[0]`).
- Значение «не определено» = **−12321.0**.
- Переменная: `Size`, `DataType` (битовая маска: 1 float, 2 int, 4 str, 8 bool, 16 vector, 32 scalar…), `IsSpec()`,
  `GetStatus()` (2 Fixed, 4 Calculated, 8 Passed, 32 Estimated), `GetUnitName()`, `UnitTypeName`.
- Полный интерфейс (перечень методов) — `Documentation\Symmetry COM Automation.pdf` (409 стр.; текст извлечён в
  `Symmetry Claude\Работа\com_pdf.txt`); VBA-примеры — `Documentation\VMG Automation\Excel Examples\*.xls`.
- После динамики процесс Python падает при выгрузке COM (код 139) — скрипты завершаются `os._exit()` (sym.hard_exit).
- Длинный расчёт нельзя прервать изнутри — запускайте sym.py с `timeout` в Bash.

## Динамика через COM (dyn.py)
`e.AddDynamicsSupport2()` (до recall/построения) → `/ActiveEngine = 2` → `init / / SteadyState` → регуляторы →
`/Integrator.RealTime = 0`, `/Integrator.StopTime = 60 s`, `/Integrator.IntegRun = 1` — **блокирует** до StopTime
(60 с модели ≈ 1 с), время `/Integrator.IntegratorTime`, шаг `/Integrator.StepSize`. Интегратор: `e.GetIntegrator("/")`
(StartIntegrator/StopIntegrator/IsRunning/IntegTime). Подробнее — dynamics.md.
`RealTime = 1` тоже блокирует `IntegRun = 1` (темп 1:1) — для обмена с ПЛК шагать самим (plcbridge.py, plc-bridge.md).
Движок можно создавать в рабочем потоке (plcbridge): `pythoncom.CoInitialize()` в потоке; AddDynamicsSupport2 — всегда.

## REST (GUI с `--HTTPServer 2`), база `http://localhost:18686/api`
Спецификация: `Documentation\web\api\rest\openapi.yaml`, схемы `Documentation\web\schemas\*.json`.
- `GET /values/<путь без ведущего />` → `{"status":0,"resp":число}` в **единицах активного набора GUI** (по умолчанию
  Field! — выполните `units SI`).
- `POST /actions/eval` (text/plain команда) → `{"resp":"OK","msg":ответ}` — **без пересчёта**.
- `POST /actions/json` `{"call":"Eval","args":{"cmd":"…; …","solve":1}}` — с пересчётом (несколько команд через `;`).
  Другие call: Value(s), SetValue(s), Variable(s), Paths, Case, SetCase, UpdateCase, Recall, SolveCase, RunCaseStudy,
  AddDataTable, ValuesFromDataTable, pyVars.
- `GET /case` — весь кейс JSON (объекты, переменные со статусами `cs`, координаты PFD `pfd`), `GET /paths/<путь>`,
  `POST /actions/recall` (text/plain абсолютный путь).
- `UpdateCase` с изменёнными `pfd`-координатами принимается («Applied variables»), но PFD **не двигается**.
- WebSocket `ws://localhost:<port>/events/infomessages` (`{"cmd":"join","msgFilter":["DYNStep"]}`) — сообщения интегратора.
- Из Git Bash curl с путями `/S1…` портится (MSYS превращает в `C:/Program Files/Git/S1…`) — `MSYS_NO_PATHCONV=1`
  или gui.py (Python).

## Сохранение из GUI
REST не умеет сохранять. gui.py save: UIA Invoke кнопки Save на панели быстрого доступа (первая `RibbonButton`
верхнего уровня) → диалог «Save Project: Do you want to overwrite…» → Invoke «Yes». Сохраняет в текущий файл
(поэтому GUI запускать сразу с копией нужного файла). Save As через UI не автоматизирован (диалог выбора файла).

## Аргументы Symmetry.exe (руководство «Symmetry Command Line Arguments»)
`"case.vsym"`, `--HTTPServer 2`, `--HTTPServer_IP host`, `--HTTPServer_Port N`, `--rotname NAME` (для SymmetryApp),
`--silent` (невидимый), `--runtime 1`, `--allowenv All|VMGSim|VMGPipe|VMGFlare|VMGThermo`.

## VMGTaskRunner
`VMGTaskRunner.exe "C:\abs\script.tst" [-c case.vsym | cases.txt] [-g] [-l None|Main|All] [-o log.txt]` — пути
абсолютные. Выполняет команды поверх кейса и завершается; в лог попадают сообщения решателя, но не ответы на
запросы и не сохраняет кейс (сохранение — через sym.py). Годится для пакетной «прогонки» списка кейсов.

## Инструменты Case Study и Optimizer через команды
```
/..CaseStudyManager.CaseStudy1 = CaseStudy.CaseStudy()
/..CaseStudyManager.CaseStudy1.Mode = AllCombinations
/..CaseStudyManager.CaseStudy1.IndVariables + /Feed.In.T          # независимая (можно несколько: IndVariable_1 …)
/..CaseStudyManager.CaseStudy1.IndVariable_0.MinValue = -50 C
/..CaseStudyManager.CaseStudy1.IndVariable_0.MaxValue = 50 C
/..CaseStudyManager.CaseStudy1.IndVariable_0.NuPoints = 10
/..CaseStudyManager.CaseStudy1.DepVariables + /Liq.In.MoleFlow    # зависимые; доля компонента — DepCustomVariables
/..CaseStudyManager.CaseStudy1.Run = 1
```
Оптимизатор — то же в `/..CaseOptimizerManager.Optimizer1` + `DepVariable_0.ObjFnMode = Maximize|Minimize`,
`CstVariables + путь` с Min/Max, решатель IPOPT; итог — `IndVariable_0.ValForBestVal` (пример 16).
Для скриптов удобнее `props.py sweep` (таблица + график сразу; Case Study складывает результаты в таблицы
данных GUI).
