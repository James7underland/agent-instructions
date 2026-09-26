# Формат файла .xmcd (Mathcad 13, worksheet 2.0.2)

XML в UTF-8. Схемы: `C:\Program Files (x86)\Mathsoft\Mathcad 13\schema\Worksheet20.xsd`, `Math20.xsd`,
`UnitSystem20.xsd`, `Provenance10.xsd` (для Mathcad 12: `Worksheet10.xsd`, `Math10.xsd`).
Конвертеры версий: `transform\Xmcd12To13.xslt`, `Xmcd13To12.xslt`. `.xmcdz` — то же, сжатое;
`.xmct` — шаблон (тот же XML); `.mcd` — старый бинарный формат (читать только через COM → SaveAs 18).

## Скелет
```xml
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<?validation-md5-digest 46d8ae80...?>            <!-- пишет Mathcad; при ручной правке удалить (или оставить) -->
<worksheet version="2.0.2" xmlns="http://schemas.mathsoft.com/worksheet20"
    xmlns:ws="http://schemas.mathsoft.com/worksheet20" xmlns:ml="http://schemas.mathsoft.com/math20"
    xmlns:u="http://schemas.mathsoft.com/units10" xmlns:p="http://schemas.mathsoft.com/provenance10" ...>
  <metadata> generator, userData(title, description, author, company, keywords, revisedBy),
             identityInfo(revision, documentID, versionID, parentVersionID, branchID) </metadata>
  <settings> presentation / calculation / editor / fileFormat / miscellaneous </settings>
  <regions> <region …>…</region>* </regions>
  <binaryContent> <item item-id="N" content-encoding="gzip">base64…</item>* </binaryContent>
</worksheet>
```
Mathcad 12: `version="1.0.4"`, `worksheet10`/`math10`, генератор «Mathcad Professional 12.0» — Mathcad 13
открывает их без проблем; xmcd.py читает оба.

**md5-подпись**: файл без неё или с устаревшей Mathcad (через COM, с подавленными диалогами) открыл без
жалоб; xmcd.py при правке её удаляет. После пересохранения через mc.ps1 подпись снова корректна.

## Важные настройки (`<settings>`)
- `presentation/textRendering/textStyles/textStyle name="Normal|Heading 1|…"` — стили текста
  (`inlineAttr font-family, font-charset (204 = кириллица), font-size…`).
- `presentation/mathRendering`: `operators` (вид знаков), `mathStyles` (шрифты формул: Variables, Constants,
  User 1–7, Math Text Font), `results/general precision="3" exponential-threshold="3" …`,
  `results/unit format-units simplify-units` (показывать `Pa` вместо `kg·m⁻¹·s⁻²`).
- `presentation/pageModel paper-code="9"` (A4; 1 = Letter), `page-width/height` (pt), `margins`.
- `calculation/builtInVariables array-origin="0"` (ORIGIN), `convergence-tolerance` (TOL),
  `constraint-tolerance` (CTOL), `prn-precision`, `prn-col-width`.
- `calculation/calculationBehavior automatic-recalculation="true" …`, `units/currentUnitSystem name="si"`.
- `fileFormat save-numeric-results="true"` — результаты сохраняются в файл (нужно для чтения без Mathcad).

## Регион
```xml
<region region-id="7" left="36" top="200.25" width="108.75" height="12" align-x="45.75" align-y="210"
        show-border="false" show-highlight="false" is-protected="true" z-order="0"
        background-color="inherit" tag="r7"> CONTENT [<rendering item-idref="3"/>] </region>
```
- Координаты в пунктах (1/72″) от начала рабочей области; COM `Region.X/Y` — в пикселях (×4/3).
- **Порядок вычисления** — по точке выравнивания (`align-y`, затем `align-x`), слева направо, сверху вниз.
  Высокий результат-матрица начинается *выше* своей `align-y`, поэтому сортировать по `top` нельзя.
- `width/height/align-*` Mathcad пересчитывает при загрузке; при генерации можно ставить примерные,
  но регионы не должны перекрываться (иначе визуальная каша) — `xmcd.py relayout` раздвигает их по
  реальным размерам из пересохранённого файла (сходится за 1–2 прохода).
- `tag` — произвольная метка, видна через COM (`Region.Tag`) — удобно помечать регионы для поиска.
- `<rendering item-idref>` — PNG-картинка региона в binaryContent (кэш для просмотра); не обязательна.

### Виды CONTENT (частота в примерах qsheet)
| Элемент | Что это |
|---|---|
| `text` (6006) | текст: `<text use-page-width lock-width><p style="Normal" …>текст <b>/<i>/<f family size>…</p></text>`; кириллица — нормально |
| `math` (4485) | формула, см. `math-xml-catalog.md` |
| `plot` (231) | график: `<plot disable-calc="false" item-idref="N"/>` — всё в бинарном блоке N |
| `png` (769), `metafile`, `ole` (55) | картинки / OLE-объекты (item-idref) |
| `pageBreak` (691) | разрыв страницы |
| `area` (9) | сворачиваемая область: `<area name is-collapsed is-locked …>` c вложенными `<region>` |
| `component` (234) | компоненты (Excel, чтение файлов, скрипты, элементы управления): `<inputs>`/`<outputs>` + blob |
| `link`, `indexes`, `reference` | гиперссылки, индексы электронной книги, ссылка на другой лист (include) |

