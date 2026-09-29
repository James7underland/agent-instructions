# Скиллы для программ (локальная копия)

Полные рабочие версии скиллов с этого компьютера. Обновлено 30.09.2026.

Общая версия для команды лежит в репозитории [quizyforu-team/claude_skills](https://github.com/quizyforu-team/claude_skills). Там нет картинок `fsa-gost/assets/example-k1/`: это фрагменты документации предприятия, они есть только здесь и в рабочей папке скилла.

При запросе пользователя выполняется синхронизация и внедрение актуальной версии скиллов из [quizyforu-team/claude_skills](https://github.com/quizyforu-team/claude_skills) с полным сохранением функционала по регламенту из [`AGENTS.md`](../AGENTS.md).

<!-- skills:start -->
| Программа | Скилл | Файлов | О чём |
|---|---|---|---|
| Superpowers (методология) | [`brainstorming`](brainstorming/SKILL.md) | 8 | You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. |
| Язык C (микроконтроллеры) | [`c-core`](c-core/SKILL.md) | 25 | Язык C (C99) по Кернигану–Ритчи с упором на надёжность: типы и неявные преобразования, приоритеты операторов, указатели и массивы, строки,… |
| Superpowers (методология) | [`diagnosing-superpowers`](diagnosing-superpowers/SKILL.md) | 20 | Use when a superpowers session went wrong and your human partner wants to know why |
| Superpowers (методология) | [`dispatching-parallel-agents`](dispatching-parallel-agents/SKILL.md) | 1 | Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies |
| Язык C (микроконтроллеры) | [`embedded-c`](embedded-c/SKILL.md) | 44 | Прошивки микроконтроллеров на C по книге «Making Embedded Systems» (Elecia White): архитектура (слои, HAL, драйверы, интерфейсы модулей), р… |
| Язык C (микроконтроллеры) | [`esp8266-pio`](esp8266-pio/SKILL.md) | 10 | Wemos (LOLIN) D1 mini на ESP8266 с PlatformIO и фреймворком Arduino (курс «Микропроцессоры»): создание проекта, platformio.ini (env d1_mini… |
| Superpowers (методология) | [`executing-plans`](executing-plans/SKILL.md) | 3 | Use when executing an implementation plan in the current session as the implementer yourself |
| Superpowers (методология) | [`finishing-a-development-branch`](finishing-a-development-branch/SKILL.md) | 1 | Use when implementation is complete, all tests pass, and you need to decide how to integrate the work |
| Visio (ФСА ГОСТ) | [`fsa-gost`](fsa-gost/SKILL.md) | 60 | ФСА (функциональные схемы автоматизации, P&ID, КИПиА) по ГОСТ 21.208-2013 и 21.408-2013 в Visio. |
| Humanizer (редактура текста) | [`humanizer`](humanizer/SKILL.md) | 10 | Rewrite AI-sounding text so it reads like the writer without changing what it says. |
| Mathcad 13 | [`mathcad13`](mathcad13/SKILL.md) | 24 | Работа с Mathcad 13 (Mathsoft, 2005; папку установки находит scripts/find_mathcad.py) |
| Superpowers (методология) | [`receiving-code-review`](receiving-code-review/SKILL.md) | 1 | Use when receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or technically questionable… |
| Superpowers (методология) | [`requesting-code-review`](requesting-code-review/SKILL.md) | 2 | Use when completing tasks, implementing major features, or before merging to verify work meets requirements |
| Simulink | [`simulink`](simulink/SKILL.md) | 22 | Работа с MATLAB/Simulink (R2025b, Windows) без мыши |
| Superpowers (методология) | [`subagent-driven-development`](subagent-driven-development/SKILL.md) | 7 | Use when executing implementation plans with independent tasks in the current session |
| Symmetry | [`symmetry`](symmetry/SKILL.md) | 204 | Работа в симуляторе ХТП Symmetry 2023.2 (SLB, бывший VMGSim) без мыши: расчёт схем (потоки, теплообменники, клапаны, сепараторы, насосы, ко… |
| Superpowers (методология) | [`systematic-debugging`](systematic-debugging/SKILL.md) | 11 | Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes |
| ТАУ лабы | [`tau-labs`](tau-labs/SKILL.md) | 9 | Отчёты по лабораторным ТАУ (методичка Великанов/Мартынова «Линейные системы», Губкин, АТП) с разными числами для каждого студента: правдопо… |
| ТАУ-3 | [`tau3`](tau3/SKILL.md) | 336 | Учебный пакет «ТАУ-3» (Лозинский/Берщанский) |
| Superpowers (методология) | [`test-driven-development`](test-driven-development/SKILL.md) | 2 | Use when implementing any feature or bugfix, before writing implementation code |
| Unimod Pro 2 | [`unimod-pro-trei`](unimod-pro-trei/SKILL.md) | 40 | Работа с проектами Unimod PRO 2 (концерн ТРЭИ, ПЛК TREI-5B, языки МЭК 61131-3). |
| Superpowers (методология) | [`using-git-worktrees`](using-git-worktrees/SKILL.md) | 1 | Use when starting feature work that needs isolation from current workspace or before executing implementation plans - ensures an isolated w… |
| Superpowers (методология) | [`using-superpowers`](using-superpowers/SKILL.md) | 8 | Use when starting any conversation - establishes how to find and use skills, requiring skill invocation before ANY response including clari… |
| Superpowers (методология) | [`verification-before-completion`](verification-before-completion/SKILL.md) | 1 | Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and… |
| Superpowers (методология) | [`writing-plans`](writing-plans/SKILL.md) | 1 | Use when you have a spec or requirements for a multi-step task, before touching code |
| Superpowers (методология) | [`writing-skills`](writing-skills/SKILL.md) | 7 | Use when creating new skills, editing existing skills, or verifying skills work before deployment |
<!-- skills:end -->

Архивы `.skill` (при необходимости) и таблица собираются командой `python tools/pack_skills.py`.
Все скиллы хранятся в открытом текстовом формате Markdown и доступны для прямого чтения любыми ИИ-агентами.
