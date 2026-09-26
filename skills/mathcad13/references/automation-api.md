# COM-автоматизация Mathcad 13

Проверено на этой машине (Windows 11, Mathcad 13.0.3, 2026-09-24). Готовый драйвер — `scripts/mc.ps1`;
этот файл нужен, когда требуется что-то, чего mc.ps1 не умеет.

## Регистрация и запуск
- ProgID `Mathcad.Application` (CurVer `.1`), CLSID `{94FBBD40-E791-4e8c-8F21-FA7A724654DA}`,
  `LocalServer32 = ...\Mathcad 13\mathcad.exe` (запускается как `mathcad.exe -Embedding`).
- Typelib `{A86F3A06-7127-4E0F-BCAF-56D15FA57AC4}` «Mathcad 12 Automation API», зарегистрирован только `win32`
  (`automation.dll`). .NET-обёртка: `Interop.Mathcad.dll`.
- Старый API: ProgID `mathcad.auto` (IMathcad: `Recalculate`, `GetComplex`, `SetComplex`, `SaveAs`, `Worksheet`) — не нужен.
- Также есть `Mathcad.Worksheet` (встраивание OLE), `Mathcad.MatrixValue/NumericValue/StringValue` (объекты значений).
- **Клиент — 32-битный**: `C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe`. mc.ps1 перезапускает себя сам.
  Python без pywin32/comtypes — COM только через PowerShell.
- Старт сервера ~0,6 с, открытие листа ~0,6–0,8 с, пересчёт большого листа (321 регион) ~0,3 с; весь вызов mc.ps1 ~3 с.

## Раннее и позднее связывание (важно)
- `Application`, `Worksheets`, `Worksheet`, объекты значений — методы/свойства работают напрямую (`$ws.GetValue('x')`).
- `Region`, `MathInterface`, `Metadata`, `Windows` — прямое обращение возвращает **пусто** (и `foreach` по `Regions`
  тоже). Нужно позднее связывание:
```powershell
function P($o, $n) { [System.__ComObject].InvokeMember($n, [Reflection.BindingFlags]::GetProperty, $null, $o, $null) }
function SetP($o, $n, $v) { [void][System.__ComObject].InvokeMember($n, [Reflection.BindingFlags]::SetProperty, $null, $o, @($v)) }
function M($o, $n, $a) { [System.__ComObject].InvokeMember($n, [Reflection.BindingFlags]::InvokeMethod, $null, $o, $a) }
$regs = $ws.Regions
for ($k = 0; $k -lt $regs.Count; $k++) { $r = $regs.Item($k); $type = P $r 'Type'; $mi = P $r 'MathInterface' }
```
  `Regions.Item(k)` — индекс с 0. `Worksheets.AddFromTemplate` вызывать через `M`.

## Объектная модель (снято рефлексией Interop.Mathcad.dll)
```
Application (IMathcadApplication2)
  Name, Version ("13,0,3,0"), FullName, Path, DefaultFilePath, Visible, Active, HWND, Left/Top/Width/Height
  Worksheets, Windows, ActiveWorksheet, ActiveWindow
  SetOption(mcShowMessageBoxes=0, bool), GetOption(...)
  Quit(MCSaveOption), CloseAll(MCSaveOption)
Worksheets: Count, Item(i), Add(), Open(path), AddFromTemplate(path), Remove(i)
Worksheet (IMathcadWorksheet2)
  Name, FullName, Path, NeedsSave, IsOpen, Regions, Windows, Metadata, SelectedRegion
  GetValue(name) -> Value, SetValue(name, variant), Recalculate(), Save(), SaveAs(path, MCFileFormat),
  Close(MCSaveOption), PrintAll(), GetOption/SetOption(mcAutocalc=0, bool)
Region (IMathcadRegion2): Type (MCRegionType), Tag, X, Y (пиксели 96 dpi = pt*4/3), Metadata, MathInterface
MathInterface: XML (get/set, Math20), UnitsXML, HasError, ErrorMsg
Value: Type ("Numeric"|"String"|"Matrix"), AsString
  NumericValue: Real, Imag, Integer   StringValue: Value
  MatrixValue: Rows, Cols, GetElement(r, c) -> Value, SetElement(r, c, v)
WorksheetMetadata: Title, Author, Company, Description, Keywords, RevisedBy, Revision, DocumentID, VersionID,
  ParentVersionID, BranchID, CustomItems, AddCustomItem, RemoveCustomItem
Window: Zoom, WindowState, ScrollTo(x,y), ScrollToRegion(r), Activate()   (Zoom НЕ влияет на экспорт картинок)
События: WorksheetOpened/Closing, WindowActivated/Deactivated, Changed, Recalculated, Quit
```
Перечисления: `MCSaveOption` mcSaveChanges=0, mcPromptToSaveChanges=1, **mcDiscardChanges=2**;
`MCRegionType` text=0, math=1, bitmap=2, metafile=3, ole=4 (**график тоже отдаёт 1**);
`MCWindowState` max=0, min=1, normal=2; `MCCustomMetadataType` text=0, date=1, number=2, yesno=3.

