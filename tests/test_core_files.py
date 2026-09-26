"""Тесты наличия и целостности обязательных базовых файлов ядра библиотеки."""

from __future__ import annotations

import re
from pathlib import Path
import pytest


def test_contains_all_required_core_files(repo_root: Path, required_core_files: list[str]) -> None:
    """Проверяет физическое наличие всех базовых модулей ядра репозитория."""
    # Arrange: формируем список ожидаемых путей
    missing_files: list[str] = []

    # Act: проверяем существование каждого файла ядра
    for filename in required_core_files:
        target = repo_root / filename
        if not target.is_file():
            missing_files.append(filename)

    # Assert: все файлы ядра обязаны существовать
    assert not missing_files, f"Отсутствуют обязательные файлы ядра: {missing_files}"


def test_agents_bootstrap_references_core_modules(repo_root: Path) -> None:
    """Проверяет, что корневой AGENTS.md содержит вызовы модулей базового ядра."""
    # Arrange: путь к AGENTS.md
    agents_file = repo_root / "AGENTS.md"

    # Act: считываем текст загрузчика
    content = agents_file.read_text(encoding="utf-8")

    # Assert: проверяем наличие прямых ссылок на модули ядра
    assert "ai_persona_claude.md" in content, "AGENTS.md обязан ссылаться на ai_persona_claude.md"
    assert "text_humanizer_ru.md" in content, "AGENTS.md обязан ссылаться на text_humanizer_ru.md"


def test_readme_catalog_references_existing_modules(repo_root: Path) -> None:
    """Проверяет, что все модули, упомянутые в каталоге README.md, существуют на диске."""
    # Arrange: считываем README.md и ищем относительные ссылки на .md файлы
    readme_path = repo_root / "README.md"
    readme_text = readme_path.read_text(encoding="utf-8")
    md_link_pattern = re.compile(r'\[`?([a-zA-Z0-9_\-]+\.md)`?\]\(([^)]+\.md)\)')

    # Act: извлекаем целевые пути ссылок
    referenced_files: set[str] = set()
    for match in md_link_pattern.finditer(readme_text):
        target = match.group(2).split("#")[0].strip()
        referenced_files.add(target)

    # Assert: каждый целевой файл обязан существовать
    missing: list[str] = []
    for rel_target in sorted(referenced_files):
        target_path = (readme_path.parent / rel_target).resolve()
        if not target_path.is_file():
            missing.append(f"{rel_target} (целевой путь {target_path} не найден)")

    assert not missing, f"README.md ссылается на несуществующие модули: {missing}"
