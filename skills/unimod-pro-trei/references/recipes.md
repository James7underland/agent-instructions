# Unimod PRO 2 — пошаговые рецепты

Все рецепты проверены на версии 2.3.43.15. Перед стартом — резервная копия
каталога проекта.

Пути в примерах:
- IDE: `C:/Program Files/UnimodPRO2/Unimod.exe`
- скрипты управления IDE: `scripts/`

---

## Рецепт 0. Цикл применения изменений

Правка файлов сама по себе ничего не меняет. Всегда:

```powershell
# 1. открыть проект и прожать диалоги импорта
.\unimod_open.ps1 -Project "D:\prj\demo01\project.uprj"
# 2. сохранить (IDE перезапишет зеркала и словари)
.\unimod_save.ps1
# 3. собрать
.\unimod_build.ps1
# 4. закрыть
.\unimod_close.ps1
```

Проверка результата сборки: появился `app/project.app`.

---

## Рецепт 1. Создать проект с нуля (полностью скриптом)

Проверено целиком: получившийся проект открывается и собирается без ошибок.

### Шаг 1. Скелет

```bash
cp -r <skill>/assets/skeleton "D:/prj/demo01"
```

В `project.uprj` поставить `name` равным имени каталога:

```python
import json
d = json.load(open('project.uprj', encoding='utf-8'))
d['name'] = 'demo01'
open('project.uprj', 'w', encoding='utf-8', newline='\n').write(
    json.dumps(d, indent=4, sort_keys=True) + "\n")
```

### Шаг 2. Состав проекта — файл `import.prj` в корне

Переводы строк обязательно CRLF, все пять секций обязательны:

```
<PROGRAM>
main_prog,ST,
</PROGRAM>

<FUNCTION>
</FUNCTION>

<STRUCTED_UNIT>
motor,
</STRUCTED_UNIT>

<FBLOCK>
motor,run,ST,
</FBLOCK>

<CHILD_PROGRAM>
</CHILD_PROGRAM>
```

Открыть проект, подтвердить диалог «Добавить изменения?», сохранить, закрыть.
IDE создаст `tasks/main/main_prog/`, запись в `task.json`, структуру `motor`
с ФБ `run` в `structs.json` и зеркала в `types/`.

**Важно:** на этом заходе НЕ должно быть файлов `*.import.csv` — будет ошибка
(см. known-issues).

### Шаг 3. Словари и код — второй заход

Удалить `import.prj` (иначе диалог повторится) и положить:

**Локальный словарь программы** — `main_prog.import.csv` в корне проекта:

```
Name;Type;ADDR_MOD;Library;Length;Value;Attribute;FRD;Save;Access;MOD_BUS_type;MOD_BUS;EDU;Cold_start;Index;Is_Ar;Ar_count;Ar_period;Ar_filter;AlphaServerName;Comment
b_run;B;;;;0;0;;false;0;0;0;;;;false;0;0;0; ;Команда пуска
r_speed;R;;;;0;0;;false;0;0;0;;;;false;0;0;0; ;Уставка скорости
m1;U;;motor;3;;0;;false;0;;;;;;false;;;;;Экземпляр двигателя
```

Строка `m1` объявляет экземпляр структуры `motor`: `Library` — имя структуры,
`Length` — число её полей. Поля `m1.Speed`, `m1.Cmd`, … IDE развернёт сама.

**Словарь структуры и код её ФБ** — прямо в `types/structs.json`:

```python
import json, base64

def tag(name, uid, uid_type, local_offset, inout, comment):
    return {"attributes": {"access": 0, "alphaCategory": "", "alphaServer": "",
                           "hda": 8, "inout": inout, "local_offset": local_offset,
                           "offset": 0, "save": 8, "value": 0},
            "children": [], "comment": comment, "lib_id": 0,
            "name": name, "uid": str(uid), "uid_type": str(uid_type)}

s = json.load(open('types/structs.json', encoding='utf-8'))
motor = s['struct_defs'][0]
motor['tags'] = [tag('Speed',   900001, 3, 0, 1, 'Задание скорости'),
                 tag('Enabled', 900002, 1, 4, 2, 'Признак работы'),
                 tag('Cmd',     900003, 1, 5, 1, 'Команда включения')]

code = b"IF Cmd = true AND Speed > 0.0 THEN\r\n    Enabled := true;\r\nELSE\r\n    Enabled := false;\r\nEND_IF;"
motor['programs'][0]['text']['st'] = base64.b64encode(code).decode()

open('types/structs.json', 'w', encoding='utf-8', newline='\n').write(
    json.dumps(s, indent=4, sort_keys=True, ensure_ascii=False) + "\n")
```

`local_offset` считать вручную: BOOL занимает 1 байт, INTEGER и REAL — по 4.

**Код программы** — `tasks/main/main_prog/prog.json`:

```python
p = json.load(open('tasks/main/main_prog/prog.json', encoding='utf-8'))
p['text']['st'] = base64.b64encode(
    b"m1.Cmd := b_run;\r\nm1.Speed := r_speed;\r\nm1.run();").decode()
open('tasks/main/main_prog/prog.json', 'w', encoding='utf-8', newline='\n').write(
    json.dumps(p, indent=4, sort_keys=True, ensure_ascii=False) + "\n")
```

