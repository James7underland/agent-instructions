"""Скрипт верификации целостности модулей инструкций для CI/CD.

Проверяет:
1. Кодировку всех .md файлов (строго UTF-8 без BOM).
2. Окончания строк (LF, без CRLF).
3. Наличие обязательных базовых файлов (AGENTS.md, README.md, ai_persona_claude.md, text_humanizer_ru.md).
4. Валидность всех локальных относительных ссылок в Markdown-документах (отсутствие битых ссылок).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

# Обеспечиваем корректный вывод UTF-8 в консолях Windows и CI/CD
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parents[1]

# Обязательные базовые модули ядра библиотеки
REQUIRED_CORE_FILES = [
    "AGENTS.md",
    "README.md",
    "ai_persona_claude.md",
    "text_humanizer_ru.md",
]

# Регулярные выражения для фильтрации блоков кода и поиска ссылок
FENCED_CODE_PATTERN = re.compile(r"```[\s\S]*?```")
INLINE_CODE_PATTERN = re.compile(r"`[^`\n]+`")
LINK_PATTERN = re.compile(r'!?\[([^\]]*)\]\(([^)]+)\)')


def check_encoding_and_endings(file_path: Path) -> list[str]:
    """Проверяет кодировку UTF-8 без BOM и окончания строк LF."""
    errors: list[str] = []
    raw_bytes = file_path.read_bytes()

    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        errors.append(f"{file_path.name}: обнаружен UTF-8 BOM (требуется UTF-8 без BOM)")

    if b"\r\n" in raw_bytes:
        errors.append(f"{file_path.name}: обнаружены окончания строк CRLF (требуются LF)")

    try:
        raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        errors.append(f"{file_path.name}: ошибка декодирования UTF-8: {exc}")

    return errors


def check_relative_links(file_path: Path) -> list[str]:
    """Проверяет корректность всех относительных ссылок в документе (вне блоков кода)."""
    errors: list[str] = []
    text = file_path.read_text(encoding="utf-8")
    file_dir = file_path.parent

    # Удаляем блоки кода и инлайн-код, чтобы не проверять синтаксические примеры в документации
    clean_text = FENCED_CODE_PATTERN.sub("", text)
    clean_text = INLINE_CODE_PATTERN.sub("", clean_text)

    for match in LINK_PATTERN.finditer(clean_text):
        link_target = match.group(2).strip()

        # Игнорируем веб-ссылки, mailto и ссылки на якоря внутри текущего файла
        if link_target.startswith(("http://", "https://", "mailto:", "#")):
            continue

        # Отсекаем якорь, если ссылка вида path/to/file.md#anchor
        path_part = link_target.split("#")[0].strip()
        if not path_part:
            continue

        decoded_path = unquote(path_part)
        target_path = (file_dir / decoded_path).resolve()

        if not target_path.exists():
            errors.append(
                f"{file_path.relative_to(ROOT_DIR)}: битая ссылка '{link_target}' "
                f"(целевой файл не найден: {target_path})"
            )

    return errors


def main() -> int:
    """Точка входа: запускает полный аудит библиотеки."""
    print("=" * 60)
    print("Запуск верификации библиотеки инструкций (agent-instructions)...")
    print("=" * 60)

    all_errors: list[str] = []

    # 1. Проверка обязательных файлов
    print("[1/3] Проверка наличия обязательных модулей ядра...")
    for required_name in REQUIRED_CORE_FILES:
        target = ROOT_DIR / required_name
        if not target.is_file():
            all_errors.append(f"Отсутствует обязательный файл ядра: {required_name}")
        else:
            print(f"  ✓ {required_name}")

    # 2. Поиск всех .md файлов
    md_files = sorted(ROOT_DIR.rglob("*.md"))
    print(f"\n[2/3] Проверка кодировки и формата ({len(md_files)} файлов)...")
    for md_file in md_files:
        enc_errors = check_encoding_and_endings(md_file)
        all_errors.extend(enc_errors)
        if not enc_errors:
            print(f"  ✓ {md_file.relative_to(ROOT_DIR)}")

    # 3. Проверка относительных ссылок
    print(f"\n[3/3] Проверка целостности относительных ссылок...")
    for md_file in md_files:
        link_errors = check_relative_links(md_file)
        all_errors.extend(link_errors)
        if not link_errors:
            print(f"  ✓ {md_file.relative_to(ROOT_DIR)} (ссылки корректны)")

    print("\n" + "=" * 60)
    if all_errors:
        print(f"ОБНАРУЖЕНО ОШИБОК: {len(all_errors)}")
        for err in all_errors:
            print(f"  ✗ {err}")
        print("=" * 60)
        return 1

    print("ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
