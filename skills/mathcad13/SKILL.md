---
name: mathcad13
description: Работа с Mathcad 13 (Mathsoft, 2005; папку установки находит scripts/find_mathcad.py) — создание расчётных листов .xmcd с нуля из текстового описания, пересчёт через COM, чтение и разбор готовых .xmcd/.mcd/.xmct (формулы, результаты, ошибки), подстановка других исходных данных, графики, экспорт и отчёты Word (.docx) по ГОСТ. Используй ВСЕГДА, когда речь о Mathcad, файлах .xmcd/.mcd/.xmct/.xmcdz, «расчётном листе», инженерном расчёте/курсовой/лабораторной «в маткаде», даже если пользователь просто просит «посчитать в Mathcad», «проверить расчёт», «поменять нагрузку и пересчитать» или «сделать отчёт из маткада». Перед работой прочитай references/known-issues.md; после задачи допиши новые находки в references/ и строку в references/session-log.md.
---

# Mathcad 13 — рабочий процесс

Mathcad 13 — 32-битное приложение 2005 года. Управляем им двумя путями:
1. **Файл** `.xmcd` — это XML (формулы в схеме Math20). Его можно генерировать и править напрямую (`scripts/xmcd.py`).
2. **COM** `Mathcad.Application` — открыть, пересчитать, получить значения/ошибки, сохранить/экспортировать
   (`scripts/mc.ps1`). Вычисляет только сам Mathcad — числа в файле без пересчёта могут быть устаревшими.

Каталог скилла — папка, где лежит этот `SKILL.md` (у каждого разработчика своя, ниже пути относительно неё).
Путь к Mathcad и к скриптам не зашит: его каждый раз находит `scripts/find_mathcad.py` (см. ниже).
Рабочие файлы пользователя — рядом с его исходными файлами или в папке, которую он назовёт; не в папке скилла
и не во временной папке сессии.

## В начале каждой задачи
0. Найди Mathcad: `python "<скилл>/scripts/find_mathcad.py"` → JSON. `dir` — папка установки, `tools` — полные пути
   к mc.ps1/xmcd.py/report.py/mcsheet.py (подставляй их в команды), `com.registered` — работает ли пересчёт.
   `ok: false` → выполни `hint`: не найден — спроси пользователя, где Mathcad 13, и задай `MATHCAD13_DIR`;
   нет COM — `mathcad.exe /regserver` от администратора. Без Mathcad доступны только `xmcd.py read/build`.
   В `others` — Mathcad 14/15/Prime: скилл с ними не работает, их файлы только читать (`xmcd.py read`).
1. Прочитай `references/known-issues.md` (грабли — обязательно) и последние записи `references/session-log.md`.
2. По типу задачи дочитай нужное:
   - пишешь/правишь формулы → `references/math-xml-catalog.md` (синтаксис, запрещённые имена), `references/units.md`;
   - нужна функция Mathcad → `references/functions.md` (375 функций по категориям);
   - что-то нестандартное через COM → `references/automation-api.md`;
   - структура файла, графики, настройки листа → `references/xmcd-format.md`;
   - «а умеет ли Mathcad X?» → `references/capabilities-report.md` (что проверено и как).

## Правила безопасности
- **Никогда не писать в папку установки Mathcad** (`dir` из find_mathcad.py, по умолчанию
  `C:\Program Files (x86)\Mathsoft\Mathcad 13`: примеры qsheet, шаблоны) — копировать к себе.
- Файл пользователя перед правкой — резервная копия `имя.bak-ГГГГММДД-ЧЧММСС.xmcd`; результат писать
  в новый файл (`имя_calc.xmcd`), перезаписывать оригинал только по явной просьбе.
- mc.ps1 открывает лист, но **всегда закрывает без сохранения** (mcDiscardChanges) — сохраняет только `-SaveAs`.
- Убивать можно только `mathcad.exe -Embedding`, запущенные нами (mc.ps1 делает это сам). Открытый пользователем
  Mathcad (без `-Embedding`) не трогать; если пользователь работает в GUI с тем же файлом — предупредить.
