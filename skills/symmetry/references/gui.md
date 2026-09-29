# GUI Symmetry (UI64\Symmetry.exe) — карта и автоматизация

WPF-приложение (Xceed AvalonDock + System.Windows.Controls.Ribbon), PFD — встроенный Visio (окно `VISIOM`/`VISIOG`).
Снимок: `examples/gui_main_window.png`. Запуск и управление — `scripts/gui.py` (свой экземпляр, pid в
`%TEMP%\symmetry_gui.json`). Запуск ~10–40 с. **Окно всегда разворачивается на весь экран** (`launch`/`shot --size max`, по умолчанию);
конкретный размер — `--size 1700x1050`. Кейс открывается с теми окнами, что были открыты при сохранении
(Process Calculator, Strip Chart и т.п. — видны в `popups`). Полная схема картинкой — `vsym.py visio` (Visio).

## Лента
| Вкладка | Группы: кнопки |
|---|---|
| Home | Case: New, Open · Thermo · Steady State: переключатель Solver Active/Inactive, Stop, Re-solve · Main Settings: Simulation Engine Selection (стационар/динамика), Unit Set (ComboBox `cmbUnitSet`, по умолчанию **Field**) |
| View | Panes: Simulation Tree, Process Flow Diagram, PFD Shapes, Window List, Errors, Start Page · Utilities: Basic Properties, **Command Log**, Case Notes · Window: Bring all to front, Minimize all, Move all to Main Window, Close all, Refresh all, Reset workspace layout |
| Tools | Productivity: Case Study, Model Regression, Optimizer · Customization: Unit Sets, Settings · Analysis: Emissions, Economics, Utilities Configuration · Utility: **Command Line**, Convergence Monitor, Line List, Specification Summary · Connectivity: Server Manager |
| Reporting | General: Project Report, Summary Sets · Customization: Report Header and Global Variables, Reports Manager |
| File | меню приложения (Open/Save/Save As/…) |
Панель быстрого доступа (заголовок): Save (первая `RibbonButton`), Undo, Redo.

## Панели
- Слева: **Shapes** (палитра: Streams, Main Shapes, Heat Exchange, Piping and Flow, Separation, Towers, Reactors, …),
  **Simulation Tree** (дерево по категориям: Streams/Heat Exchange/…/Property Packages), **Errors**.
- Центр: PFD (вкладки схем внизу: Main Flowsheet, «+» — новая), меню **PFD**: Page Set up, Center Drawing, Copy
  Drawing, **Save PFD As → Image File (Active Flowsheet only) | Visio file**, Utility (Borders and PFD ID,
  Show/Hide Stream Labels, Stream Display Option, Datasheets, Scaling, Labels Visibility), Shape (Order, Rotate or
  Flip, Align, Distribute, **Lay Out Shapes…**), Format, Tools (Ruler & Grid).
- Справа: Windows List (открытые окна операций).
- **Tools → Command Line**: окно «Command Line Interface Current Object : /» — поле команды + **Run Script…**
  (запуск .tst). Снимок `examples/gui_command_line.png`. Удобно дать пользователю: «вставьте команды из файла».

## Что автоматизируется (gui.py) и что нет
✔ запуск с кейсом, REST-команды с пересчётом, чтение значений, весь кейс JSON, Save (+ «Yes»), снимок главного окна и
  области PFD (PrintWindow, окно может быть перекрыто), список диалогов и нажатие их кнопок, выбор вкладок ленты
  (`click Tools --type TabItem`) и нажатие кнопок (`click "Command Line"`), дамп UIA-дерева (`ui`).
✗ открыть окно свойств аппарата (двойной щелчок по значку/узлу дерева): UIA Invoke у узлов дерева нет, PostMessage
  двойного щелчка Visio игнорирует; реальную мышь и фокус пользователя не трогаем → просить пользователя или
  показывать данные через `sym.py info`/таблицы.
✗ Save As (файловый диалог) — вместо этого запускать GUI сразу с копией файла под нужным именем.
✗ красивая раскладка PFD для кейсов, собранных скриптом: GUI расставляет значки в ряд, потоки — отдельными
  короткими стрелками у левого края, без соединений (`UpdateCase` с новыми `pfd`-координатами не двигает фигуры).
  → для отчёта рисовать `scripts/pfd.py`; для «настоящей» GUI-схемы — пользователь расставляет/соединяет вручную
  (или строить схему в GUI мышью с самого начала). Кейсы из Documentation имеют нормальные PFD.

## UI Automation — приёмы
- Главное окно: заголовок начинается с «Symmetry | <файл>»; `app.top_window()` может вернуть всплывающее окно
  ошибок (450×67, «(N)» — счётчик ошибок) — ищите по заголовку.
- `descendants()` в этом окне теряет узлы (VisioHost) — обходить рекурсивно `children()` (`gui.walk`).
- Диалоги (Save Project, License, сообщения) — дочерние Window главного окна: `gui.py popups` их перечисляет и
  снимает (`popups DIR`), `gui.py answer Yes` нажимает кнопку.
- Имена ribbon-кнопок = подписи (`New`, `Open`, `Thermo`, `Re-solve`, `Case Study`, …); вкладки — TabItem `Home` и т.п.
