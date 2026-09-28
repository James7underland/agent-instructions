"""Тесты кодировки, окончаний строк и чистоты типографики Markdown-документов."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from conftest import get_all_markdown_paths, get_markdown_file_id

ALL_MD_FILES = get_all_markdown_paths()

FENCED_CODE_PATTERN = re.compile(r"```[\s\S]*?```")
INLINE_CODE_PATTERN = re.compile(r"`[^`\n]+`")
RAW_LATEX_ARROW_PATTERN = re.compile(r"\$(?:\\to|\\leftarrow|\\leftrightarrow|\\rightarrow|\\Leftarrow|\\Rightarrow)\$")


@pytest.mark.parametrize("file_path", ALL_MD_FILES, ids=get_markdown_file_id)
def test_file_has_no_utf8_bom(file_path: Path) -> None:
    """Проверяет отсутствие сигнатуры BOM (Byte Order Mark) в начале файла."""
    # Arrange: читаем начальные байты файла
    raw_bytes = file_path.read_bytes()

    # Act: проверяем префикс BOM
    has_bom = raw_bytes.startswith(b"\xef\xbb\xbf")

    # Assert: файл обязан быть UTF-8 без BOM
    assert not has_bom, f"Файл {file_path.name} содержит UTF-8 BOM"


@pytest.mark.parametrize("file_path", ALL_MD_FILES, ids=get_markdown_file_id)
def test_file_has_strict_lf_line_endings(file_path: Path) -> None:
    """Проверяет, что файл содержит исключительно UNIX-окончания строк (LF, без CRLF)."""
    # Arrange: читаем бинарное содержимое
    raw_bytes = file_path.read_bytes()

    # Act: проверяем наличие байтов \r\n
    has_crlf = b"\r\n" in raw_bytes

    # Assert: окончания строк CRLF запрещены
    assert not has_crlf, f"Файл {file_path.name} содержит окончания строк CRLF (требуются LF)"


@pytest.mark.parametrize("file_path", ALL_MD_FILES, ids=get_markdown_file_id)
def test_file_is_valid_utf8(file_path: Path) -> None:
    """Проверяет возможность корректного декодирования содержимого в кодировке UTF-8."""
    # Arrange: считываем сырые байты
    raw_bytes = file_path.read_bytes()

    # Act & Assert: декодирование не должно вызывать исключений
    try:
        raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        pytest.fail(f"Файл {file_path.name} не является валидным UTF-8: {exc}")


@pytest.mark.parametrize("file_path", ALL_MD_FILES, ids=get_markdown_file_id)
def test_file_has_no_raw_latex_arrows_in_text(file_path: Path) -> None:
    """Проверяет отсутствие сырых команд LaTeX-стрелок в тексте вне блоков кода."""
    # Arrange: читаем текст и удаляем экранированные блоки кода
    text = file_path.read_text(encoding="utf-8")
    clean_text = FENCED_CODE_PATTERN.sub("", text)
    clean_text = INLINE_CODE_PATTERN.sub("", clean_text)

    # Act: ищем сырые LaTeX-стрелки
    matches = RAW_LATEX_ARROW_PATTERN.findall(clean_text)

    # Assert: сырые LaTeX-стрелки запрещены (требуется нативный Юникод)
    assert not matches, (
        f"В файле {file_path.name} обнаружены сырые LaTeX-стрелки: {matches}. "
        f"Используйте нативные символы Юникода (→, ←, ↔, ⇒, ⇔)."
    )