- После генерации/правки листа — обязательно пересчитать через mc.ps1 и проверить `error_count`
  и `region_count` (регион с неизвестным элементом Mathcad молча удаляет).

## Инструменты
Полные пути к скриптам — из `tools` в выводе find_mathcad.py (ниже `<скилл>` — каталог скилла).
Запуск из инструмента PowerShell: `& "<скилл>\scripts\mc.ps1" ...`
(перед чтением кириллицы: `[Console]::OutputEncoding=[Text.Encoding]::UTF8`);
из Bash: `powershell -NoProfile -ExecutionPolicy Bypass -File "<скилл>/scripts/mc.ps1" ...`.
mc.ps1 сам находит папку Mathcad тем же способом (`-Action info` показывает её в `install_dir`).

**`scripts/find_mathcad.py`** — поиск установки (`MATHCAD13_DIR` → COM `Mathcad.Application` → реестр Mathsoft →
запись установщика → Program Files), версия exe, зарегистрирован ли COM, пути к скриптам скилла; `--dir` — только папка.

**`scripts/mc.ps1`** — COM-драйвер, печатает JSON. Сам перезапускается в 32-битном PowerShell, таймаут, чистит процесс.
```
mc.ps1 -Action info                                   # версия, проверка что COM жив
mc.ps1 -Path calc.xmcd -SaveAs calc_out.xmcd          # пересчитать и сохранить копию с результатами
mc.ps1 -Path calc.xmcd -Regions [-Xml]                # список регионов + ошибки (код и текст)
mc.ps1 -Path calc.xmcd -Get "M.max,σ,v"               # значения (базовые СИ, без единиц)
mc.ps1 -Path calc.xmcd -Set "a=2;v=[1,2,3];W=[[1,2],[3,4]]" -Get y   # SetValue (перекрывается определениями в листе!)
mc.ps1 -Path calc.xmcd -SaveAs report.htm             # экспорт: .xmcd .xmcdz .xmct .htm .mcd (RTF нет)
mc.ps1 -Path old.mcd   -SaveAs old.xmcd               # конвертация старого бинарного формата
mc.ps1 -Path calc.xmcd -Meta "Title=…;Author=…" -SaveAs out.xmcd   # метаданные листа (кириллица ок)
```
Поля JSON: `ok, error, region_count, region_types, error_count, errors[] (i, tag, x, y, error_code, error_text, xml),
values{}, set{}, saved{}, metadata{}, recalc_s`.

**`scripts/xmcd.py`** — работа с XML (Python 3, только stdlib).
```
python xmcd.py read  file.xmcd [--xml]                # регионы читаемым текстом: формулы, результаты, текст, графики
python xmcd.py build spec.txt out.xmcd [--title T]    # лист из текстового описания (синтаксис ниже)
python xmcd.py relayout in.xmcd out.xmcd              # раздвинуть перекрытия по реальным размерам (после пересчёта)
python xmcd.py set in.xmcd out.xmcd "q=15 kN/m" "h.s=450 mm"   # заменить правую часть определения
python xmcd.py expr "y := x^2 + 1" [--inner]          # XML одной формулы (--inner — для MathInterface.XML)
```

**`scripts/report.py`** — отчёт Word: текстовые регионы → абзацы/заголовки Word, формулы и графики → картинки
(рендер Mathcad), A4, поля 30/15/20/20 мм, Times New Roman 14. Комментарии справа от формул — в той же строке.
```
python report.py calc.xmcd report.docx [--title "…"] [--size 14] [--math-zoom 1.4] [--scale 2.5] [--keep DIR]
```

