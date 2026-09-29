"""Тесты наличия и целостности обязательных базовых файлов ядра библиотеки."""

from __future__ import annotations

import re
from pathlib import Path


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
    assert "ai_persona_agent.md" in content, "AGENTS.md обязан ссылаться на ai_persona_agent.md"
    assert "text_humanizer_ru.md" in content, "AGENTS.md обязан ссылаться на text_humanizer_ru.md"
    assert "superpowers_agent.md" in content, "AGENTS.md обязан ссылаться на superpowers_agent.md"


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


def test_all_root_markdown_modules_cataloged_in_readme(repo_root: Path) -> None:
    """Проверяет полноту каталога README.md: каждый корневой модуль обязан быть внесен в README.md."""
    # Arrange: находим все .md файлы в корне (кроме AGENTS.md и самого README.md)
    root_md_files = sorted(
        p.name for p in repo_root.glob("*.md")
        if p.name not in ("README.md", "AGENTS.md")
    )
    readme_text = (repo_root / "README.md").read_text(encoding="utf-8")

    # Act: выявляем модули, не упомянутые в README.md
    uncataloged: list[str] = [name for name in root_md_files if name not in readme_text]

    # Assert: ни один корневой модуль не должен быть потерян
    assert not uncataloged, f"В README.md не включены следующие корневые модули: {uncataloged}"


def test_all_review_checklists_cataloged_in_checklists_readme(repo_root: Path) -> None:
    """Проверяет полноту каталога чек-листов: каждый файл из review_checklists/ обязан быть в README.md."""
    # Arrange: находим все .md файлы в review_checklists/ (кроме README.md)
    checklists_dir = repo_root / "review_checklists"
    checklist_files = sorted(
        p.name for p in checklists_dir.glob("*.md")
        if p.name != "README.md"
    )
    readme_text = (checklists_dir / "README.md").read_text(encoding="utf-8")

    # Act: выявляем чек-листы, не упомянутые в оглавлении
    uncataloged: list[str] = [name for name in checklist_files if name not in readme_text]

    # Assert: каждый чек-лист обязан быть внесен в каталог
    assert not uncataloged, f"В review_checklists/README.md не включены файлы: {uncataloged}"
