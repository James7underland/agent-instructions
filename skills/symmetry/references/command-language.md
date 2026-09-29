# Командный язык Symmetry (sim42 / .tst)

Один и тот же язык используется везде: файлы `.tst` (журнал команд внутри каждого `.vsym`), `Eval()` в COM,
REST `/api/actions/eval`, VMGTaskRunner, консоль StandaloneServer. В руководстве HTML5 **не описан**: всё ниже
восстановлено по 296 примерам и проверено на движке 2023.2 (сессия 2026-09-26).

## Объекты и пути
- `/` — корневая схема; `/S1` — объект в ней; `/S1.In.T` — переменная порта; `/T1.Stage_5.draw` — вложенный объект.
  В подсхеме: `/SFS1.S1.Out.T` (разделитель — точка). `$RootThermo` (= `/RootThermo`) — термодинамический кейс;
  `$` — менеджер термодинамики.
- Имена чувствительны к регистру; нельзя пробел, запятую, `|`, точку. Переименование: `/S1.NewName = Feed`.
- Путь можно брать в кавычки: `'/Feed.In.T' = 15` и `"/V1.Cv" = 20` — так пишет GUI (разницы нет).
- Порты: материальные (`In`, `Out`, `Vap`, `Liq0`, `In0`, `Out1`, …), энергетические (`InQ`, `OutQ`),
  сигнальные (`DeltaP`, `OutT`, `Cv`, …). Список портов операции — `references/unit-ops-catalog.md` или `dir /X`.
- У материального потока **два порта**: `In` (куда задают/подключают) и `Out` (откуда читают результат и
  подключают дальше). Спецификации ставят на `/S1.In.*`, результаты читают с `/S1.Out.*`.

## Операторы
| Команда | Смысл |
|---|---|
| `/S1 = Stream.Stream_Material()` | создать объект `Модуль.Класс("инициализация")` (конструкторы — unit-ops-catalog.md) |
| `/S1.In.T = 20 C` | задать значение (спецификация, фиксированное). Единицы после числа; без единиц — активный набор (`units`) |
| `/S1.In.T =` | снять спецификацию (пусто справа) |
| `/Rec.In.T ~= -20 C` | начальная оценка (для рециклов, колонн) |
| `/S1.In.Fraction = 0.7 0.2 0.1` | вектор — через пробел, порядок = порядок компонентов в `$RootThermo`; доли нормируются сами |
| `/H1.In -> /S1.Out` | соединить порты (порядок не важен: `/S1.Out -> /H1.In` тоже работает) |
| `/S1.Out ->` | отсоединить порт |
| `/CN1.In ->> /S1.In.VolumeFlow` | подключить сигнальный порт к **переменной** (измерение для регулятора, Set и т.п.) |
| `$RootThermo = VirtualMaterials.Advanced_Peng-Robinson` | создать термокейс с пакетом свойств (`thermo.md`) |
| `/ -> $RootThermo` | назначить термокейс схеме (все операции наследуют) |
| `$RootThermo + METHANE ETHANE` | добавить компоненты (можно алиасы: `C1 C2 nC4 H2O CO2 H2S N2`) |
| `$RootThermo - n-HEPTANE` | удалить компонент |
| `/T1.Stage_0 + 17` | «добавить» внутрь контейнера (у колонны — ступени; у ReportManager и т.п. — элементы) |
| `delete /X` (`delete '/X'`) | удалить объект |
| `/X` (без оператора) | **запрос**: печатает объект/порт/переменную (текст с запятой как десятичным разделителем в ru-локали) |
| `dir /X` | содержимое: порты с типами, параметры `Имя = значение`. `dir /S1.Out` — все свойства потока одной строкой (точка как разделитель) |
| `cd /X`, `cd /` | сменить текущий объект (относительные пути) |
| `units SI` / `units` | сменить / показать активный набор единиц: British, Field, Hysys, PureSI, Refinery, SI, sim42, VMG, Yaws |
| `hold` / `go` | приостановить решатель / возобновить (пакетный ввод; внутри `.tst` так оформлены блоки) |
| `copy /A /B`, `paste /FS1`, `cut`, `undo`, `redo` | буфер обмена и история (как в GUI) |
| `init / / SteadyState` | инициализировать динамику из стационара (после `/ActiveEngine = 2`) |
| `optimizecode 1`, `maxversions 1`, `displayproperties …`, `commonproperties …` | служебные строки GUI в начале .tst — можно не писать |
| `# текст` | комментарий |
| `about`, `language` | версия ядра (`Version = (101062, '01.24.2023…')`), язык |

`help`, `alias`, `unitsets`, `tree` через COM ничего полезного не возвращают (None/список Python).

## Статус значения в выводе движка
`T = 20,0 * C` — `*` фиксировано (спецификация); `=` рассчитано; `|` передано со связанного порта;
`~` оценка; `None` — не определено. Через COM «нет значения» приходит числом **−12321** (sym.py переводит в None).

