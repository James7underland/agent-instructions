"""Тесты валидации, целостности и синтаксиса прикладных скиллов (skills/)."""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import ROOT_DIR

SKILLS_DIR = ROOT_DIR / "skills"
SKILL_DIRS = sorted([p.parent for p in SKILLS_DIR.glob("*/SKILL.md")])
PYTHON_SCRIPT_PATHS = sorted(SKILLS_DIR.rglob("*.py"))

NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FRONTMATTER_PATTERN = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Парсит плоский YAML frontmatter блока --- name: ... description: ... ---."""
    if text.startswith("\ufeff"):
        text = text[1:]
    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        return None
    fields = {}
    for line in match.group(1).splitlines():
        key, sep, val = line.partition(":")
        if sep and not line.startswith((" ", "\t")):
            fields[key.strip()] = val.strip().strip('"').strip("'")
    return fields


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=lambda p: p.name)
def test_skill_has_valid_frontmatter(skill_dir: Path) -> None:
    """Проверяет корректность frontmatter в SKILL.md каждого скилла."""
    skill_file = skill_dir / "SKILL.md"
    assert skill_file.exists(), f"Файл {skill_file} не найден"

    content = skill_file.read_text(encoding="utf-8")
    fm = parse_frontmatter(content)
    assert fm is not None, f"В {skill_file} отсутствует валидный блок frontmatter (--- name/description ---)"

    name = fm.get("name", "")
    assert name == skill_dir.name, f"Имя скилла '{name}' не совпадает с каталогом '{skill_dir.name}'"
    assert NAME_PATTERN.match(name), f"Имя скилла '{name}' не соответствует формату kebab-case"

    description = fm.get("description", "")
    assert description, f"Поле description в {skill_file} не может быть пустым"
    assert len(description) <= 1500, f"Слишком длинный description в {skill_file}: {len(description)} симв."


def test_no_hardcoded_foreign_user_paths() -> None:
    """Проверяет отсутствие жестко зашитых путей сторонних пользователей (Users/MSI)."""
    violations: list[str] = []
    scanned_exts = {".md", ".py", ".ps1", ".txt", ".json"}

    for path in SKILLS_DIR.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in scanned_exts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "Users\\MSI" in text or "Users/MSI" in text:
            violations.append(str(path.relative_to(ROOT_DIR)))

    assert not violations, "Обнаружены жестко заданные пути пользователей в файлах:\n" + "\n".join(f"  - {v}" for v in violations)


@pytest.mark.parametrize("script_path", PYTHON_SCRIPT_PATHS, ids=lambda p: str(p.relative_to(ROOT_DIR)).replace("\\", "/"))
def test_python_scripts_syntax(script_path: Path) -> None:
    """Проверяет синтаксическую корректность всех Python-скриптов скиллов."""
    source = script_path.read_text(encoding="utf-8")
    try:
        ast.parse(source, filename=str(script_path))
    except SyntaxError as exc:
        pytest.fail(f"Синтаксическая ошибка в {script_path.name}: {exc}")


def test_pack_skills_verification() -> None:
    """Проверяет работу скрипта pack_skills.py в режиме проверки (--check)."""
    script_path = SKILLS_DIR / "tools" / "pack_skills.py"
    assert script_path.exists(), "Скрипт pack_skills.py не найден"

    res = subprocess.run(
        [sys.executable, str(script_path), "--check"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert res.returncode == 0, f"pack_skills.py --check завершился с ошибкой:\n{res.stdout}\n{res.stderr}"


def test_task_modules_link_to_skills() -> None:
    """Проверяет привязку верхнеуровневых прикладных модулей к скиллам."""
    mappings = {
        "model_mathcad.md": "skills/mathcad13/SKILL.md",
        "model_unimod_trei.md": "skills/unimod-pro-trei/SKILL.md",
        "diagram_fsa_visio.md": "skills/fsa-gost/SKILL.md",
        "lab_tau_reports.md": "skills/tau-labs/SKILL.md",
        "model_tau3.md": "skills/tau3/SKILL.md",
        "model_simulink.md": "skills/simulink/SKILL.md",
        "superpowers_agent.md": "skills/using-superpowers/SKILL.md",
    }
    for mod_name, skill_rel in mappings.items():
        mod_path = ROOT_DIR / mod_name
        assert mod_path.exists(), f"Модуль {mod_name} не найден в корне репозитория"
        content = mod_path.read_text(encoding="utf-8")
        assert skill_rel in content, f"В модуле {mod_name} отсутствует ссылка на {skill_rel}"
