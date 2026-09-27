# Конвертация Markdown в PDF (Маршруты Word / WeasyPrint)

Этот модуль регламентирует архитектуру, инструментарий и регламент компиляции технической документации и академических отчетов из формата Markdown (`.md`) в полиграфический PDF (`.pdf`).

Инструкция действует как прикладной инженерный стандарт для нейросетей и разработчиков при создании скриптов сборки, автоматизации экспорта отчетов по лабораторным работам, курсовым проектам, ТЗ, планам и архитектурным описаниям.

---

## ⚡ Обязательное предварительное согласование маршрута с пользователем

> [!IMPORTANT]
> **КРИТИЧЕСКИЙ ПРОТОКОЛ AI-АГЕНТА:**
> Перед началом конвертации любого документа из Markdown в PDF нейросеть **ОБЯЗАНА явно спросить у пользователя**, какой способ конвертации использовать, и предложить два варианта:
>
> 1. **(Рекомендуется по умолчанию) Двухстадийная конвертация через Word:**  
>    Сначала конвертируем `.md` в Word (`.docx`) по ГОСТ 7.32 (согласно [`doc_word_gost.md`](doc_word_gost.md)), **затем пользователь лично проверяет и подтверждает, что получился качественный Word-документ**, и только после этого Word конвертируется в `.pdf` через виртуальный принтер Microsoft Print to PDF (или Word COM API).
> 2. **Прямая конвертация через WeasyPrint / CSS Paged Media:**  
>    Markdown компилируется в HTML и сразу растеризуется в PDF движком WeasyPrint без участия Microsoft Word (быстрый автономный режим для легких справок, ТЗ и сред CI/CD Linux/Docker).
>
> **По умолчанию агент всегда рекомендует и предлагает именно Вариант 1 (через Word)**, так как сложные технические отчеты с формулами, многоуровневыми таблицами и оглавлениями требуют предварительного визуального контроля верстки в офисном пакете.

---

## 1. Сравнительная схема архитектурных маршрутов

```mermaid
graph TD
    MD["Исходный Markdown-документ (*.md)"]

    subgraph Route1["Маршрут № 1 (Рекомендуемый по умолчанию): Двухстадийный через Word"]
        PANDOC["Конвертер Pandoc + python-docx<br/>(Оформление по doc_word_gost.md)"]
        DOCX["Документ Word (*.docx)<br/>(Нативные OMML формулы, таблицы, стили)"]
        USER_CHECK{{"ОБЯЗАТЕЛЬНЫЙ КОНТРОЛЬ ПОЛЬЗОВАТЕЛЕМ:<br/>Убедиться, что Word получился хорошим"}}
        WORD_PRINT["Microsoft Print to PDF / Word COM API<br/>(doc.ExportAsFixedFormat / печать)"]
        PDF1["Итоговый эталонный PDF (*.pdf)<br/>(Академический стандарт, 100% верстка)"]

        MD --> PANDOC
        PANDOC --> DOCX
        DOCX --> USER_CHECK
        USER_CHECK -->|Подтверждение пользователя| WORD_PRINT
        WORD_PRINT --> PDF1
    end

    subgraph Route2["Маршрут № 2: Прямая автономная конвертация (WeasyPrint)"]
        PYMD["Парсер Python-Markdown<br/>(+ расширения tables, fenced_code, toc)"]
        CSS["CSS Paged Media Level 3<br/>(@page, маргинальные боксы)"]
        WP["Движок WeasyPrint<br/>(HTML/CSS -> PDF)"]
        PDF2["Автономный PDF (*.pdf)<br/>(Для CI/CD и легковесных справок)"]

        MD --> PYMD
        PYMD --> WP
        CSS --> WP
        WP --> PDF2
    end
```

---

## 2. Маршрут № 1: Конвертация через Word и Microsoft Print to PDF (Регламент)