Поле `text.md5` не трогать — IDE его не проверяет.

Открыть, подтвердить диалоги, сохранить. `*.import.csv` будет потреблён и удалён.

### Шаг 4. Сборка

F9. Успех — появился `app/project.app` и активировались кнопки
«Загрузка / Отладка / Эмуляция».

---

## Рецепт 2. Добавить программу в существующий проект

1. `import.prj` с новой программой в секции `<PROGRAM>` (остальные секции пустые).
2. Открыть, подтвердить, сохранить, закрыть, удалить `import.prj`.
3. Порядок вызова поправить в `tasks/main/task.json`, массив `programs[]` —
   программы выполняются в порядке этого массива.
4. Локальный словарь — `<имя>.import.csv`, код — `prog.json`.

---

## Рецепт 3. Изменить код существующей программы / ФБ / функции

| Что | Где лежит код |
|---|---|
| программа | `tasks/main/<имя>/prog.json` -> `text.st` |
| ФБ структуры | `types/structs.json` -> `struct_defs[i].programs[j].text.st` |
| функция | `functions/functions.json` -> `programs[i].text.st` (и дубль в `functions/<имя>/prog.json`) |

```python
import json, base64
p = json.load(open(path, encoding='utf-8'))
print(base64.b64decode(p['text']['st']).decode('utf-8'))          # прочитать
p['text']['st'] = base64.b64encode(new_code_crlf_bytes).decode()  # записать
```

Текст — UTF-8 с CRLF. `prog.st` править бессмысленно, он перезапишется.
Исключение для программ верхнего уровня: `prog.import.st` при закрытом проекте
или «Импорт ST программ с диска» при открытом (Рецепт 10).
Для функции безопаснее править оба места (`functions.json` и `functions/<имя>/prog.json`)
одинаково.

---

## Рецепт 4. Добавить переменные

| Словарь | Способ |
|---|---|
| локальный словарь программы | `<имя_программы>.import.csv` в корне проекта |
| словарь данных структуры | `types/structs.json` -> `struct_defs[i].tags[]` |
| словарь функции (параметры) | `functions/functions.json` -> `programs[i].tags[]` |
| **глобальный** | **только GUI**: редактор словаря -> Импорт -> файл CSV |

`*.import.csv` работает для программ и дочерних программ (у дочерних сохраняется
`Attribute`: 1 — вход, 2 — выход). Для функции файл просто не будет потреблён —
параметры функции добавляются правкой `functions.json`.

**`*.import.csv` заменяет словарь целиком**, а не дописывает: класть в него все
переменные программы, старые и новые (подробно — Рецепт 10).

### Правило offset (иначе сборка упадёт)

У переменных словарей программ и функций `attributes.offset` — это глобальный
индекс, и он **должен быть уникальным по всему проекту**. Если поставить 0 или
повторить чужое значение, сборка падает с «Ошибка в адресации переменных».

Как выбрать свободный: посмотреть максимум в `tags/base.csv` (колонка `Offset`)
после очередного сохранения и продолжить с выравниванием — BOOL занимает 1 байт,
INTEGER и REAL по 4.

```python
import csv
rows = list(csv.DictReader(open('tags/base.csv', encoding='cp1251'), delimiter=';'))
free = max((int(r['Offset']) for r in rows), default=0) + 4
free += (-free) % 4          # выравнивание на 4
```

У членов структуры (`structs.json` -> `tags[]`) `offset` не используется —
там работает `local_offset`, а `offset` можно оставить 0.

Пункт меню «Отладка -> Переиндексация базы переменных» коллизию НЕ чинит.

### Добавить параметр функции

```python
import json
f = json.load(open('functions/functions.json', encoding='utf-8'))
fn = next(p for p in f['programs'] if p['name'] == 'clamp01')
fn['tags'].append({
    "attributes": {"access": 0, "alphaCategory": "", "alphaServer": "", "hda": 8,
                   "inout": 1,          # 1 = входной параметр
                   "local_offset": 0,
                   "offset": 32,        # уникальный! см. правило offset выше
                   "save": 8, "value": 0},
    "children": [], "comment": "Входное значение", "lib_id": 0,
    "name": "x", "uid": "920001", "uid_type": "3"})
open('functions/functions.json', 'w', encoding='utf-8', newline='\n').write(
    json.dumps(f, indent=4, sort_keys=True, ensure_ascii=False) + "\n")
```

Первый тег функции — всегда возвращаемое значение, его имя совпадает с именем
функции, `inout` = 2. Его создаёт `import.prj`, трогать не нужно.

Глобальный словарь скриптом не создаётся: он хранится в бинарном
`tags/global.var`, формат которого разобран не полностью. Если нужны глобальные
переменные — либо подготовить CSV и попросить пользователя сделать импорт через
GUI, либо взять за основу проект, где нужные глобальные переменные уже есть.

---

## Рецепт 10. Дочерняя программа, массивы, архивация — файлами