## Типичный каркас
```
units SI
hold
$RootThermo = VirtualMaterials.Advanced_Peng-Robinson
/ -> $RootThermo
$RootThermo + METHANE ETHANE PROPANE
go
/Feed = Stream.Stream_Material()
/Feed.In.T = 20 C
/Feed.In.P = 3000 kPa
/Feed.In.MoleFlow = 100 kmol/h
/Feed.In.Fraction = 0.8 0.15 0.05
/V1 = Valve.Valve()
/V1.In -> /Feed.Out
/V1.Out.P = 500 kPa
/S2 = Stream.Stream_Material()
/S2.In -> /V1.Out
/S2.Out.T          # запрос
```
Два из трёх (T, P, VapFrac) + расход + состав полностью задают поток. `VapFrac = 1` (с P) — точка росы,
`VapFrac = 0` — точка кипения; тогда T не задавать (снять `/S1.In.T =`).

## Решатель
- В GUI и в .tst решатель активен: после каждой команды пересчитывается всё, что можно. Через **COM `Eval` сам не
  решает** — нужен `Solve()` (sym.py делает это после каждой команды, как GUI; `--batch` — только в конце/на `go`).
- Через REST `/api/actions/eval` тоже **не решает** — используйте JSON API `{"call":"Eval","args":{"cmd":…,"solve":1}}`
  (gui.py eval так и делает).
- Недоопределённая схема не даёт ошибок — просто остаются `None`. Переопределение (лишняя спецификация) даёт
  `[Error] ConsistencyError: /V1.Out - T 30,00 [C] vs 23,93 [C]` — снимите одну из спецификаций (`путь =`).
- Рецикл: соединить петлю и дать оценки `~=` (T, P, расход, состав) на разрывном потоке. Метод — `/RecycleMethod`
  (Broyden/Wegstein/SuccessiveSubstitution), точность `/MaxError`, итерации `/MaxNumIterations`.

## Специальные синтаксисы операций (проверено)
- **Колонна** (Tower.*): `"Stage_0 + N"` → N+3 ступени (0 = конденсатор … N+2 = куб); питание по умолчанию на
  ступени N+1: `/T1.Stage_<N+1>.feed.ParentStage = 10` переносит его на 10-ю (порт станет `Feed_10_feed`);
  спецификации: `/T1.Stage_0.TopReflux = Tower.RefluxRatioSpec()` + `/T1.Stage_0.TopReflux.Port = 2.5`,
  `/T1.Stage_0.condenserL.Port.MoleFlow = 40` (дистиллят), `/T1.Stage_0.condenserV.Port.MoleFlow = 0` (полный
  конденсатор), давления `/T1.P_Profile.Item0 = 1600 kPa`, `/T1.P_Profile.Item19 = 1650 kPa`; **обязательно**
  `/T1.TryToSolve = 1` (иначе «Not Converged» без попытки). Боковые отборы: `/T1.Stage_9.draw = Tower.LiquidDraw()`,
  `/T1.Stage_23.draw = Tower.VapourDraw()`, расход `/T1.LiquidDraw_9_draw.MoleFlow = 19.5`. Продукты:
  `/Dist.In -> /T1.LiquidDraw_0_condenserL`, `/Bott.In -> /T1.LiquidDraw_19_reboilerL`, пар — `VapourDraw_0_condenserV`.
  Нагрузки: `/T1.EnergyFeed_0_condenserQ` (положительная = отводимое тепло), `/T1.EnergyFeed_19_reboilerQ`.
  Пример: `examples/05_column_depropanizer.tst`.
- **Конверсионный реактор**: `/R1.NumberRxn = 1`, `/R1.Rxn0.Formula = Имя:3+2*4-!0-2*1` (индексы компонентов
  с 0; + продукты, − реагенты, `!` базовый компонент, коэффициент 1 можно не писать), `/R1.Rxn0.Conversion = 0.95`,
  `/R1.Rxn0.RxnOrder = 0` (порядок последовательных реакций), `/R1.OutQ = 0 W` (адиабатный). Пример 07.
- **Регулятор**: `/CN1 = Controller.Controller()`, `/CN1.In ->> /S1.In.VolumeFlow` (PV), `/CN1.Out -> /V1.%Opening`
  (OP), `/CN1.Target = 2 m3/h` (SP), `/CN1.Kp`, `/CN1.Ti = 1 min`, `/CN1.Td`, `/CN1.Mode = Automatic|Manual`,
  диапазон PV `/CN1.MinInput`/`MaxInput`, `/CN1.SSActive = 0` (не работать в стационаре). Пример 08.
- **Энергопоток**: `/Q1 = Stream.Stream_Energy()`, `/Q1.Out -> /H1.InQ` (подвод) или `/Q2.In -> /C1.OutQ` (отвод).
- Параметры операции при создании: `Heater.Heater("NumberSegments = 5; DeltaP.DP = None")` — строка «имя = значение;».

## Чтение результатов (надёжно)
- Числа: `sym.py get CASE "/S1.Out.T@C" "/S1.Out.Fraction"` (COM `GetVMGVariable().GetValueAtUnits`), не парсить текст.
- Таблица потоков: `sym.py streams CASE --out t.xlsx`; всё про поток — `dir /S1.Out`.
- Тексты ответов движка идут с десятичной запятой (локаль Windows ru) — это только отображение.