### 2.1 Этап 1: Сборка `.docx` по ГОСТ 7.32
1. Сборка документа выполняется в строгом соответствии с модулем [`doc_word_gost.md`](doc_word_gost.md):
   - Поля: левое 30 мм, правое 15 мм, верхнее 20 мм, нижнее 20 мм (ширина полосы набора 165 мм).
   - Шрифт основного текста: Times New Roman 14 пт, межстрочный интервал 1,5, абзацный отступ 1,25 см, выравнивание по ширине.
   - Титульный лист: оформляется отдельной секцией по каноническому образцу `Отчет_ЛР3.docx` (`different_first_page_header_footer = True`), строго обычным начертанием (`bold=False` / `w:b="0"`) — полужирный шрифт запрещен. Номер страницы не проставляется. Место и год выпуска размещаются в нижнем колонтитуле первой страницы. ИИ обязан предварительно уточнить у пользователя согласие с формой титульника по умолчанию.
   - Структура и разрывы страниц: каждая новая глава (ГЛАВА 1, ГЛАВА 2 и т.д.) и структурные разделы («ЦЕЛЬ РАБОТЫ», «ВЫВОДЫ», «СПИСОК ИСПОЛЬЗОВАННОЙ ЛИТЕРАТУРЫ») начинаются строго с новой страницы (`page_break_before = True`). Подразделы идут подряд (`page_break_before = False`) с обязательным `keep_with_next = True`.
   - Оглавление: строго 14 пт (Times New Roman, обычное прямое начертание, одинарный интервал), нативное динамическое поле Word `TOC \o "1-2" \h \z \u` со сквозной нумерацией со 2-й страницы по образцу `Отчет_ЛР3.docx` (`ГЛАВА X НАЗВАНИЕ ГЛАВЫ` / `x.x. Название подглавы`). Обязателен принудительный сброс отступа первой строки `FirstLineIndent = 0` у стилей и абзацев оглавления, чтобы исключить паразитный сдвиг вправо на 1,25 см, наследуемый от `Normal`.
   - Рисунки: масштабируются на максимально доступный размер полосы набора (ширина 165 мм, высота пропорционально до 155 мм) для максимальной четкости графиков; рисунок и подпись строго на одной странице с атрибутом `keep_with_next = True` на абзаце изображения.
   - Таблицы: шрифт **по умолчанию строго 14 пт** (Times New Roman, как во всей работе; ИИ запрещено уменьшать кегль до 12 пт по умолчанию без предварительного разрешения/просьбы пользователя), переменные в шапке и данных курсивом, а индексы — строго нижним/верхним индексом (`w:vertAlign val="subscript"` / `val="superscript"`, *Y*~дин~, *t*~рег~, П~1~, *I*^2^), полное центрирование содержимого ячеек по вертикали и горизонтали, визуальный межабзацный отступ 12 пт после таблицы (`space_before = 12 pt` у следующего абзаца), обязательные свойства `tblHeader` (повтор шапки на каждой странице), `cantSplit` (запрет разрыва строк) и `keep_with_next = True` для первой строки (защита от отрыва шапки от таблицы).
   - Формулы: компилируются в нативные редактируемые формулы Word OMML (`m:oMath`) с сохранением математического наклона (курсива) переменных (*y*, *x*₁, *x*₂, *x*₃, *k*, *R*²), выравниванием по центру полосы и нумерацией у правого края; паразитное жирное начертание строго запрещено (в исходнике недопустимы `\boldsymbol`, `\mathbf` и заворачивание формул в `**...**`, на уровне Word OMML и COM гарантируется `Bold = False`).
   - Списки и перечисления: в исходном Markdown перед каждым списком обязательна пустая строка во избежание слияния элементов в сплошной текст при компиляции; размер шрифта списков в Word — строго 14 пт. При вложенных списках обязательно учитывается `w:ilvl`: уровень 0 (внешние номера `1., 2.`) с отступом `left_indent = 1.25 см`, уровень 1 (вложенные маркеры) с отступом `left_indent = 2.00 см`. Сырые текстовые дефисы (`- `) категорически запрещены — используются круглые маркеры Word (•).
   - Пошаговый алгоритм конвертации Markdown в Word через `pypandoc` и `python-docx` подробно документирован в [`doc_word_gost.md`](doc_word_gost.md).

### 2.2 Этап 2: Обязательная пауза и верификация пользователем
> [!CAUTION]
> **ЗАПРЕЩЕНО автоматически переходить к экспорту в PDF без одобрения пользователя.**
> 
> 1. Агент обязан сформировать `.docx`, сохранить его на диск и предоставить пользователю прямую кликабельную ссылку на файл (формата `[Название.docx](file:///путь)`).
> 2. Агент сообщает пользователю:  
>    *«Файл Word успешно сформирован. Пожалуйста, откройте его и убедитесь, что верстка, оглавление, формулы и таблицы отображаются корректно. Ожидаю вашего подтверждения для финального экспорта в PDF через Microsoft Print to PDF».*
> 3. Только после получения явного согласия пользователя («Word отличный, конвертируй в PDF») агент запускает печать/экспорт.