Проверено 2026-09-12 на `s2_lab`: собирается, в эмуляции считает правильно.

### Дочерняя программа

Два захода, как в Рецепте 1.

1. **Заход 1** — `import.prj` в корне (все пять секций, CRLF), в секции
   `<CHILD_PROGRAM>` строка `child_sq,ST,R,sim_main,` — имя, язык, буква типа
   выхода, родитель. Открыть, подтвердить, сохранить, закрыть и **удалить
   `import.prj` самому** — IDE его не удаляет. Результат:
   - каталог `tasks/main/sim_main/child_sq/` (`prog.json`, `prog.csv`, `prog.var`);
   - в `prog.json` родителя `"childPrograms": ["child_sq"]`;
   - в словаре дочерней — выходная переменная `child_sq` (атрибут 2) нужного типа.
2. **Заход 2** — словарь и код:
   - `child_sq.import.csv` в корне — входы с `Attribute=1`. Строку выходной
     переменной писать не нужно: импорт её всё равно не трогает;
   - код — `tasks/main/sim_main/child_sq/prog.json` → `text` =
     `{"md5": "<любое>", "st": "<base64>"}` (у новой дочерней `text` = `{}`);
   - вызов в коде родителя: `y := child_sq(a);`. Результат обязательно
     присвоить или использовать в выражении; вызывать можно только из родителя.
3. Открыть, сохранить, собрать.

### Массив в локальном словаре

В `<программа>.import.csv` — одна строка на массив, элементы IDE создаст сама:

```
l_buf;A;;R;[3];;0;;false;0;;;;;;false;;;;;Буфер
g_mat;A;;R;[2,3];;0;;false;0;;;;;;false;;;;;Матрица 2x3
```

`Type=A`, `Library` = буква типа элемента, `Length` = `[N]` или `[N,M]`.
Обращение в ST — `l_buf[2]`, `g_mat[1,2]`; индексы с нуля, выход за границу
останавливает приложение. `types/arrays.json` IDE дополнит сама.
Глобальный массив — только GUI (см. `gui-guide.md`).

### Архивация

Поля CSV: `Is_Ar` (`true`/`false`), `Ar_count` — размер буфера, `Ar_period` —
фильтр по времени (с), `Ar_filter` — фильтр по значению:

```
l_arch;R;;;;0;0;;false;0;0;0;;;;true;50;2;0.1; ;Архивируемая
```

Импорт их сохраняет; после сборки в `base.csv`:
`sim_main.l_arch;real;20;true;50;2;0.1;…`.

### Главное правило импорта словаря

`<программа>.import.csv` **заменяет** локальный словарь целиком. Класть
**полный** список: все строки текущего `prog.csv` плюс новые. Развёрнутые поля
структур (`<экземпляр>.<поле>`) можно опустить — хватит строки `Type=U`.
Иначе пропадут все остальные переменные программы (см. known-issues).

### Текст программы без правки base64

- **Проект закрыт:** положить полный текст в `tasks/main/<прог>/prog.import.st`
  (UTF-8, CRLF). При открытии IDE его забирает и удаляет, после Ctrl+Shift+S
  текст оказывается в `prog.json`.
- **Проект открыт:** поправить `prog.st` → «Инструменты → Экспорт/импорт →
  Импорт ST программ с диска» → окно «Программы были обновленны по
  измененным prog.st файлам» → OK → Ctrl+Shift+S.
- Оба способа работают **только для программ верхнего уровня**. `prog.st`
  дочерней программы игнорируется и при сохранении перезаписывается —
  её код писать в `prog.json`.

---

## Рецепт 11. Схема FBD файлами (без мыши)

Проверено 2026-09-12: схема, записанная скриптом в `prog.json`, открывается
редактором, рисуется, даёт код на ST, собирается и правильно считает в
эмуляции. Подробности и ловушки — `fbd-guide.md`.

### Шаг 1. Программа и словарь (два захода IDE)

Первый заход — `import.prj` создаёт FBD-программу (`<имя>,FBD,`), второй —
`<программа>.import.csv` наполняет её локальный словарь. В одном заходе
совмещать нельзя: `import.prj` вместе с `*.import.csv` даёт ошибку.

Экземпляр системного ФБ заводится тем же импортом словаря:

```
_TON_1;U;;TON;4;;0;;false;0;;;;;;false;;;;;Таймер по фронту
_TON_1.IN;B;;;;0;1;;false;0;0;0;;;;false;0;0;0; ;Пуск
_TON_1.PT;I;;;;0;1;;false;0;0;0;;;;false;0;0;0; ;Уставка, мсек
_TON_1.Q;B;;;;0;2;;false;0;0;0;;;;false;0;0;0; ;Готово
_TON_1.ET;I;;;;0;2;;false;0;0;0;;;;false;0;0;0; ;Текущее время
```

Строки экземпляра **любого** системного ФБ генератор строит сам по библиотеке
IDE — выводы, типы, `Length`:

```python
from fbd_gen import instance_csv_rows
rows = [r for r in open('tasks/main/logic/prog.csv', encoding='utf-8').read().splitlines() if r]
rows += instance_csv_rows('cnt1', 'CTU') + instance_csv_rows('alarm_delay', 'TON')
open('logic.import.csv', 'w', encoding='utf-8', newline='').write('\r\n'.join(rows) + '\r\n')
```

Буквы типов в словаре — только проверенные: B, I, R, T, M, U, A. С неизвестной
буквой (`Y`, `D`) IDE падает при открытии проекта.

### Шаг 2. Схема (проект закрыт)

```python
import sys; sys.path.insert(0, '<skill>/scripts')
from fbd_gen import Scheme

s = Scheme(dict_csv='tasks/main/logic/prog.csv')
s.chain('sum_real', '+', ['a_real', 'b_real'], line=5)       # sum := a + b
s.chain('alarm',    '>', ['sum_real', ('100.0', 'R')], line=10)

ton = s.fb('_TON_1', 'TON', [('IN','B'), ('PT','I')], [('Q','B'), ('ET','I')], 24, 15)
s.link(s.var('alarm', 2, 15), ton, 'B', dst_slot=0)
s.link(s.const('3000', 'I', 2, 16), ton, 'I', dst_slot=1)
s.link(ton, s.var('alarm_delayed', 44, 15), 'B', src_slot=0)

s.save('tasks/main/logic/prog.json')     # сам расставит sequence и проверит
```

Для библиотечного ФБ выводы можно не перечислять: `s.fb_lib('cnt1', 'CTU', 40, 3)`.
Ещё: `s.eni(fb)` — вызов ФБ по условию, `s.link(..., invert=True)` — NOT на
связи, `s.op('AND', 3, …)` — оператор на три входа (пишет `args`),
`s.op('INT_TO_REAL', 1, …, in_t='I', out_t='R')` — преобразование,
`s.comment('текст', col, line)`.

`save()` не запишет файл, если найдёт проблему: нет обязательного поля,
дубль `sequence`, связь на несуществующий блок, две связи в один вход, разные
типы на концах (кроме константы), неподключённый вход или выход оператора,
переменной нет в словаре, два блока одного экземпляра ФБ, оператор на 3+
входа без `args`. Неподходящую константу (`2` в REAL, `1` в BOOL) и цикл по
связям генератор не даст создать вовсе.

### Шаг 3. Обязательная сверка

Открыть проект → «Сборка → Редактор → Вывести код на ST» → убедиться, что
строк столько, сколько цепочек. IDE читает схему молча и молча выбрасывает
непонятое, поэтому пропущенная цепочка иначе не обнаружится: сборка пройдёт
успешно и без неё.

Прочитать схему (свою или чужую) без IDE:

```bash
python <skill>/scripts/fbd_dump.py tasks/main/logic/prog.json --blocks --links
```

---

## Рецепт 12. Правка схемы FBD мышью

Проверено 2026-09-13 (песочница `fbd_d`): связи и блоки встают точно при
масштабах 12×18, 16×24, 22×30, с прокруткой и при изменённом размере панелей.
Подробности — `fbd-guide.md` → «Мышь: `fbd_lib.ps1`».

Проект открыт (`unimod_open.ps1`), вкладка нужной FBD-программы активна.
Блоки адресуются по данным из **сохранённого** `prog.json`: блок, поставленный
мышью, появится там только после сохранения.

```powershell
. "<skill>\assets\scripts\ui\fbd_lib.ps1"
Set-UmTopmost | Out-Null
$path = "C:\prj\demo\tasks\main\logic\prog.json"

# 1. поставить блоки
Invoke-FbdPlace -Item level -Column 2 -Line 20                       # переменная
Select-FbdPalette 'Оператор'
Invoke-FbdPlace -Item 'Больше (>)' -Parent 'Сравнение' -Column 20 -Line 20 -TitleRows 1 -Pins 2
Select-FbdPalette 'Переменная'
Invoke-FbdPlace -Item alarm -Column 34 -Line 20
Save-FbdProject -WaitFile $path | Out-Null

# 2. провести связи по блокам из файла
$prog = Read-FbdProg $path
$gt = Get-FbdBlock $prog -Name '>' -Column 20 -Line 20
Invoke-FbdLink -Src (Get-FbdBlock $prog -Column 2 -Line 20) -Dst $gt -DstSlot 0
Invoke-FbdLink -Src $gt -Dst (Get-FbdBlock $prog -Column 34 -Line 20)

# 3. зафиксировать связи, сохранить и сверить
Save-FbdProject -WaitFile $path | Out-Null
Submit-FbdLinks -Prog (Read-FbdProg $path)   # без этого последние связи только нарисованы
Save-FbdProject -WaitFile $path | Out-Null
Assert-FbdFile $path -Links 2        # ожидаемое число связей в программе
Set-UmTopmost -Off | Out-Null
```

Константу для второго входа `>` мышью ставят значком-рукой (см. `gui-guide.md`),
через `fbd_lib` это пока не автоматизировано — проще дописать её файлом.