**`scripts/mcplot.py` + `scripts/mcsheet.py`** — графики «как нарисованные вручную»: любое число кривых, зелёная
сетка, цвета/толщина/символы, пределы осей, крупный размер (формат блока расшифрован — `references/xmcd-format.md`).
```
mcsheet.build(spec_lines_with('@PLOT afh'), {'afh': dict(ys=['ImW', '0'], xs=['ReW', '-1'], xlim=(-3, 0.5),
              ylim=(-3, 0.5), size=(64, 60), traces=[dict(line='solid', color='red', weight=2),
              dict(line='none', color='black', symbol='o')])}, 'raw.xmcd')
mcsheet.recalc_layout('raw.xmcd', 'final.xmcd'); mcsheet.export_plots('final.xmcd', 'out_dir')  # {имя: png}
```
Параметры `make_plot`: `axes='boxed'|'crossed'|'none'`, `xgrids`/`ygrids` (число делений), `grid_color`;
`mcsheet.build(..., font_size=…)` — размер шрифта формул и чисел на осях.

**`scripts/mcfig.py`** — доводка PNG графика для отчёта: срезает подписи выражений Mathcad («ImW», «ReW, -1»),
оставляет числа у осей и рисует свои подписи осей и кривых (курсив Times, `_{}`/`^{}`, `[..]` — прямой шрифт),
стрелки, штриховку, точки; `logx` для логарифмической оси.
```
mcfig.finish('out_dir/afh.png', 'afh_final.png', xlim=(-3, 0.5), ylim=(-3, 0.5), xlabel='Re', ylabel='jIm',
             labels=[dict(text='W(jω)', x=-1.5, y=0.3, color=(255, 0, 0))])
```

## Линейный синтаксис спецификации (build) — кратко
```
# Заголовок 1 / ## Заголовок 2 / > обычный текст (кириллица — только в тексте и комментариях)
L.p := 6 m               // комментарий справа   (число+единица = произведение; .p — литеральный индекс)
q := 10 kN/m
M.max := q*L.p^2/8
M.max = kN*m             // вывод в заданных единицах; просто "M.max =" — в базовых
f(x) := x^3 - 2*x - 5    |  g :== 9.81 m/s^2 (глобальное)  |  i := 0..10  |  t := 0, 0.1..1
A := [2, 1; 1, 3]  v := [1; 2; 3]  v[i]  M[i, j]  col(M, j)  det(M)  transpose(M)  M^-1  sqrt(x)  abs(x)
sum(e, k, 1, n)  prod(…)  int(e, x, a, b)  diff(e, x[, n])  lim(e, x, a)  if(c, a, b)  vectorize(e)
Given / x^2 + y^2 == 25 / sol := Find(x, y)      (== — «жирное» равно для ограничений)
y''(t) + y(t) == 0 ; y(0) == 0 ; y'(0) == 1 ; y := Odesolve(t, 3)   (каждое — отдельной строкой после Given)
[xa; ya] := Odesolve([xa; ya], τ, 3)             (система ОДУ)   Minerr(x, y) — метод Левенберга по умолчанию
e -> simplify | e -> solve, x | e -> float, 20 | int(x^2, x) ->     (символьные вычисления)
W(s) -> invlaplace, s | e -> laplace, t | e -> series, x == 0, 5 | e -> convert, parfrac, x | e -> assume, a > 0
f(n) := prog { s <- 0; for k in 1..n { s <- s + k }; if s > 10: return 10; s }   (программа, можно многострочно)
σ = MPa @prec=2 zeros   |  v = @matrix   |  x = @sci prec=3      (формат числа; @matrix — весь вектор, не таблица)
@plot Y vs X [points]  |  @plot f(x) vs x  |  @plot f(t), g(t) vs t  |  @plot Yd, fit(z) vs Xd, z
   + logx / logy / loglog в конце;   // Рисунок 1 - подпись (появится под графиком)
> текст с **жирным**, *курсивом*, σ_{max}, м^{2}       ---  (строка из трёх дефисов = разрыв страницы)
!x := 5                                  (отключённая формула)
```
Полная таблица соответствий и тонкости — `references/math-xml-catalog.md`; пример — `examples/beam.txt`.

## Рецепты

**Новый расчёт с нуля.**
1. Написать spec (UTF-8) по образцу `examples/beam.txt`. Имена — с литеральными индексами (`F.1`, `σ.max`), без
   конфликтов со встроенными (`F A s m g L R c e` — единицы/константы; список — в math-xml-catalog.md).
   Нет `kPa` — определить `kPa := 1000*Pa`.
