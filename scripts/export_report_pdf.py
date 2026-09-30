# -*- coding: utf-8 -*-
"""Автономный скрипт полиграфического экспорта DOCX в PDF через MS Word COM API.

Реализует защищенный маршрут:
- Изоляция во временном ASCII-каталоге (защита от зависания Word COM на кириллических путях Windows).
- Принудительное обновление полей документа и динамического оглавления.
- Экспорт через ExportAsFixedFormat (wdExportFormatPDF = 17, OptimizeForPrint, CreateWordBookmarks).
- Возврат готового PDF в целевую директорию.

Использование из командной строки:
    python scripts/export_report_pdf.py --input Отчет.docx
    python scripts/export_report_pdf.py -i Отчет.docx -o Отчет_ГОСТ.pdf

Использование как библиотеки:
    from scripts.export_report_pdf import export_docx_to_pdf
    pdf_path = export_docx_to_pdf("Отчет.docx", "Отчет.pdf")
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Sequence


def export_docx_to_pdf(
    docx_path: str | Path,
    pdf_path: str | Path | None = None,
) -> Path:
    """Экспортирует документ Word (.docx) в PDF (.pdf) через Word COM API."""
    source_docx = Path(docx_path).resolve()
    if not source_docx.is_file():
        raise FileNotFoundError(f"Файл Word не найден: {source_docx}")

    if pdf_path is None:
        target_pdf = source_docx.with_suffix(".pdf")
    else:
        target_pdf = Path(pdf_path).resolve()

    if sys.platform != "win32":
        raise RuntimeError("Экспорт через Word COM API поддерживается только на платформе Windows.")

    try:
        import win32com.client as win32
    except ImportError as exc:
        raise ImportError(
            "Для экспорта в PDF через Word COM требуется пакет pywin32. "
            "Установите его командой: pip install pywin32"
        ) from exc

    print(f"[PDF] Запуск экспорта {source_docx.name} -> {target_pdf.name}...")

    # Изоляция во временном каталоге с ASCII-путем во избежание зависаний COM
    temp_dir = Path(tempfile.gettempdir())
    temp_docx = temp_dir / f"_export_{source_docx.stem}.docx"
    temp_pdf = temp_dir / f"_export_{source_docx.stem}.pdf"

    shutil.copy2(source_docx, temp_docx)

    word = win32.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0

    try:
        doc = word.Documents.Open(str(temp_docx.resolve()))
        doc.Content.LanguageID = 1049  # Русский язык

        # Обновление всех динамических полей и оглавления
        doc.Fields.Update()
        if doc.TablesOfContents.Count > 0:
            doc.TablesOfContents(1).Update()

        # Экспорт в PDF со стандартным полиграфическим качеством и закладками
        doc.ExportAsFixedFormat(
            OutputFileName=str(temp_pdf.resolve()),
            ExportFormat=17,   # wdExportFormatPDF
            OpenAfterExport=False,
            OptimizeFor=0,     # wdExportOptimizeForPrint
            CreateBookmarks=1, # wdExportCreateWordBookmarks
        )

        pages = doc.ComputeStatistics(2)  # wdStatisticPages = 2
        doc.Close(False)

        # Копирование готового PDF в целевую директорию
        shutil.copy2(temp_pdf, target_pdf)
        print(f"[OK] Экспорт успешно завершен! Страниц: {pages}, файл: {target_pdf.name} ({target_pdf.stat().st_size:,} байт)")
        return target_pdf
    finally:
        word.Quit()
        temp_docx.unlink(missing_ok=True)
        temp_pdf.unlink(missing_ok=True)


def main(argv: Sequence[str] | None = None) -> int:
    """Точка входа CLI."""
    parser = argparse.ArgumentParser(description="Полиграфический экспорт DOCX в PDF через Word COM API")
    parser.add_argument("-i", "--input", required=True, help="Путь к исходному файлу Word (*.docx)")
    parser.add_argument("-o", "--output", help="Путь к результирующему файлу PDF (*.pdf)")

    args = parser.parse_args(argv)

    try:
        export_docx_to_pdf(args.input, args.output)
        return 0
    except Exception as exc:
        print(f"[ERR] Ошибка при экспорте в PDF: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