Одиночные команды без скрипта: `fbd_do.ps1 view | mode | link | place | save |
scroll | clear` (примеры — в шапке скрипта). `save` сначала фиксирует связи
толчком, потом сохраняет и печатает число связей в файле.

Связь, проведённая мышью, попадает в модель IDE только после следующей правки
блока (проверено 2026-09-14) — поэтому шаг `Submit-FbdLinks` обязателен.

---

## Рецепт 13. Правка чужой схемы FBD

Проверено 2026-09-13: схема `project_FBD` (6 блоков, ни одной связи, сборка
невозможна) доведена до рабочей — присваивание, `GET_CRC_FB`, `OR` → `TON` с
выходами в новые переменные; сборка прошла, эмуляция запустилась.

```bash
cp -r "<проект>" "<проект>_edit"                              # 1. копия
cp tasks/main/<прог>/prog.json prog.before.json
python <skill>/scripts/fbd_dump.py tasks/main/<прог>/prog.json --blocks --links   # 2. разбор
```

```python
# 3. новые переменные — полным словарём (импорт заменяет словарь)
from fbd_gen import Scheme, var_csv_row
rows = [r for r in open('tasks/main/program_0001/prog.csv', encoding='utf-8').read().splitlines() if r]
rows += [var_csv_row('ton_q', 'B', comment='Таймер отработал'), var_csv_row('crc_val', 'I')]
open('program_0001.import.csv', 'w', encoding='utf-8', newline='').write('\r\n'.join(rows) + '\r\n')
# заход IDE: открыть -> сохранить -> закрыть; проверить, что строки дошли до prog.csv
```

```python
# 4. правка схемы (проект закрыт)
s = Scheme.load('tasks/main/program_0001/prog.json')
ton = s.one('_TON_1.TON')
s.move(ton, column=35, line=23)
s.link(s.one('OR'), ton, 'B', dst_slot=0)
s.link(s.const('2000', 'I', 28, 24), ton, 'I', dst_slot=1)
s.link(ton, s.var('ton_q', 50, 23), src_slot=0)
s.save('tasks/main/program_0001/prog.json')
```

```bash
python <skill>/scripts/fbd_diff.py prog.before.json tasks/main/program_0001/prog.json   # 5. дифф
```

6. Открыть проект → `Get-FbdStCode` → `fbd_dump.py prog.json --check-st st.txt`
   → сборка → эмуляция. 7. Правили ещё и мышью — `fbd_do.ps1 save` и повторить
   дифф. Если `fbd_dump.py` ещё до правки писал «порядок в файле не тот, что IDE
   назначит», первая правка мышью этот порядок поменяет — решить заранее.

---

## Рецепт 14. Большая схема FBD и несколько программ

Проверено 2026-09-14 (песочница `fbd_h`): 3, 8 и 21 канал аварий по уровню
(60, 147, 402 блока) — сгенерированы, открыты, код IDE совпал со схемой,
сборка, эмуляция; обмен между программами через `программа.переменная` и через
глобальную переменную.

### Шаг 1. Программы и словари (два захода IDE, см. Рецепт 11)

```python
from fbd_gen import var_csv_row, instance_csv_rows
rows = [var_csv_row('ack', 'B', '0', 'Квитирование'), var_csv_row('any_alm', 'B')]
for k in range(1, n + 1):
    rows += [var_csv_row('lvl_%d' % k, 'R', '50'), var_csv_row('hi_%d' % k, 'B'),
             var_csv_row('alm_%d' % k, 'B'), var_csv_row('lat_%d' % k, 'B')]
    rows += instance_csv_rows('dly_%d' % k, 'TON')      # свой экземпляр на каждый блок ФБ
```

### Шаг 2. Схема таблицей: объект — строки, стадия — полоса

```python
from fbd_gen import Scheme, K, Op
s = Scheme(dict_csv='tasks/main/alarms/prog.csv')
s.comment('Аварии по уровню', 2, 1)
for k in range(1, n + 1):
    line = s.next_line
    s.expr('hi_%d' % k, ('>', 'lvl_%d' % k, K('90.0', 'R')), line=line)
    bottom = s.next_line
    s.fb_call('dly_%d' % k, 'TON', line=line, column=45,
              ins={'IN': 'hi_%d' % k, 'PT': K('3000', 'I')}, outs={'Q': 'alm_%d' % k})
    s.expr('lat_%d' % k, ('AND', ('OR', 'alm_%d' % k, 'lat_%d' % k), '!ack'), line=line, column=88)
    s.next_line = max(bottom, s.next_line)
s.expr('any_alm', Op('OR', *['lat_%d' % k for k in range(1, n + 1)]), line=s.next_line)
for w in s.save('tasks/main/alarms/prog.json'):     # ошибки — исключение, здесь предупреждения
    print(w)
```

Стадии одного канала стоят на одной строке и выполняются слева направо; сводка
внизу выполняется последней. Поле больше 500 строк — `s.lines = 1000` до `save()`.

### Шаг 3. Сверка машиной

```powershell
. "<skill>\assets\scripts\ui\fbd_lib.ps1"
Get-FbdStCode | Out-File -Encoding utf8 st.txt     # вкладка схемы активна
```

