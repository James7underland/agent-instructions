"""Тесты целостности и валидности локальных относительных ссылок в Markdown-файлах."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote
import pytest
from conftest import ROOT_DIR, get_all_markdown_paths, get_markdown_file_id

ALL_MD_FILES = get_all_markdown_paths()

FENCED_CODE_PATTERN = re.compile(r"```[\s\S]*?```")
INLINE_CODE_PATTERN = re.compile(r"`[^`\n]+`")
LINK_PATTERN = re.compile(r'!?\[([^\]]*)\]\(([^)]+)\)')


@pytest.mark.parametrize("file_path", ALL_MD_FILES, ids=get_markdown_file_id)
def test_markdown_file_has_valid_relative_links(file_path: Path) -> None:
    """Проверяет, что все относительные ссылки в документе указывают на существующие файлы."""
    # Arrange: считываем текст и отсекаем блоки кода, чтобы игнорировать примеры синтаксиса
    text = file_path.read_text(encoding="utf-8")
    clean_text = FENCED_CODE_PATTERN.sub("", text)
    clean_text = INLINE_CODE_PATTERN.sub("", clean_text)
    file_dir = file_path.parent

    broken_links: list[str] = []

    # Act: сканируем все ссылки в документе
    for match in LINK_PATTERN.finditer(clean_text):
        link_target = match.group(2).strip()

        # Игнорируем внешние веб-ссылки, почту и внутрифайловые якоря
        if link_target.startswith(("http://", "https://", "mailto:", "#")):
            continue

        # Отсекаем якорь ссылки вида path/to/doc.md#section
        path_part = link_target.split("#")[0].strip()
        if not path_part:
            continue

        decoded_path = unquote(path_part)
        target_path = (file_dir / decoded_path).resolve()

        if not target_path.exists():
            broken_links.append(f"'{link_target}' (целевой путь не найден: {target_path})")

    # Assert: ни одной битой ссылки быть не должно
    rel_source = file_path.relative_to(ROOT_DIR)
    assert not broken_links, f"В файле {rel_source} обнаружены битые ссылки:\n" + "\n".join(f"  - {err}" for err in broken_links)