### 2.3 Этап 3: Экспорт Word в PDF (Microsoft Print to PDF / Word COM API)
Экспорт выполняется через автоматизацию MS Word COM API (или печать на системный принтер «Microsoft Print to PDF»):
- **Защита от зависания на кириллических путях:** метод `Documents.Open` в Word COM на Windows зависает при наличии кириллицы в пути к файлу. Документ обязательно копируется во временный каталог с ASCII-путем (`Path(tempfile.gettempdir())`), обрабатывается и сохраняется там, а затем готовый PDF и DOCX возвращаются в целевой каталог.
- Перед сохранением принудительно обновляются все поля документа и оглавления: `doc.Fields.Update()`, `doc.TablesOfContents(1).Update()`.
- Вызывается встроенный метод экспорта Word `ExportAsFixedFormat` с параметром `wdExportFormatPDF = 17` (обеспечивает качество виртуального принтера Microsoft Print to PDF с сохранением гиперссылок оглавления и векторных шрифтов).

```python
"""Эталонный экспорт Word в PDF через Word COM / Microsoft Print to PDF."""
import shutil
import tempfile
from pathlib import Path
import win32com.client as win32

def export_word_to_pdf(docx_path: Path, pdf_path: Path | None = None) -> Path:
    docx_path = docx_path.resolve()
    if pdf_path is None:
        pdf_path = docx_path.with_suffix(".pdf")
    else:
        pdf_path = pdf_path.resolve()
    
    # 0. Изоляция во временном ASCII-каталоге во избежание зависания Word COM на кириллице
    temp_dir = Path(tempfile.gettempdir())
    temp_docx = temp_dir / "_export_temp.docx"
    temp_pdf = temp_dir / "_export_temp.pdf"
    shutil.copy2(docx_path, temp_docx)
    
    word = win32.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        doc = word.Documents.Open(str(temp_docx))
        
        # 1. Принудительный сброс отступа оглавления и обновление полей
        for st_id in (-42, -43):  # wdStyleTOC1, wdStyleTOC2
            try:
                doc.Styles(st_id).ParagraphFormat.FirstLineIndent = 0
            except Exception:
                pass
        doc.Fields.Update()
        if doc.TablesOfContents.Count > 0:
            toc = doc.TablesOfContents(1)
            toc.Update()
            for p in toc.Range.Paragraphs:
                p.FirstLineIndent = 0
        
        # 2. Экспорт в PDF (wdExportFormatPDF = 17)
        doc.ExportAsFixedFormat(
            OutputFileName=str(temp_pdf),
            ExportFormat=17,
            OpenAfterExport=False,
            OptimizeFor=0,      # wdExportOptimizeForPrint (высокое качество печати)
            CreateBookmarks=1,  # wdExportCreateWordBookmarks (кликабельное оглавление)
        )
        doc.Close(False)
        shutil.copy2(temp_pdf, pdf_path)
        return pdf_path
    finally:
        word.Quit()
        for p in (temp_docx, temp_pdf):
            if p.exists():
                try:
                    p.unlink()
                except Exception:
                    pass
```

---

## 3. Маршрут № 2: Прямая автономная конвертация через WeasyPrint (CSS Paged Media)

### 3.1 Сфера применения и особенности WeasyPrint
Прямая конвертация через WeasyPrint применяется в автономных средах сборки (CI/CD, Linux, Docker-контейнеры), где отсутствует Microsoft Word, а также для оперативного экспорта небольших технических справок, планов и ТЗ:

| Критерий | WeasyPrint (Маршрут № 2) | Microsoft Word / Print to PDF (Маршрут № 1, рекомендованный) |
|---|---|---|
| **Предварительный контроль верстки** | Нет (сразу финальный PDF) | **Да (ручная инспекция `.docx` пользователем перед печатью)** |
| **Сложные математические формулы** | MathML / SVG плагины | **Нативный векторный OMML (редактируемые формулы Word по ГОСТ)** |
| **Академическое оглавление** | Сложные маргинальные CSS счетчики | **Встроенное поле Word `TOC` с идеальными точечными отточиями** |
| **Контроль разрывов страниц** | Свойства CSS Paged Media | **Свойства абзацев Word (`keepNext`, `cantSplit`, `tblHeader`)** |
| **Автономность в Linux / CI** | **Высокая (запуск через `uv run`)** | Требует установленный MS Word (Windows / macOS) |

### 3.2 Способы запуска WeasyPrint и окружение

#### 3.2.1 Изолированный запуск через `uv` (Рекомендуемый способ)
Утилита `uv` позволяет запускать конвертер без предварительной ручной установки зависимостей в системный Python:

```bash
uv run --with markdown --with weasyprint --with pygments python convert.py input.md -o dist/
```

Пакетная обработка группы файлов:
```bash
uv run --with markdown --with weasyprint --with pygments python convert.py docs/*.md -o pdf_out/ --css custom_style.css
```

#### 3.2.2 Стандартный запуск через виртуальное окружение Python
При интеграции в существующий проект или виртуальное окружение:

```bash
# Установка зависимостей
pip install markdown weasyprint pygments

# Запуск конвертации
python convert.py report.md -o build/
```

> [!NOTE]
> **Особенности работы WeasyPrint на Windows:**
> WeasyPrint использует библиотеки Pango, HarfBuzz и cairo для растеризации шрифтов и отрисовки векторной графики. Современные версии WeasyPrint (начиная с версии 60+) содержат необходимые бинарные зависимости в колёсах (wheels) для Windows. При возникновении ошибки загрузки библиотек DLL необходимо установить GTK3 для Windows или воспользоваться запуском внутри WSL2 / контейнера.

---

### 3.3 Эталонный скрипт прямой конвертации (`convert.py`)

Скрипт полностью автономен, строго следует стандартам [`code_python.md`](code_python.md), содержит аннотации типов, обработку относительных путей, подсветку синтаксиса кода и внедрение стилей.