```bash
python <skill>/scripts/fbd_dump.py tasks/main/alarms/prog.json --check-st st.txt
```

«код IDE совпадает со схемой в файле (148 операторов)» — IDE прочла всё.

### Шаг 4. Обмен между программами

```python
s.expr('ack', 'alarms.any_alm', line=s.next_line)   # читать переменную программы alarms
s.expr('g_any', 'any_alm', line=s.next_line)        # писать глобальную (заведена в GUI)
```

`fbd_gen.py` находит тип по `tasks/*/alarms/prog.csv` или `tags/global.csv` и
ставит нужные `dict`/`mode`. Порядок программ в цикле — `task.json → programs`.

---

## Рецепт 17. Релейная цепь LD и элементы без списка

Проверено 2026-09-18 (`fbd_k`): сборка и эмуляция.

```python
busL = s.bus('left', line=4, column=2)           # у шины три вывода: три цепи
busR = s.bus('right', line=4, column=60)
ct = s.contact('a', line=4, column=16, kind='direct')    # 'inv' | 'N' | 'P'
cl = s.coil('q1', line=4, column=40, kind='direct')      # + 'R' | 'S'
s.link(busL, ct, 'B', src_slot=0); s.link(ct, cl, 'B'); s.link(cl, busR, 'B', dst_slot=0)

s.link(s.var('flag_j', 2, 12), s.jump('skip_here', line=12, column=20), 'B')
s.label('skip_here', line=17, column=2)          # пропуск цепочек между прыжком и меткой
```

Мышью элементы без списка (константа, метка, прыжок, шина, соединение) ставятся
перетаскиванием значка-руки:

```powershell
Invoke-FbdPlaceHand -Palette 'Константа' -Kind 'целая' -Value '12' -Column 10 -Line 5
Invoke-FbdPlaceHand -Palette 'Метка' -Value 'skip_here' -Column 2 -Line 12
Invoke-FbdPlaceHand -Palette 'Шина' -Kind 'Левая  силовая шина' -Column 2 -Line 4
```

Результат у метки, шины и прыжка проверять по файлу: пиксельный детектор их не
видит.

---

## Рецепт 16. Структуры, дочерние программы и массивы на схеме

Проверено 2026-09-18 (`fbd_j`): сборка и эмуляция, значения совпали с ST.

### Шаг 1. Словарь программы (импорт, Рецепт 11)

```
t2;U;;tank;9;;0;;false;0;;;;;;false;;;;;Экземпляр структуры
buf;A;;R;[4];;0;;false;0;;;;;;false;;;;;Локальный массив
arr3;A;;R;[2,2,2];;0;;false;0;;;;;;false;;;;;Трёхмерный массив
byte_v;K;;;;0;0;;false;0;0;0;;;;false;0;0;0; ;Байт (буква K)
dbl_v;N;;;;0;0;;false;0;0;0;;;;false;0;0;0; ;Дв.точности (буква N)
```

Поля структуры и элементы массива IDE развернёт сама. Индекс элемента на схеме
может быть переменной: `abuf[idx]`.

### Шаг 2. Дочерняя программа — два захода

`import.prj` с `<CHILD_PROGRAM> ch_lim,ST,R,fbd_x,` (имя, язык, тип выхода,
родитель), затем `ch_lim.import.csv` с параметрами — **`Attribute 1`**, иначе у
блока на схеме не будет входов. Код дочерней — в её `prog.json` (`text.st`,
base64); `prog.st` у дочерних игнорируется.

### Шаг 3. Схема

```python
s = Scheme(dict_csv='tasks/main/fbd_x/prog.csv')
s.struct_call('t2', 'calc', line=3,
              ins={'Level_pct': 'sim_main.t1.Level_pct', 'Area_m2': K('3.0', 'R'),
                   'H_max_m': K('5.0', 'R'), 'SP_hi': K('80.0', 'R'), 'SP_lo': K('20.0', 'R')},
              outs={'Volume_m3': 's_vol', 'Alarm_hi': 's_alm'})
s.child_call('ch_lim', line=s.next_line, ins={'x': 'x_in'}, out='y_lim')
s.expr('buf[0]', 's_vol', line=s.next_line)                 # элемент массива — обычная переменная
s.expr('buf[2]', 'g_real[0]', line=s.next_line)             # элемент глобального массива
s.expr('arr_sum', Op('+', 'buf[0]', 'buf[1]', 'buf[2]'), line=s.next_line)
s.save('tasks/main/fbd_x/prog.json')
```

Ещё: `s.struct_fields('t2', line, column)` — блок со всеми полями (запись во
вход, чтение с выхода), `s.struct_pin('t2', …)` + связь — копия структуры
целиком (IDE развернёт в присваивание всех полей).

### Шаг 4. Сверка

`Get-FbdStCode` → `fbd_dump.py prog.json --check-st st.txt`: разборщик понимает
и метод структуры, и дочернюю программу, и копию структуры.

---

## Рецепт 15. Сверить новую схему с эталоном в эмуляции