## Графики (binaryContent)
Блок графика — gzip + base64, внутри MFC-сериализация (`eqRegion`, `docRegion`, `tree`, `d2_graph_format`,
`graphData`, `axisFormat`, `trace2D`…). Выражения осей хранятся деревом записей
`[id]@@[op:2][00 00][flags][parent][00 00][payload]`, где идентификатор = `[len+1][len]имя\0`,
число = `[len+1][1][len]цифры\0`. Отсюда способ генерации: взять готовый график-шаблон и переименовать
идентификаторы (длина может меняться). Шаблоны в скилле (источник — графики из qsheet):
| Файл | Имена в дереве | Вид | Источник |
|---|---|---|---|
| `plot_xy.bin` | y, x | линия; матрица Y → по кривой на столбец | feat_04a #11 |
| `plot_pts.bin` | population, time | только маркеры (квадраты) | feat_07 #19 |
| `plot_fx.bin` | f, x, x | `f(x)` от `x` | feat_04a #70 |
| `plot_2fx.bin` | x, t, y, t, t | `x(t)` сплошная, `y(t)` пунктир | pendulum #28 |
| `plot_datafit.bin` | Y, f, z, X, z | маркеры `Y` от `X` + линия `f(z)` от `z` | linfitlo #15 |
Переименование — `xmcd.rename_plot_ids()` (по записям дерева, за один проход).
**Логарифмические оси**: в блоке `axisFormat` байт флагов оси X стоит через 10 байт после тега, оси Y — ещё
через 22 байта (перед ним байт `*`); бит `0x01` = логарифмическая шкала (найдено сравнением feat_04b #27/#29).
Оси автомасштабируются (числа пределов в блоке — только кэш последней отрисовки). Имена в графиках — ASCII.
Прочие виды (полярные, 3D, подписи осей, заголовки, цвета) — только если найти подходящий график-образец.
Размер графика хранится внутри блока (≈220×210 pt); атрибуты региона width/height на него почти не влияют.
Если имя переименовать, не обновив байт длины, Mathcad **молча выбрасывает** график при загрузке.

### Полная расшифровка блока графика (2026-09-25, реализовано в `scripts/mcplot.py`)
- **Дерево** (после `tree` + 17 байт заголовка): записи в прямом порядке `[id][40 40][op u16][00 00][side][parent]`,
  id с 6 подряд. Доп. байты: лист `0x0f02` → `00 00` + значение (идентификатор `[len+1][len]имя\0`, число
  `[len+1][01][len]цифры\0`); пустое место `0x0f00` → `00 00 00`; `0x4b95` (унарный минус) и `0x708e` (список
  аргументов) → `00` (у них только правый потомок). После узла без потомков — по байту `00` на каждого предка,
  завершённого через правые связи (корень не считается). Хвост: `[следующий id][00][02 00 00 00]`.
  **Номера узлов ≥ 0x40 (id, parent, хвост) пишутся с префиксом-экраном `40`**: 0x41 → `40 41` (в образцах Mathcad
  встречалось до 0x7f; ≥ 0x100 не проверялось). Без экрана график с ≥ 58 узлами молча выбрасывается при загрузке.
- Структура: `c119(корень){ c19f[Y]{ c19f{ c19f{пределы Y(верх, низ)}, c19f{маркеры} }, список Y }, Y2… } ,
  c19f[X]{ c19f{ c19f{пределы X}, маркеры }, список X } }`; список — `c30a` левоассоциативно; `f(v)` = `ce12(имя, 708e(арг))`.
- side: `0x40`/`0x80` (левый/правый) + у листьев `0x24` (имя), `0x34` (число, заданное пользователем), `0x36`
  (авто-значение). **Предел, заданный пользователем, — без бита 0x02**, иначе Mathcad его игнорирует (в т.ч. у
  узла минуса: шаблон 2fx имел `82` → отрицательный предел не применялся).
- `axisFormat` (+20 X, +42 Y; запись 21 байт + `2a`): [0] флаги `0x01` лог, `0x02` сетка, `0x04` числа на оси
  (сброс — чисел нет), `0x08` автомасштаб, `0x40` авто-сетка; **[9] число интервалов сетки** (0 = авто; работает при
  любых флагах, 2…99); [14..16] цвет сетки RGB (по умолчанию 00 ff 00).
- `graphData` (смещения от конца слова `graphData`): [15] бит 0 = легенда под графиком («trace 1»);
  **[23] стиль осей: 0 none, 1 boxed, 2 crossed**; [27]/[31] (int32) — ширина и высота графика (≈7 pt на единицу);
  `shpRect` — только кэш положения. Флага «Hide arguments» в [14]/[15] нет (не найден).
- Размер чисел на осях = размер стиля формул Variables/Constants листа (`mcsheet.build(..., font_size=14)`).
- `trace2D`: заголовок + 16 записей `29 [линия 0 нет,1 сплошная,2 точки,3 штрих,4 штрих-пунктир] [R G B]
  [флаги] {символ}{толщина}{тип} 01 [№] 01`; флаги `0x1f` = всё по умолчанию, бит 0 сброшен → следует байт символа
  (3 квадрат, 5 кружок…), бит 2 сброшен → байт толщины, бит 3 сброшен → байт типа.

## Результаты и ошибки в файле
См. `math-xml-catalog.md` → «Результаты». Ошибки вычислений в файл не записываются, только результаты
успешных вычислений (`<result>`), поэтому «пустой» `eval` без `<result>` после пересохранения = ошибка
или не вычислено.

## Экспорт HTML (для отчётов)
`SaveAs(path.htm, 3)` → `path.htm` + `path_images\IMGnnnn_*.PNG` + `filelist.xml`. Один `<div>` на регион
в порядке регионов файла (абсолютные координаты), текст — `<span class="Heading_1|Normal">` UTF-8,
формулы и графики — PNG 96 dpi. Масштаб окна (Window.Zoom) на картинки не влияет; крупнее картинки
получаются, если увеличить шрифты `mathStyles` (так делает `report.py`), но тогда подписи графиков тоже растут.