```python
"""Универсальный конвертер Markdown-документов в PDF с поддержкой CSS Paged Media.

Модуль выполняет парсинг Markdown с расширениями (таблицы, листинги, подсветка кода)
и последующий рендеринг в PDF через движок WeasyPrint.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Sequence

import markdown
from weasyprint import CSS, HTML

__all__: list[str] = ["convert_markdown_to_pdf", "build_html_document"]

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Базовые встроенные стили печати (CSS Paged Media Level 3)
DEFAULT_CSS_CONTENT = """
@page {
    size: A4;
    margin: 20mm 15mm 20mm 20mm;
    @bottom-center {
        content: counter(page) " / " counter(pages);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        font-size: 9pt;
        color: #666;
    }
}

@page :first {
    @bottom-center {
        content: none;
    }
}

html, body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #24292e;
    background-color: #fff;
    margin: 0;
    padding: 0;
}

h1, h2, h3, h4, h5, h6 {
    color: #111;
    font-weight: 600;
    margin-top: 1.4em;
    margin-bottom: 0.6em;
    break-after: avoid;
    page-break-after: avoid;
}

h1 { font-size: 20pt; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
h2 { font-size: 16pt; border-bottom: 1px solid #eaecef; padding-bottom: 0.2em; }
h3 { font-size: 13pt; }
h4 { font-size: 11pt; }

p {
    margin: 0 0 0.8em 0;
    text-align: justify;
    orphans: 2;
    widows: 2;
}

a {
    color: #0366d6;
    text-decoration: none;
}

hr {
    border: 0;
    height: 1px;
    background: #e1e4e8;
    margin: 2em 0;
    break-after: page;
    page-break-after: always;
}

/* Листинги кода */
pre {
    background-color: #f6f8fa;
    border-radius: 4px;
    padding: 12px;
    overflow-x: auto;
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
    font-size: 9.5pt;
    line-height: 1.45;
    break-inside: avoid;
    page-break-inside: avoid;
    border: 1px solid #e1e4e8;
    white-space: pre-wrap;
    word-break: break-all;
}

code {
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
    font-size: 0.9em;
    background-color: rgba(27, 31, 35, 0.05);
    padding: 0.2em 0.4em;
    border-radius: 3px;
}

pre code {
    background-color: transparent;
    padding: 0;
    font-size: 1em;
}

/* Таблицы */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 1.2em 0;
    break-inside: auto;
    page-break-inside: auto;
    font-size: 10pt;
}

thead {
    display: table-header-group; /* Дублирует шапку таблицы при переносе на новую страницу */
}

tr {
    break-inside: avoid;
    page-break-inside: avoid;
}

th, td {
    border: 1px solid #dfe2e5;
    padding: 6px 12px;
    text-align: left;
}

th {
    background-color: #f6f8fa;
    font-weight: 600;
}

/* Изображения и плавающие блоки */
figure, img {
    max-width: 100%;
    height: auto;
    break-inside: avoid;
    page-break-inside: avoid;
}

figure {
    margin: 1.5em 0;
    text-align: center;
}

figcaption {
    font-size: 9pt;
    color: #555;
    margin-top: 0.5em;
}

blockquote {
    border-left: 4px solid #dfe2e5;
    color: #6a737d;
    padding: 0 1em;
    margin: 0 0 1em 0;
}
"""


def build_html_document(body_html: str, custom_css: str | None = None) -> str:
    """Оборачивает отрендеренный фрагмент Markdown в полноценный HTML5 документ.

    Args:
        body_html: Сгенерированное тело документа из Markdown.
        custom_css: Опциональные пользовательские CSS-стили.

    Returns:
        Сформированная HTML-страница со всеми стилями в секции head.
    """
    css_bundle = DEFAULT_CSS_CONTENT
    if custom_css:
        css_bundle += f"\n/* --- Custom Injected Styles --- */\n{custom_css}"

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <title>Markdown to PDF Export</title>
    <style>
{css_bundle}
    </style>
</head>
<body>
{body_html}
</body>
</html>
"""


def convert_markdown_to_pdf(
    input_file: Path,
    output_file: Path,
    custom_css_path: Path | None = None,
) -> None:
    """Выполняет конвертацию одного файла Markdown в PDF.

    Args:
        input_file: Путь к исходному файлу .md (UTF-8).
        output_file: Путь для сохранения итогового файла .pdf.
        custom_css_path: Опциональный путь к файлу дополнительных CSS стилей.

    Raises:
        FileNotFoundError: Если исходный файл или указанный CSS не найдены.
        ValueError: Если исходный файл имеет недопустимое расширение или пуст.
    """
    if not input_file.exists():
        msg = f"Исходный файл не найден: {input_file}"
        raise FileNotFoundError(msg)

    if input_file.suffix.lower() not in {".md", ".markdown"}:
        msg = f"Ожидается файл Markdown (.md), получено: {input_file.name}"
        raise ValueError(msg)

    md_content = input_file.read_text(encoding="utf-8")
    if not md_content.strip():
        msg = f"Исходный файл пуст: {input_file}"
        raise ValueError(msg)

    custom_css: str | None = None
    if custom_css_path is not None:
        if not custom_css_path.exists():
            msg = f"Файл стилей не найден: {custom_css_path}"
            raise FileNotFoundError(msg)
        custom_css = custom_css_path.read_text(encoding="utf-8")

    # Инициализация парсера Markdown с необходимыми расширениями
    md_extensions = [
        "tables",
        "fenced_code",
        "codehilite",
        "toc",
        "def_list",
        "attr_list",
    ]
    extension_configs = {
        "codehilite": {
            "guess_lang": False,
            "noclasses": True,  # Инлайновые стили для цветов подсветки кода
            "pygments_style": "default",
        },
    }

    body_html = markdown.markdown(
        md_content,
        extensions=md_extensions,
        extension_configs=extension_configs,
    )

    full_html = build_html_document(body_html=body_html, custom_css=custom_css)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    # base_url задается каталогом исходного файла для корректного поиска локальных картинок
    base_dir = str(input_file.parent.resolve())
    html_renderer = HTML(string=full_html, base_url=base_dir)
    html_renderer.write_pdf(target=str(output_file))

    logger.info("Успешно создан PDF: %s -> %s", input_file.name, output_file)


def main(argv: Sequence[str] | None = None) -> int:
    """Точка входа командной строки."""
    parser = argparse.ArgumentParser(
        description="Конвертация Markdown в PDF с поддержкой CSS Paged Media (WeasyPrint).",
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Один или несколько файлов Markdown (.md) для конвертации",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Каталог сохранения сгенерированных PDF (по умолчанию — рядом с исходником)",
    )
    parser.add_argument(
        "--css",
        type=Path,
        default=None,
        help="Путь к внешнему CSS-файлу для переопределения правил верстки",
    )

    args = parser.parse_args(argv)

    success_count = 0
    failure_count = 0

    for input_path in args.inputs:
        try:
            if args.output_dir:
                dest_file = args.output_dir / f"{input_path.stem}.pdf"
            else:
                dest_file = input_path.with_suffix(".pdf")

            convert_markdown_to_pdf(
                input_file=input_path,
                output_file=dest_file,
                custom_css_path=args.css,
            )
            success_count += 1
        except Exception as err:  # noqa: BLE001
            logger.error("Ошибка при обработке %s: %s", input_path, err)
            failure_count += 1

    logger.info("Конвертация завершена. Успешно: %d, с ошибками: %d", success_count, failure_count)
    return 1 if failure_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
```