Когда логика уже есть на ST (или в чужом проекте) и её переписывают на FBD,
сверять глазами нечего: нужно, чтобы совпадали значения в каждом цикле. Приём —
положить обе программы в одну задачу и считать расхождение прямо на схеме
(проверено 2026-09-18 на `tank_sim`: модель уровня, функция, две аварии).

1. Копия проекта, новая FBD-программа в той же задаче **после** эталонной
   (`import.prj`, затем словарь — Рецепт 11). Порядок в `task.json` — тот же
   цикл, значения эталона уже посчитаны.
2. В схеме читать переменные эталона по префиксу: `sim_main.h_sim_m`,
   `sim_main.t1.Level_pct` — блок переменной `dict 0`, генератор ставит сам.
3. Считать расхождения и копить их защёлкой — иначе разовое расхождение между
   двумя чтениями словаря будет не видно:

```python
s.expr('d_pct', ('-', 'pct', 'sim_main.t1.Level_pct'), line=l, column=58)
s.expr('diff_hi', ('XOR', 'a_hi', 'sim_main.t1.Alarm_hi'), line=l2, column=100)
s.expr('bad_num', ('>', ('+', ('ABS', 'd_pct'), ('ABS', 'd_m')), K('0.0', 'R')), line=l3, column=100)
s.expr('err_hold', ('OR', 'diff_hi', 'diff_lo', 'bad_num', 'err_hold'), line=l4, column=100)
```

4. Сборка, эмуляция: открыть словари обеих программ **до** входа в эмуляцию,
   прогнать полный цикл процесса (у `tank_sim` — период синусоиды 60 с) и
   смотреть `err_hold`. Ноль расхождений за период = логика повторена точно.
5. Уставки, по которым эталон принимает решения, стоит на время сверки сдвинуть
   в рабочую зону (в `tank_sim` — `LIM_HI`/`LIM_LO` и `init_done := false`),
   иначе аварии не сработают ни в одной версии и сверять будет нечего.

---

## Рецепт 5. Прочитать проект (аудит)

```python
import json, base64, csv

# состав проекта
print(open('proj_structure.prj', encoding='utf-8').read())

# порядок вызова программ и период задачи
t = json.load(open('tasks/main/task.json', encoding='utf-8'))
print(t['cycle'], t['programs'])

# код всех программ
import glob, os
for p in glob.glob('tasks/main/*/prog.json'):
    d = json.load(open(p, encoding='utf-8'))
    print('---', d['name'])
    print(base64.b64decode(d['text']['st']).decode('utf-8', 'replace'))

# структуры и их ФБ
s = json.load(open('types/structs.json', encoding='utf-8'))
for st in s['struct_defs']:
    print(st['name'], [x['name'] for x in st['tags']],
          [pr['name'] for pr in st['programs']])

# глобальный словарь (зеркало; актуально сразу после сохранения)
rows = list(csv.DictReader(open('tags/global.csv', encoding='utf-8'), delimiter=';'))
```

Помни: `global.csv` актуален только на момент последнего сохранения из IDE.

---

## Рецепт 6. Конфигурация контроллера

Всё в `configuration.json` — чистый JSON, правится напрямую:

- `controllers[0].typeMaster` — тип мастер-модуля (в разобранных проектах `77`).
- `controllers[0].net_eth1`, `net_netMask1`, `net_gateway` — сетевые настройки,
  применяются после загрузки приложения в ПЛК.
- `controllers[0].watchdogTime`, `runModeParam_*` — режим исполнения.
- `controllers[0].communicationLines[]` — линии связи ST-BUS и модули ввода-вывода.
- `modbus[]` — задачи Modbus: адрес, порт, функция, диапазоны, привязка к
  переменным (`beginReadVariableLocal`, `writeVariablesCount`, `diagVariable`).
- `opc[]` — параметры OPC-сервера.

Параметры подключения IDE к ПЛК (для загрузки/отладки) — отдельно, в
`settings.ini`, секция `[connectionPLC]`.

---

## Рецепт 7. Архив проекта

`*.ua2` — ZIP с шифрованием, распаковать сторонними средствами не выйдет.
Упаковка/распаковка — только через меню «Файл -> Архив проекта».
При каждом сохранении IDE сама обновляет `project.ua2` в корне проекта —
это удобная точка отката, но прочитать её снаружи нельзя.

---

## Рецепт 9. Распаковать `*.ua2` (архив проекта)

Архив зашифрован (ZipCrypto), сторонними средствами не открывается —
только через IDE. Меню мышью не кликается надёжно из-за DPI, поэтому идём
клавиатурой.

1. Запустить Unimod **без проекта** (просто `Unimod.exe`), дождаться главного окна.
2. Кликнуть меню «Файл» — логические координаты примерно `(27, 41)`.
3. Клавиатурой: `{DOWN}` ×6 → подсветится «Архив проекта»
   (стрелки останавливаются и на неактивных пунктах, поэтому считать надо все:
   Создать / Открыть / Закрыть / Удалить / Недавние / Архив).
4. `{RIGHT}` — откроется подменю, `{DOWN}` — «Распаковать проект из файла»,
   `{ENTER}`.
