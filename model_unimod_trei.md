# Разработка проектов в Unimod PRO 2 (ТРЭИ) (`model_unimod_trei.md`)

> Модуль прикладного слоя для создания и модификации проектов ПЛК TREI-5B в среде Unimod PRO 2 (МЭК 61131-3: FBD, ST, LD).
> Путеводитель по библиотеке — [`README.md`](README.md).
> Полная рабочая реализация и инструментарий скилла — [`skills/unimod-pro-trei/SKILL.md`](skills/unimod-pro-trei/SKILL.md).

---

## 1. Назначение и сфера применения

Модуль подключается при решении задач:
- Разработка и редактирование проектов автоматизации на контроллерах концерна ТРЭИ (ТРЭИ-5В-04/05);
- Создание программ, функций, функциональных блоков (POU) и пользовательских структур данных;
- Проектирование и синтез схем на языке функциональных блоковых диаграмм (FBD) через генерацию структуры `prog.json` (`assets/scripts/fbd_gen.py`);
- Автоматизированное построение словарей переменных и импорт конфигурации задач через текстовые спецификации (`import.prj`, `*.import.csv`);
- Управление средой разработки Unimod PRO 2 через скрипты автоматизации и Windows UI Automation (`assets/scripts/ui/`);
- Проверка синтаксиса, компиляция проекта (F9) и сборка исполняемого бинарного образа контроллера (`project.app`).

---

## 2. Архитектура формата и ключевые правила

Формат проекта Unimod PRO 2 представляет собой файловую структуру (JSON, CSV, XML, INI) в сочетании с бинарными словарями переменных `*.var`.

1. **Приоритет бинарного словаря `tags/global.var`:**
   - Файл `tags/global.var` является единственным источником истины для глобальных переменных. Текстовый файл `tags/global.csv` выступает лишь зеркалом и перезаписывается средой при сохранении. Повреждение или удаление `global.var` приводит к безвозвратной утрате глобального словаря.
2. **Хранение программного кода в base64:**
   - Исходный текст программ на языке ST и схем FBD хранится в закодированном виде внутри JSON-файлов соответствующих модулей. Файлы `.st` в каталоге проекта являются генерируемыми зеркалами.
3. **Обязательный цикл подтверждения изменений:**
   - Любая файловая модификация проекта становится легитимной только после выполнения цикла: **Открыть в IDE → Сохранить весь проект (Ctrl+Shift+S) → Собрать (F9)**.
4. **Резервирование перед началом работ:**
   - До внесения изменений создается полная копия папки проекта: `cp -r <project_dir> <project_dir>.bak-ГГГГММДД-ЧЧММСС`.

---

## 3. Инструментарий автоматизации

Скрипты и эталоны размещены в подкаталоге [`skills/unimod-pro-trei/assets/`](skills/unimod-pro-trei/):

| Компонент | Назначение |
|---|---|
| [`assets/skeleton/`](skills/unimod-pro-trei/assets/skeleton/) | Эталонная структура чистого проекта для быстрого развертывания с нуля |
| [`assets/scripts/fbd_gen.py`](skills/unimod-pro-trei/assets/scripts/fbd_gen.py) | Программная генерация схем FBD: размещение блоков по сетке, трассировка связей, контроль типов |
| [`assets/scripts/fbd_dump.py`](skills/unimod-pro-trei/assets/scripts/fbd_dump.py) | Декомпиляция и проверка логики FBD-схем, сопоставление со сгенерированным кодом ST |
| [`assets/scripts/fbd_diff.py`](skills/unimod-pro-trei/assets/scripts/fbd_diff.py) | Смысловое сравнение двух версий схем FBD с локализацией изменений |
| [`assets/scripts/manual.py`](skills/unimod-pro-trei/assets/scripts/manual.py) | Извлечение справочных разделов заводского руководства ТРЭИ по имени блока или функции |
| [`assets/scripts/ui/`](skills/unimod-pro-trei/assets/scripts/ui/) | Набор сценариев управления интерфейсом IDE и эмуляцией контроллера через UI Automation |

---

## 4. Справочные материалы

Перед разработкой алгоритмов обратитесь к специализированным руководствам скилла:
- Архитектурная карта структуры файлов: [`skills/unimod-pro-trei/references/file-format-notes.md`](skills/unimod-pro-trei/references/file-format-notes.md);
- Свод критических ограничений и ловушек: [`skills/unimod-pro-trei/references/known-issues.md`](skills/unimod-pro-trei/references/known-issues.md);
- Пошаговые рецепты типовых операций: [`skills/unimod-pro-trei/references/recipes.md`](skills/unimod-pro-trei/references/recipes.md);
- Библиотека 204 системных функциональных блоков: [`skills/unimod-pro-trei/references/fb-library.md`](skills/unimod-pro-trei/references/fb-library.md);
- Руководство по проектированию схем FBD: [`skills/unimod-pro-trei/references/fbd-guide.md`](skills/unimod-pro-trei/references/fbd-guide.md);
- Навигация по графическому интерфейсу среды: [`skills/unimod-pro-trei/references/gui-guide.md`](skills/unimod-pro-trei/references/gui-guide.md).