## SaveAs: коды форматов (проверено)
| Код | Имя | Результат |
|---|---|---|
| 18 | mcXMCD / mcXMCD13 | XML-лист Mathcad 13 ✔ |
| 19 | mcXMCDZ | сжатый xmcd ✔ |
| 15 | mcXMCT | шаблон (тот же XML) ✔ |
| 13 | mcXMCD12 | XML для Mathcad 12 ✔ |
| 3 | mcHtml | HTML + папка `<имя>_images` (текст — UTF-8 текстом, формулы/графики — PNG 96 dpi) ✔ |
| 16 | mcRTF | **пишет HTML, а не RTF** ✘ (RTF — только из меню GUI) |
| 17 / 12 / 9 | mcMcad11 / mcMcad12 / current | бинарный .mcd (`MCAD 311…`, `312…`, `313…`) ✔ |
| 0 | default | бинарный .mcd v12, **расширение игнорируется** — всегда задавайте код |
| 2, 8 | MathML, Mcad2001 | «формат больше не поддерживается» ✘ |

## GetValue / SetValue
- `GetValue(name)` — последнее (нижнее) значение переменной в листе. Результат в **базовых СИ без единиц**.
  Литеральный индекс через точку: `GetValue("M.max")`. Греческие — `\` + латинская буква шрифта Symbol:
  `σ`→`\s`, `α`→`\a`, `φ`→`\f`, `θ`→`\q`, `ω`→`\w`, `Δ`→`\D` (mc.ps1 переводит сам). Штрих — `'`.
- Матрица → `MatrixValue`, элементы `GetElement(r, c)` (с 0, row-major доступ; в XML хранение по столбцам).
- `SetValue(name, v)` связывает значение **в начале листа**: если в листе есть `name := …`, оно перекроет
  SetValue. Для входных данных готового листа менять определение в файле (`xmcd.py set`) или через
  `MathInterface.XML`. Принимает число, строку, `double[]` (→ вектор-столбец), `double[,]` (→ матрица).
  Единицы задать нельзя (только числом в базовых СИ). При включённом автопересчёте SetValue запускает фоновый
  пересчёт — перед Close вызывайте `Recalculate()`.
- Неизвестная переменная → исключение «The requested value was not found in the worksheet».

## Ошибки регионов
`MathInterface.HasError`, `ErrorMsg` — строка с табами, первое поле — код, например
`bad_variable\tmc_undefinedVar\tmc_undefinedVar\t\tvalue_zone\t`. Текст: `messages\messages_EN.xml`
(`<short_name>` → `<text>`), mc.ps1 подставляет. Частые: `bad_variable` (не определено),
`bad_dimensions` (несогласованные единицы), `divide by zero`, `ODE*` (решатели).

## Изменение формулы через COM
`SetP $mi 'XML' '<ml:define xmlns:ml="http://schemas.mathsoft.com/math20">…</ml:define>'` — работает,
пересчёт даёт новый результат, `SaveAs` сохраняет. **Но после этого Mathcad упал при Close/Quit**
(«Microsoft Visual C++ Runtime Library»). Поэтому: сохранить (SaveAs) сразу после правки, ждать падения
и добивать процесс по PID. Надёжнее править файл: `xmcd.py set` / `xmcd.py expr --inner` для генерации XML.
Передавать XML в дочерний PowerShell только через файл (аргументы командной строки теряют кавычки).

## Жизненный цикл и зависания
1. `SetOption(0, $false)` — без модальных окон (иначе автоматизация может повиснуть на диалоге).
2. Всегда `Close(2)` всех листов, пауза ~300 мс, `Quit(2)`, `ReleaseComObject`.
3. Лист не закрыт → `mathcad.exe -Embedding` остаётся жить. Даже при правильном порядке иногда висит/падает
   при выходе — mc.ps1 узнаёт PID сервера (`Application.HWND` → `GetWindowThreadProcessId`) и через 4 с добивает.
4. «Зомби»: `Get-Process` может показывать уже завершённый mathcad (HasExited=True) — проверяйте `HasExited`.
5. Убивать можно только свои `-Embedding` процессы; GUI-сессию пользователя (без `-Embedding`) не трогать.

## Метаданные
Чтение и запись через `P`/`SetP` на объекте `Metadata` листа (Title, Author, Company, Description, Keywords,
RevisedBy); кириллица сохраняется. В mc.ps1: `-Meta "Title=Расчёт балки;Author=Иванов И.И."` + `-SaveAs`.

## Что не открывается
- Лист со скриптовыми объектами (ползунки/кнопки/текстовые поля на VBScript, CLSID `d058c3d4-…`, `mcscript.ocx`)
  → `Worksheets.Open` бросает «Unknown Error» (и с `Visible=true`). Без этих регионов лист открывается.
- Файлы Mathcad 14/15 → «The specified XML worksheet was created with a newer version of Mathcad and cannot be opened.»
- Prime `.mcdx` → «Failed to open document».
- `Regions.Count` — только регионы верхнего уровня (вложенные в area не считаются).

## Прочее из DevRef (`doc\Help_EN\DevRef\*.html`)
- Scriptable components (VBScript/JScript внутри листа), элементы управления (Slider, TextBox, ListBox, …),
  DAQ, компоненты Excel/MATLAB/ODBC — регионы `ws:component` в XML; через COM не управляются.
- User EFI DLL: свои функции на C (`userefi\microsft\` — MCADINCL.H, MCADUSER.LIB, примеры), DLL кладётся в
  `userefi\` и подхватывается при старте Mathcad. Нужен компилятор MSVC (x86).
- Открыть лист пользователю в GUI: `Start-Process "file.xmcd"` (ассоциация `.xmcd` → Mathcad, DDE).