5. В файловом диалоге **напечатать полный путь** к `.ua2` (поле «Имя файла»
   уже в фокусе) и `{ENTER}`.
6. В окне «Сохранить распакованный проект»: `^a`, `{DEL}`, ввести имя проекта,
   `{ENTER}`. Путь по умолчанию — `Documents/UnimodPRO2/`; сменить его можно
   только кнопкой «...», текст туда не печатается.

Перед каждым шагом полезно снимать скриншот и убеждаться, что подсвечен нужный
пункт: вслепую жать `{ENTER}` в меню «Файл» опасно — рядом «Удалить проект».

Что лежит внутри архива: полный слепок каталога проекта, включая `app/`
(результат сборки) и вложенные `project.ua2` / `project_1.ua2` — авто-архивы,
которые IDE создаёт при сохранении. Из-за вложенности архив заметно больше
самого проекта.

---

## Рецепт 8. Сборка упала — что делать

1. **Не нажимать Enter вслепую.** Первый диалог после неудачной сборки —
   «Упаковать проект и отправить разработчику по электронной почте…?», и кнопка
   по умолчанию там «Да». Отвечать ESC. Второй диалог («Исправить обнаруженные
   ошибки?») — тоже ESC. `unimod_build.ps1` делает это сам.
2. Смотреть вкладку **«Список ошибок»** внизу главного окна: номер, описание,
   источник, строка, столбец, категория.
3. Типовые причины при генерации проекта скриптами:

| Ошибка | Причина | Лечение |
|---|---|---|
| «Ошибка в адресации переменных», источник «Ошибка в базе» | у двух переменных совпал `attributes.offset` | проставить уникальный offset, см. Рецепт 4 |
| переменная не найдена | забыт `*.import.csv`, или он не был потреблён (для функции он не работает) | проверить, что файл исчез после открытия проекта |
| синтаксис ST | текст записан не в UTF-8/CRLF или битый base64 | перечитать `text.st` через base64 и сверить |

4. Полезно смотреть `tags/base.csv` — это то, что реально ушло компилятору
   (кодировка CP1251): имена, типы и назначенные offset всех переменных.

---

## Рецепт 18. Проверить поведение системного ФБ в эмуляции

Зачем: руководство описывает алгоритм словами, а проверять надо числами.
Приём — «сценарий на ST + метки стадий + один заход в эмуляцию».

### Шаг 1. Что обещает руководство

```bash
python scripts/manual.py HYSTER          # раздел целиком
python scripts/manual.py --example TON   # только пример вызова
```

В примерах руководства есть готовые числа (`SETFIELD(2024, 5, 8, 589)` →
`OUT = 1960`) — их и стоит воспроизводить: сверка получается однозначной.

### Шаг 2. Словарь и сценарий (проект закрыт)

```python
from fbd_gen import instance_csv_rows, var_csv_row
rows = [HEAD] + [var_csv_row('z_getfield', 'I', comment='ожидание 29')]
rows += instance_csv_rows('gfl1', 'GETFIELD')       # экземпляр + все его поля
open(root + '/t1.import.csv', 'w', encoding='utf-8', newline='\r\n').write('\n'.join(rows) + '\n')
```

Сценарий — в `tasks/main/<программа>/prog.import.st` (UTF-8, CRLF). Счётчик
циклов и метки стадий обязательны:

```
n := n + 1;
z_stage := 1;
gfl1.GETFIELD(2024, 3, 7, FALSE);
z_getfield := gfl1.Q;
z_stage := 2;
```

Аргументы позиционные, в порядке входов из `fb_info('GETFIELD')['inputs']`.
Допустимы литералы (`b#5`, `d#1711021435000.0`, `'Hello'`), элементы массива,
целые массивы (для выводов «ссылка на массив») и выражения (`n >= 3`).
Период задачи задаётся в `tasks/main/task.json` → `cycle` (100 мс удобно:
такты легко считать).

### Шаг 3. Заход в IDE

```powershell
.\unimod_open.ps1 -Project <...>\project.uprj   # импорт словаря и текста
.\unimod_save.ps1
.\unimod_build.ps1 -ProjectDir <...>
.\ui\um_emul.ps1 -Action dict -Prog t1          # словарь открыть ДО эмуляции
.\ui\um_emul.ps1 -Action run -WaitSec 12 -Out r.txt
```

`-Action run` войдёт в эмуляцию, подождёт, прочитает **весь** словарь
постранично и выйдет. Значения — в `r.txt` строками `имя=значение`.

### Шаг 4. Чтение результата

- `z_stage` доросла до последней метки → программа отработала цикл целиком.
- Нули у дальних переменных при недоросшей `z_stage` — это чтение, а не
  исполнение (см. known-issues).
- Проверять в первую очередь **единицы**: `INTEG` интегрирует в секундах,
  `LRATE` ограничивает в единицах в секунду, таймеры — в миллисекундах.

### Что стоит проверять за один заход

До 25 блоков в одном сценарии проходят спокойно. Экземпляры лишних блоков
можно оставлять в словаре — на сборку и скорость это не влияет.
