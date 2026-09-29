# Файлы кейсов

| Расширение | Что это |
|---|---|
| `.vsym` | кейс Symmetry = ZIP: `__s42z__.s42` (двоичное состояние: `RELB_101051` + pickle `csim.solver.Flowsheet`), `<имя>.tst` (текст команд, журнал всей истории кейса), `<имя>.GUI` (ini: `[Symmetry] 11.1`, `PFD.Engine = Visio2013`, `Unit.Default = Field`, шрифты/форматы), `<имя>.vsd` (PFD Visio), `_metadata.json`, опц. `DynamicsCase.s2m` |
| `.vmp` | старый VMGSim-проект (тот же ZIP + `.s2m`, `UnitOpFiles/`) |
| `.tst` | скрипт команд (см. command-language.md) — **главный способ создавать кейсы с нуля** |
| `.fsw` | Flaresim (XML) |

- Кейс, сохранённый движком (`sym.py … --save X.vsym`), содержит только `.s42`, `.tst`, `_metadata.json`; GUI его
  открывает и сам расставляет значки (без соединительных линий).
- `.tst` внутри — журнал: те же параметры могут задаваться многократно (действует последнее), есть блоки
  `hold`/`go`, `# store …`, `# stored by …`, строки GUI (`displayproperties`, `/..Historian…`, `/X.Info.VMGSimUnitOpTag`).
  `vsym.py tst CASE --clean` убирает шум, `vsym.py specs CASE` — итоговые спецификации.
- Воспроизвести кейс из .tst можно (`sym.py run extracted.tst`), но надёжнее `--recall` исходного .vsym:
  журнал может ссылаться на удалённые объекты/старые версии.
- `_metadata.json`: новый формат (2023) — `root.unitOps[]` с `tp`, `n`, `p`, `os` (статус), `matPortsIn/Out`,
  `enePortsIn/Out` (`conn` — с чем соединён), `vars` (спецификации), `pfd` (координаты); `thermo[]` (пакет,
  компоненты). Старый (2018–2020) — `RootFlowsheet.UnitOperations{тип:{имя:{MatPortsIn…}}}`, `Thermodynamics`;
  `vsym.load_meta()` приводит к новому. Промежуточный (2023, пересохранённые старые кейсы): `RootFlowsheet.unitOps`
  словарь по типам с `matPortsIn` словарями — тоже нормализуется. PFD из GUI целиком — `vsym.py visio`. Статус в старом файле — текст сообщения на момент сохранения.
- Пересохранить старый кейс в новом формате: `sym.py run --recall old.vsym --save new.vsym`.
- Временные файлы движка при recall: `%LOCALAPPDATA%\Temp\Schlumberger\Symmetry_VMGMasterInterface\…`.
- Настройки пользователя: `C:\ProgramData\Schlumberger\Symmetry\Symmetry_x64\MSI.ini` (единицы по умолчанию Field),
  наборы единиц `…\UnitSets\*.set`. Не менять без просьбы.