---

## 4. Специфика верстки CSS Paged Media

### 4.1 Контроль разрывов страниц (Page Break Control)

WeasyPrint строго поддерживает свойства `break-inside`, `break-before` и `break-after` из спецификации CSS Paged Media Level 3:

```css
/* 1. Запрет отрыва заголовка от следующего за ним текста (Orphan Heading) */
h1, h2, h3, h4, h5, h6 {
    break-after: avoid;
    page-break-after: avoid;
}

/* 2. Запрет разрыва листинга кода или рисунка посередине блока */
pre, figure, .card, .callout {
    break-inside: avoid;
    page-break-inside: avoid;
}

/* 3. Принудительный перенос раздела на новую страницу */
.page-break, hr {
    break-after: page;
    page-break-after: always;
}

/* 4. Разрешение переноса длинных таблиц с сохранением шапки */
table {
    break-inside: auto;
}
thead {
    display: table-header-group; /* Повторяется вверху каждой страницы при переносе */
}
tr {
    break-inside: avoid; /* Запрещает разрыв отдельной строки таблицы пополам */
}
```

### 4.2 Маргинальные боксы страницы (`@page`)

CSS Paged Media делит область полей страницы на 16 маргинальных боксов:

```mermaid
graph TD
    subgraph Page["Анатомия страницы @page"]
        TL["@top-left"] --- TC["@top-center"] --- TR["@top-right"]
        ML["@left-middle"] --- CONTENT["ОСНОВНОЙ КОНТЕНТ<br/>(Body DOM)"] --- MR["@right-middle"]
        BL["@bottom-left"] --- BC["@bottom-center<br/>(Номера страниц)"] --- BR["@bottom-right"]
    end
```

Пример настройки колонтитулов и номеров страниц:
```css
@page {
    size: A4 portrait;
    margin: 20mm 15mm 20mm 20mm;

    @top-right {
        content: "Лабораторная работа №3";
        font-size: 8pt;
        color: #888;
    }

    @bottom-center {
        content: "Страница " counter(page) " из " counter(pages);
        font-size: 9pt;
    }
}

/* Титульный лист (первая страница) без колонтитулов */
@page :first {
    @top-right { content: none; }
    @bottom-center { content: none; }
}
```

---

## 5. Профили стилизации: Современный и ГОСТ 7.32

### 5.1 Профиль: Академический ГОСТ 7.32 (`gost_style.css`)
Используется для оформления лабораторных работ, пояснительных записок и курсовых проектов в связке с модулями [`doc_markdown.md`](doc_markdown.md) и [`doc_word_gost.md`](doc_word_gost.md).

