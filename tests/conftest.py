"""Общие фикстуры и конфигурация pytest для тестирования библиотеки инструкций."""

from __future__ import annotations

from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]

# Базовые обязательные модули ядра
REQUIRED_CORE_FILES = [
    "AGENTS.md",
    "README.md",
    "ai_persona_agent.md",
    "text_humanizer_ru.md",
]


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Возвращает абсолютный путь к корню репозитория инструкций."""
    return ROOT_DIR


@pytest.fixture(scope="session")
def required_core_files() -> list[str]:
    """Возвращает перечень обязательных файлов ядра."""
    return list(REQUIRED_CORE_FILES)


def get_all_markdown_paths() -> list[Path]:
    """Возвращает отсортированный список всех Markdown-файлов в репозитории (исключая скрытые папки)."""
    return sorted(
        p for p in ROOT_DIR.rglob("*.md")
        if not any(part.startswith(".") for part in p.relative_to(ROOT_DIR).parts)
    )


def get_markdown_file_id(file_path: Path) -> str:
    """Генерирует лаконичный относительный идентификатор для параметризации тестов."""
    return str(file_path.relative_to(ROOT_DIR)).replace("\\", "/")
