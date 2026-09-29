# Связь модели Symmetry с ПЛК (OPC DA → Modbus TCP → контроллер)

> Основной путь теперь — **plc-bridge.md** (свой мост OPC UA/Modbus на движке, без GUI и без регистрации DA-сервера).
> Здесь — нативный OPC DA Symmetry и разбор олимпиадного стенда.

Типовой стенд (олимпиада «Олимпиадная схема», 2025): динамическая модель Symmetry играет роль объекта, ПЛК
(ТРЭИ, проект Unimod — см. скилл unimod-pro-trei) реализует управление. Цепочка:
**Symmetry (динамика) ⇄ VMG OPC DA Server ⇄ OPC→Modbus-шлюз ⇄ ПЛК (массивы регистров)**.

## OPC DA сервер Symmetry
- `C:\Program Files\VMG\Symmetry\OPCServer\`: `vmgsimxopc.exe` (сервер), `RegisterOPC.bat`/`RunOPC.bat`,
  данные — `C:\ProgramData\Schlumberger\Symmetry\Symmetry_x64\OPCServer\`. Лицензия `VMG_OPC_Server`.
- Список тегов — XML (пример: `OPC_DA.XML` рядом с моделью):
```xml
<Main><Settings><ActiveCaseId>My case 3</ActiveCaseId></Settings>
 <Variables><Group Name="aitec">
  <Variable><OPCTag>01LV-03.%_Opening</OPCTag><SimPath>/01LV-03.%Opening</SimPath>
   <CanWrite>True</CanWrite><VarType>Float</VarType><VarShape>Scalar</VarShape><UnitName>Active Set</UnitName></Variable>
```
  `OPCTag` — имя для клиентов (в тегах `%Opening` → `%_Opening`), `SimPath` — путь переменной модели,
  `CanWrite` — запись разрешена, `VarType` Float/String, `UnitName` Active Set (единицы активного набора GUI!).
- Разобрать XML: `python -c "import xml.etree.ElementTree as E; [print(v.findtext('OPCTag'), v.findtext('SimPath'), v.findtext('CanWrite')) for v in E.parse('OPC_DA.XML').iter('Variable')]"`.
- Ячейки калькулятора (ProCalc) видны как `ИмяКалькулятора.PCalcMgr.Sh1.B12.Value` → `SimPath …Val_Num`.

## Приём «ПЛК пишет в таблицу, таблица — в модель»
Запись идёт не прямо в `%Opening`/`PumpSpeed`, а в ячейки Process Calculator, у которых стоит связь
`->>` на переменную модели (`/VLV_Opening_Percent.Sh1.B12.Var ->> /01GV-07.%Opening`). Чтение — прямые теги
(`01GV-07.%_Opening`, `01PT-01.PV` = `/01PT-01.In`) или вычисляемые ячейки (состояние 1/0).
Запись в ячейку сразу передаётся в связанную переменную, **но сама ячейка при чтении не меняется** — обратную связь
брать с фактической переменной. `dir`/`/X.Ignored` у всех объектов показывает `Ignored = 1` — смотреть `InternalVal`
(0/None — работает, 1 — выключен).

## «Датчики» в модели
Датчики давления/уровня сделаны объектами `Controller.Controller()` в режиме `Mode = Indicator` (без выхода OP):
`/01PT-01.In ->> /S29.In.P` — PV = давление потока, тег `01PT-01.PV`. Регулирование при этом выполняет ПЛК
(через PCV/задвижки/частоту насосов), а не Symmetry. Проверка: `dir /01PT-01` → `Mode`, `/01PT-01.In` → `Conn. to`.

## Насосы под управлением
`Pump.PumpWithCurve`: `Switch` (вкл/выкл, String), `PumpSpeed` (об/мин), `InQ` (подводимая мощность — «наличие
питания»). Остановленный насос с открытыми задвижками пропускает поток (см. разбор олимпиадной схемы).

## Разбор такого стенда (чек-лист)
1. `vsym.py meta` — аппараты и связи; `vsym.py visio CASE pfd.png --parts 4` — схема из GUI целиком.
2. Датчики: для каждого `Controller` — PV (`Conn. to`), режим, SP; сравнить с описанием в таблице тегов.
3. Калькуляторы: ячейки `A/B/C…` и связи `->>` (из `.tst`: `grep "/<имя>.Sh1."`), флаг `Ignored` (по `InternalVal`!).
4. OPC XML ↔ таблица Modbus: каждому тегу есть `SimPath`, адреса без пересечений, R/W совпадают.
5. Динамика: прогнать `dyn.py --recall CASE --tend 300 --dt 15 --rec …` без управления — устойчивость, уровни.

## Нативный OPC DA сервер Symmetry — детали (руководство «Symmetry OPC Server»)
- Отдельное приложение `OPCServer\vmgsimxopc.exe` (LightOPC, OPC DA 2.0, ProgID `OPC.VMGSim.1`); регистрация
  `RegisterOPC.bat` = `vmgsimxopc.exe /r` (**админ, реестр — только с разрешения пользователя**); на этом ПК НЕ
  зарегистрирован (в реестре только `OPC.Automation`, `OPC.ServerList` — OPC Core Components).
- Symmetry (GUI) передаёт данные серверу по TCP 127.0.0.1:8080 (`OPCServerTest\VMGSim-OPCComConfig.xml`, `<Port>`).
  Одновременно только один экземпляр Symmetry; смена набора тегов — с перезапуском сервера.
- Включение: форма главного flowsheet → вкладка «Symmetry OPC Server» → Configure (группы, переменные,
  Import/Export XML) → Connect. Командами: `/OPCSrvConn.Connect = 1`, `/OPCSrvConn.Disconnect = 1`.
- Служебные теги (всегда): `Main.RecallModel`, `Main.SaveModelAs`, `Main.BaseDirectory`, `Main.ActiveModel`;
  `DynamicsMain.IntegratorRunning` (`/Integrator.IntegRun`), `.IntegratorTime`, `.StopTime`, `.StepSize`,
  `.RealTimeFactor` (`RtFac`), `.ActivateRealTime` (`RealTime`), `.RealTimeScale` (`RtScale`), `.StepMode`, `.Steps`
  (`OPCServer\VMGSim-OPCGeneralTags.xml`) — внешняя система может запускать/останавливать интегратор.
- Для OPC UA-клиентов (ПЛК) нужен шлюз DA→UA; проще plcbridge.py (`tags.py from-xml OPC_DA.XML` переносит
  готовую конфигурацию тегов).

## Блок OPC Client (модель читает/пишет чужой OPC DA сервер) — команды (пример OPCDyn_Finished_Client)
```
/OPC1 = OPCClient.OPCClientOp()
/OPC1.Client.OPCServerID = OPC.VMGSim.1      # ProgID сервера; OPCServerNode = имя/IP (DCOM) или пусто
/OPC1.Client.Enabled = 1
/OPC1.Client.Connect = 1
/OPC1.Client.Groups + Group1
/OPC1.Client.Group1.OPCItems + Tag1
/OPC1.Client.Group1.Tag1.OPCItemID = TestGroup.S1.T
/OPC1.Client.Group1.Subscribe = 1
/OPC1.Client.Group1.Tag1.SimVar = /S2.In.P
/OPC1.Client.Group1.Tag1.Mode = Write to OPC Server      # или Read From OPC Server / Write To Sim
```
Группа: `Update Rate`, `Dead Band`, `Write/Read Behaviour` (Auto — с частотой интегратора), `Condition Variable`,
`Dependent Groups`. Только OPC DA (COM/DCOM), OPC UA не умеет.