```css
@page {
    size: A4 portrait;
    /* Поля по ГОСТ 7.32: левое 30 мм, правое 15 мм, верхнее 20 мм, нижнее 20 мм */
    margin: 20mm 15mm 20mm 30mm;

    @bottom-center {
        content: counter(page);
        font-family: "Times New Roman", Times, serif;
        font-size: 11pt;
        color: #000;
    }
}

@page :first {
    @bottom-center { content: none; }
}

html, body {
    font-family: "Times New Roman", Times, serif;
    font-size: 14pt;
    line-height: 1.5;
    color: #000;
    background-color: #fff;
}

/* Абзацы с красной строкой 1.25 см */
p {
    text-align: justify;
    text-indent: 1.25cm;
    margin: 0 0 0.4em 0;
    orphans: 2;
    widows: 2;
}

/* Заголовки по ГОСТ */
h1, h2, h3 {
    font-family: "Times New Roman", Times, serif;
    font-weight: bold;
    color: #000;
    text-align: center;
    text-indent: 0;
    break-after: avoid;
    page-break-after: avoid;
}

h1 { font-size: 14pt; text-transform: uppercase; margin-top: 1.5em; margin-bottom: 0.8em; }
h2 { font-size: 14pt; margin-top: 1.2em; margin-bottom: 0.6em; }
h3 { font-size: 14pt; margin-top: 1.0em; margin-bottom: 0.4em; }

/* Таблицы по ГОСТ: сплошные черные границы */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 1.2em 0;
    font-size: 12pt;
    line-height: 1.2;
}

th, td {
    border: 1px solid #000;
    padding: 5px 8px;
    text-align: left;
}

th {
    font-weight: bold;
    text-align: center;
    background-color: transparent;
}
```

### 5.2 Профиль: Современный инженерный отчет (`modern_clean.css`)
Используется для архитектурных документов, технических аудитов ([`doc_tech_audit.md`](doc_tech_audit.md)), регламентов и ТЗ. Характеризуется строгой неогротескной типографикой (Inter / Segoe UI), легкими фоновыми плашками листингов и акцентными цветовыми блоками.

---

## 6. Обработка графики и формул

### 6.1 Векторные схемы Draw.io (`*.drawio.svg`)
WeasyPrint нативно парсит формат SVG без растрирования. Диаграммы, экспортированные по правилам [`diagram_drawio.md`](diagram_drawio.md), сохраняют идеальную векторную резкость при любом увеличении PDF:

```markdown
<figure>
  <img src="schemes/system_architecture.drawio.svg" alt="Архитектура системы">
  <figcaption>Рисунок 1 — Структурная схема вычислительного контура</figcaption>
</figure>
```

> [!IMPORTANT]
> **Разрешение путей к ассетам (Base URL):**
> Для того чтобы локальные изображения корректно попадали в итоговый PDF, в функцию `HTML(..., base_url=...)` всегда передается абсолютный путь к каталогу исходного Markdown-файла. В самом Markdown пути указываются относительно этого файла.

### 6.2 Математические формулы LaTeX
Сам парсер Python-Markdown не компилирует формулы `$E = mc^2$`. Для их отображения в PDF применяются два инженерных подхода:

1. **Предварительный рендеринг в SVG:** формулы компилируются в автономные SVG-файлы и подключаются стандартным тегом `![Формула](math/eq1.svg)`.
2. **Расширение `markdown-katex`:**
   ```bash
   pip install markdown-katex
   ```
   В скрипте `convert.py` добавляется расширение `"katex"`, которое подставляет скомпилированный MathML/HTML, поддерживаемый WeasyPrint.

---

## 7. Чек-лист проверки и верификации готового PDF

Перед передачей сгенерированного документа пользователю или прикреплением к отчету агент выполняет проверку:

- [ ] **Отсутствие оторванных заголовков (Heading Orphans):** ни один заголовок `h1`-`h4` не находится внизу страницы без минимум двух строк последующего текста.
- [ ] **Целостность шапок таблиц:** таблицы, разрывающиеся на несколько страниц, имеют повторяющуюся строку заголовка (`thead`) в начале каждого нового листа.
- [ ] **Неразрывность строк таблиц:** ни одна строка таблицы (`tr`) не расщеплена пополам между страницами.
- [ ] **Форматирование листингов кода:** длинные строки кода оборачиваются (`white-space: pre-wrap;`), блоки `pre` не обрезаются по правому краю поля страницы.
- [ ] **Нумерация страниц:** титульный лист не содержит номера; страницы пронумерованы сквозным счетчиком формата `N` или `N / M`.
- [ ] **Векторная графика:** диаграммы SVG отмасштабированы по ширине полосы набора (`max-width: 100%`) и сохраняют векторную резкость при 400% зуме.
- [ ] **Шрифты и Юникод:** все кириллические символы отображаются корректным начертанием (нет артефактов ненайденных глифов или замены шрифта на дефолтный monospace).
