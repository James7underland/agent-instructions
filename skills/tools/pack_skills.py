#!/usr/bin/env python3
"""Проверка скиллов, сборка архивов .skill (опционально) и обновление таблицы в README.md.

Запуск из корня репозитория:
    python skills/tools/pack_skills.py                  # проверить скиллы и обновить таблицу в README
    python skills/tools/pack_skills.py --check          # только проверить; код выхода 1, если что-то не так
    python skills/tools/pack_skills.py --build-archives # собрать бинарные архивы .skill

Скилл — это папка <Программа>/<имя-скилла>/ с файлом SKILL.md.
"""
from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
TABLE_START = "<!-- skills:start -->"
TABLE_END = "<!-- skills:end -->"

EXCLUDED_DIRS = {"__pycache__", ".git", ".idea", ".vscode"}
EXCLUDED_FILES = {".DS_Store", "Thumbs.db", "desktop.ini"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log"}
KEEP_EOL_SUFFIXES: set[str] = set()  # Все текстовые файлы нормализуются к LF для детерминированности
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DESCRIPTION_LIMIT = 1024
FILE_SIZE_WARN = 20 * 1024 * 1024

SECRET_PATTERNS = [
    ("токен GitLab", re.compile(rb"glpat-[A-Za-z0-9_\-]{20,}")),
    ("токен GitHub", re.compile(rb"\b(gh[opsu]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})")),
    ("ключ Anthropic", re.compile(rb"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("ключ OpenAI", re.compile(rb"\bsk-[A-Za-z0-9]{40,}")),
    ("ключ AWS", re.compile(rb"\bAKIA[0-9A-Z]{16}\b")),
    ("приватный ключ", re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("логин:пароль в URL", re.compile(rb"https?://[^\s/:@]+:[^\s/@]{6,}@")),
]


def is_excluded(path: Path, base: Path) -> bool:
    rel = path.relative_to(base)
    if any(part in EXCLUDED_DIRS for part in rel.parts):
        return True
    if path.name in EXCLUDED_FILES or path.suffix in EXCLUDED_SUFFIXES:
        return True
    return ".bak-" in path.name


def git_ignored(paths: list[Path]) -> set[Path]:
    """Файлы из .gitignore (например, локальные материалы, которые нельзя выкладывать) — не кладём в архив."""
    if not paths:
        return set()
    try:
        r = subprocess.run(
            ["git", "-C", str(ROOT), "check-ignore", "--stdin", "-z"],
            input=b"\0".join(p.relative_to(ROOT).as_posix().encode("utf-8") for p in paths),
            capture_output=True,
        )
    except FileNotFoundError:
        return set()
    if r.returncode not in (0, 1):
        return set()
    return {ROOT / s.decode("utf-8") for s in r.stdout.split(b"\0") if s}


def skill_files(skill_dir: Path) -> list[Path]:
    files = [p for p in skill_dir.rglob("*") if p.is_file() and not is_excluded(p, skill_dir)]
    ignored = git_ignored(files)
    return sorted(
        (p for p in files if p not in ignored),
        key=lambda p: p.relative_to(skill_dir).as_posix(),
    )


def parse_frontmatter(text: str) -> dict[str, str] | None:
    if text.startswith("﻿"):
        text = text[1:]
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not m:
        return None
    fields = {}
    for line in m.group(1).splitlines():
        k, sep, v = line.partition(":")
        if sep and not line.startswith((" ", "\t")):
            fields[k.strip()] = v.strip().strip('"').strip("'")
    return fields


def archive_bytes(f: Path) -> bytes:
    """Содержимое файла для архива: текст с LF, как его хранит git (.gitattributes: eol=lf).

    Иначе файл, скопированный в рабочую копию с CRLF, git считает неизменённым, а архив получается другим.
    """
    data = f.read_bytes()
    if f.suffix.lower() in KEEP_EOL_SUFFIXES or b"\0" in data[:8000]:
        return data
    return data.replace(b"\r\n", b"\n")


def build_archive(skill_dir: Path, files: list[Path]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            info = zipfile.ZipInfo(f"{skill_dir.name}/{f.relative_to(skill_dir).as_posix()}", (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 0
            info.external_attr = 0o644 << 16
            z.writestr(info, archive_bytes(f))
    return buf.getvalue()


PROGRAM_NAMES = {
    "mathcad13": "Mathcad 13",
    "simulink": "Simulink",
    "symmetry": "Symmetry",
    "unimod-pro-trei": "Unimod Pro 2",
    "fsa-gost": "Visio (ФСА ГОСТ)",
    "tau-labs": "ТАУ лабы",
    "tau3": "ТАУ-3",
    "c-core": "Язык C (микроконтроллеры)",
    "embedded-c": "Язык C (микроконтроллеры)",
    "esp8266-pio": "Язык C (микроконтроллеры)",
}


def find_skills() -> list[Path]:
    candidates = list(ROOT.glob("*/SKILL.md")) + list(ROOT.glob("*/*/SKILL.md"))
    return sorted({p.parent for p in candidates if not is_excluded(p, ROOT)}, key=lambda p: p.name)


def short_description(desc: str, limit: int = 140) -> str:
    first = re.split(r"(?<=[.!?])\s|\s—\s", desc, maxsplit=1)[0]
    first = first if len(first) <= limit else first[: limit - 1].rstrip() + "…"
    return first.replace("|", "\\|")


def render_table(rows: list[tuple[str, str, int, str, str]]) -> str:
    lines = [
        "| Программа | Скилл | Файлов | О чём |",
        "|---|---|---|---|",
    ]
    for prog, name, count, desc, rel_link in rows:
        lines.append(f"| {prog} | [`{name}`]({quote(rel_link)}) | {count} | {desc} |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="ничего не записывать, только проверить")
    ap.add_argument("--build-archives", action="store_true", help="собрать бинарные архивы .skill")
    args = ap.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    rows: list[tuple[str, str, int, str]] = []
    names_seen: dict[str, Path] = {}

    skills = find_skills()
    if not skills:
        errors.append("не найдено ни одного <Программа>/<скилл>/SKILL.md")

    for skill_dir in skills:
        if skill_dir.parent == ROOT:
            prog = PROGRAM_NAMES.get(skill_dir.name, skill_dir.name)
        else:
            prog = skill_dir.parent.name
        label = f"{prog}/{skill_dir.name}"
        fm = parse_frontmatter((skill_dir / "SKILL.md").read_text(encoding="utf-8"))
        if fm is None:
            errors.append(f"{label}: в SKILL.md нет frontmatter (--- name/description ---)")
            continue
        name, desc = fm.get("name", ""), fm.get("description", "")
        if name != skill_dir.name:
            errors.append(f"{label}: name '{name}' не совпадает с именем папки '{skill_dir.name}'")
        if not NAME_RE.match(skill_dir.name):
            errors.append(f"{label}: имя скилла только из a-z, 0-9 и дефисов")
        if name in names_seen:
            errors.append(f"{label}: скилл '{name}' уже есть в {names_seen[name]}")
        names_seen[name] = skill_dir.relative_to(ROOT)
        if not desc:
            errors.append(f"{label}: пустой description")
        elif len(desc) > DESCRIPTION_LIMIT:
            warnings.append(f"{label}: description {len(desc)} символов (> {DESCRIPTION_LIMIT}), может обрезаться")

        files = skill_files(skill_dir)
        for f in files:
            data = f.read_bytes()
            rel = f.relative_to(ROOT).as_posix()
            if len(data) > FILE_SIZE_WARN:
                warnings.append(f"{rel}: {len(data) // (1024 * 1024)} МБ — большой файл для git")
            for what, rx in SECRET_PATTERNS:
                if rx.search(data):
                    errors.append(f"{rel}: похоже на {what} — убрать перед коммитом")

        if args.build_archives:
            archive = skill_dir.parent / f"{skill_dir.name}.skill"
            fresh = build_archive(skill_dir, files)
            archive.write_bytes(fresh)
            print(f"собран {archive.relative_to(ROOT).as_posix()} ({len(files)} файлов)")

        rel_link = (skill_dir / "SKILL.md").relative_to(ROOT).as_posix()
        rows.append((prog, name or skill_dir.name, len(files), short_description(desc), rel_link))

    if README.exists():
        text = README.read_text(encoding="utf-8")
        if TABLE_START in text and TABLE_END in text:
            head, rest = text.split(TABLE_START, 1)
            _, tail = rest.split(TABLE_END, 1)
            new = f"{head}{TABLE_START}\n{render_table(rows)}\n{TABLE_END}{tail}"
            if new != text:
                if args.check:
                    errors.append("README.md: таблица скиллов устарела, запустите tools/pack_skills.py")
                else:
                    README.write_text(new, encoding="utf-8", newline="\n")
                    print("обновлена таблица в README.md")
        else:
            warnings.append(f"README.md: нет меток {TABLE_START} / {TABLE_END}, таблица не обновлена")

    for w in warnings:
        print(f"ПРЕДУПРЕЖДЕНИЕ: {w}")
    for e in errors:
        print(f"ОШИБКА: {e}")
    print(f"скиллов: {len(skills)}, ошибок: {len(errors)}, предупреждений: {len(warnings)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
