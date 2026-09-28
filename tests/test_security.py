"""Тесты безопасности: проверка отсутствия приватных токенов, ключей API и секретов."""

from __future__ import annotations

import re

from conftest import ROOT_DIR

EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache", ".vscode", ".idea", "venv", ".venv"}
SCANNED_EXTENSIONS = {".md", ".py", ".txt", ".json", ".yml", ".yaml", ".ps1", ".ini"}

SECRET_PATTERNS = [
    ("токен GitLab", re.compile(r"glpat-[A-Za-z0-9_\-]{20,}")),
    ("токен GitHub", re.compile(r"\b(?:gh[opsu]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})")),
    ("ключ Anthropic", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("ключ OpenAI", re.compile(r"\bsk-[A-Za-z0-9]{40,}")),
    ("ключ AWS", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("приватный ключ", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("логин:пароль в URL", re.compile(r"https?://[^\s/:@]+:[^\s/@]{6,}@")),
]


def test_no_secrets_in_repository() -> None:
    """Проверяет весь репозиторий на случайную фиксацию токенов и секретов."""
    violations: list[str] = []

    for file_path in sorted(ROOT_DIR.rglob("*")):
        if not file_path.is_file() or file_path.suffix.lower() not in SCANNED_EXTENSIONS:
            continue

        rel_parts = set(file_path.relative_to(ROOT_DIR).parts)
        if rel_parts & EXCLUDED_PARTS:
            continue

        # Исключаем сами файлы сканеров, где регулярные выражения определены
        if file_path.name in ("pack_skills.py", "test_security.py"):
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        rel_path = file_path.relative_to(ROOT_DIR).as_posix()
        for secret_name, regex in SECRET_PATTERNS:
            if regex.search(content):
                violations.append(f"{rel_path}: обнаружен потенциальный {secret_name}")

    assert not violations, "В репозитории обнаружены незащищенные секреты:\n" + "\n".join(f"  - {v}" for v in violations)
