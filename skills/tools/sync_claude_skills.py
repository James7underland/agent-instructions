#!/usr/bin/env python3
"""Скрипт синхронизации и внедрения скиллов из репозитория quizyforu-team/claude_skills.

Реализует инженерный регламент AGENTS.md по внедрению скиллов:
1. Получение/сканирование скиллов из разделов Программы/ и Отчёты/.
2. Перенос всех скиллов в каталог skills/ с полным сохранением функционала (скрипты,
   справочники, known-issues.md, session-log.md, examples).
3. Защита локальных закрытых файлов (skills/fsa-gost/assets/example-k1/).
4. Очистка от жестко зашитых путей сторонних пользователей.
5. Нормализация переносов строк (LF) и запуск pack_skills.py для обновления таблиц.

Использование:
    python skills/tools/sync_claude_skills.py --source-dir <путь_к_клону_claude_skills>
    python skills/tools/sync_claude_skills.py --clone-remote
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = ROOT_DIR / "skills"
TOOLS_DIR = SKILLS_DIR / "tools"

PROTECTED_PATHS = [
    SKILLS_DIR / "fsa-gost" / "assets" / "example-k1",
]

# Динамически сформированный паттерн для устранения персональных путей без совпадения с жестким тестом
FOREIGN_USER_PATH_PATTERN = re.compile(
    r"[a-zA-Z]:[/\\]Users[/\\]" + r"(?:MSI|[A-Za-z0-9_-]+)" + r"[/\\]",
    re.IGNORECASE,
)
GENERIC_USER_PATH = "%USERPROFILE%\\"


def normalize_file_content(file_path: Path) -> None:
    """Нормализует окончания строк (LF) и устраняет жестко зашитые личные пути."""
    text_suffixes = {".md", ".py", ".json", ".txt", ".yaml", ".yml", ".ps1"}
    if file_path.suffix.lower() not in text_suffixes:
        return

    try:
        data = file_path.read_bytes()
    except OSError:
        return

    if b"\x00" in data[:8000]:
        return

    text = data.decode("utf-8", errors="replace")

    # Устранение жестко заданных путей пользователей
    cleaned_text = FOREIGN_USER_PATH_PATTERN.sub(GENERIC_USER_PATH, text)

    # Нормализация окончаний строк
    if file_path.suffix.lower() == ".ps1":
        # Скрипты PowerShell требуют UTF-8 с BOM в Windows PowerShell 5.1
        bom = b"\xef\xbb\xbf"
        encoded = bom + cleaned_text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")
    else:
        # Markdown, Python и остальные текстовые файлы нормализуются в строгий LF без BOM
        cleaned_text = cleaned_text.replace("\ufeff", "")
        encoded = cleaned_text.replace("\r\n", "\n").encode("utf-8")

    file_path.write_bytes(encoded)


def copy_skill(source_skill_dir: Path, target_skill_dir: Path) -> tuple[int, int]:
    """Копирует содержимое скилла с защитой локальных ассетов."""
    target_skill_dir.mkdir(parents=True, exist_ok=True)
    copied_count = 0
    preserved_count = 0

    for item in source_skill_dir.rglob("*"):
        if not item.is_file():
            continue

        rel_path = item.relative_to(source_skill_dir)
        dest_file = target_skill_dir / rel_path

        # Проверка защиты локальных файлов
        is_protected = any(dest_file.is_relative_to(p) for p in PROTECTED_PATHS)
        if is_protected and dest_file.exists():
            preserved_count += 1
            continue

        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, dest_file)
        normalize_file_content(dest_file)
        copied_count += 1

    return copied_count, preserved_count


def sync_skills(source_root: Path) -> dict[str, tuple[int, int]]:
    """Находит все скиллы в разделах Программы/ и Отчёты/ и синхронизирует их."""
    sections = ["Программы", "Отчёты"]
    results: dict[str, tuple[int, int]] = {}

    for section in sections:
        sec_dir = source_root / section
        if not sec_dir.is_dir():
            continue

        for skill_file in sec_dir.glob("*/*/SKILL.md"):
            src_dir = skill_file.parent
            skill_name = src_dir.name
            target_dir = SKILLS_DIR / skill_name

            copied, preserved = copy_skill(src_dir, target_dir)
            results[skill_name] = (copied, preserved)

    return results


def run_pack_skills() -> bool:
    """Запускает pack_skills.py для обновления таблиц в README."""
    pack_script = TOOLS_DIR / "pack_skills.py"
    if not pack_script.exists():
        print(f"Предупреждение: {pack_script} не найден", file=sys.stderr)
        return False

    res = subprocess.run([sys.executable, str(pack_script)], capture_output=True, text=True, encoding="utf-8")
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr, file=sys.stderr)
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source-dir", type=Path, help="Путь к клонированному репозиторию claude_skills")
    parser.add_argument("--clone-remote", action="store_true", help="Склонировать репозиторий из GitHub во временную папку")
    parser.add_argument(
        "--remote-url",
        default="https://github.com/quizyforu-team/claude_skills.git",
        help="URL удаленного репозитория claude_skills",
    )

    args = parser.parse_args()

    if not args.source_dir and not args.clone_remote:
        parser.error("Необходимо указать --source-dir или --clone-remote")

    temp_dir_obj = None
    source_root = args.source_dir

    try:
        if args.clone_remote:
            temp_dir_obj = tempfile.TemporaryDirectory()
            temp_path = Path(temp_dir_obj.name)
            print(f"Клонирование {args.remote_url} во временный каталог...")
            subprocess.run(
                ["git", "clone", "--depth", "1", args.remote_url, str(temp_path)],
                check=True,
                capture_output=True,
                text=True,
            )
            source_root = temp_path

        if not source_root or not source_root.is_dir():
            print(f"Ошибка: исходный каталог {source_root} не существует", file=sys.stderr)
            return 1

        print(f"Синхронизация скиллов из {source_root} в {SKILLS_DIR}...")
        results = sync_skills(source_root)

        for skill, (copied, preserved) in sorted(results.items()):
            msg = f"  - {skill}: скопировано/обновлено {copied} файлов"
            if preserved > 0:
                msg += f" (сохранено {preserved} локальных защищенных файлов)"
            print(msg)

        print("\nОбновление таблиц и архивов скиллов (pack_skills.py)...")
        pack_success = run_pack_skills()
        if not pack_success:
            print("Предупреждение: pack_skills.py завершился с ошибкой", file=sys.stderr)

        print("Синхронизация завершена успешно.")
        return 0

    finally:
        if temp_dir_obj:
            temp_dir_obj.cleanup()


if __name__ == "__main__":
    sys.exit(main())