2. `xmcd.py build spec.txt s1.xmcd` → `mc.ps1 -Path s1.xmcd -SaveAs s2.xmcd` → проверить `error_count`/`errors`.
3. `xmcd.py relayout s2.xmcd s3.xmcd` → `mc.ps1 -Path s3.xmcd -SaveAs final.xmcd` → повторить relayout, пока
   не «0 overlap(s)» (обычно 1–2 прохода).
4. `xmcd.py read final.xmcd` — проверить результаты по смыслу (порядок величин, единицы) и показать пользователю.

**Разобрать готовый файл пользователя.**
1. Скопировать в рабочую папку (для `.mcd`: `mc.ps1 -Path x.mcd -SaveAs x.xmcd`).
2. `mc.ps1 -Path x.xmcd -Regions -SaveAs x_calc.xmcd` → ошибки с текстом; `xmcd.py read x_calc.xmcd` — все формулы и
   результаты свежего пересчёта. Числа из непересчитанного файла — только «как было сохранено».
3. Объяснять по регионам (номер, координата, формула, результат); ошибки — с кодом из `errors[]`.
4. Не открывается: «newer version» — это Mathcad 14/15 (пересчитать нельзя, но `xmcd.py read` читает формулы и
   сохранённые результаты); «Unknown Error» — скорее всего скриптовые объекты (ползунки) — убрать их из копии;
   `.mcdx` — Prime, не поддерживается. `Minerr` в чужих файлах с auto-method может врать — проверить атрибуты.

**Данные из файлов.** `READPRN("f.txt")` / `READFILE("f.csv", "delimited")` (десятичная точка!) /
`READFILE("f.xls", "Excel")` (только .xls, не .xlsx). Пути — от папки листа.

**Пересчитать с другими исходными данными.** `xmcd.py set in.xmcd tmp.xmcd "q=15 kN/m" ...` → `mc.ps1 -Path tmp.xmcd
-SaveAs out.xmcd -Get "..."`. (`-Set` в mc.ps1 годится, только если переменная в листе не определена.)

**Отчёт / курсовая в Word.** Готовый пересчитанный лист → `report.py final.xmcd отчёт.docx --title "…"`. Проверка:
Word COM `ExportAsFixedFormat(pdf, 17)` + PyMuPDF → PNG страниц → посмотреть. Нужен .docx по шаблону вуза — можно
дальше править через skill `docx`.

**Показать пользователю в самом Mathcad.** `Start-Process "путь\файл.xmcd"` (откроется GUI).

## Ключевые факты
- COM из 32-битного процесса; Region/MathInterface — только позднее связывание (InvokeMember).
- GetValue — базовые СИ без единиц; греческие имена в COM — `\s` для σ (mc.ps1 переводит).
- Порядок вычисления — по `align-y`/`align-x` регионов; матрицы в XML — по столбцам.
- Результаты сохраняются в файл (`<result>`), ошибки — нет (только через COM).
- Графики — бинарные; генерируем клонированием шаблонов (`templates/plot_*.bin`), имена в графиках ASCII.
- Нет: RTF через COM, оператор строки матрицы, Unicode в математике, единицы kPa/kJ/MN, чтение .xlsx,
  открытие Mathcad 14/15/Prime, листов со скриптовыми объектами.
- Mathcad проверяет XML по схеме: одно нарушение (например, `genfit` без `method`) — «файл повреждён» целиком.

## Пополнение скилла (обязательно в конце задачи)
- Новая грабля → `references/known-issues.md` (симптом → причина → что делать).
- Новая проверенная возможность/ограничение → строка в `references/capabilities-report.md`.
- Новая конструкция XML/синтаксиса → `references/math-xml-catalog.md` (+ поддержка в `xmcd.py`, если частая).
- Запись в `references/session-log.md`: дата, задача, что сделано, что нового.
- Скрипты менять аккуратно: после правки прогнать `examples/beam.txt` полным циклом (build → mc → relayout → read).
