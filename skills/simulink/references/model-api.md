# Шпаргалка: модель Simulink из кода (R2025b)

## Каркас
```matlab
mdl = 'sar';
if bdIsLoaded(mdl), close_system(mdl, 0); end
new_system(mdl);
add_block('simulink/Sources/Step', [mdl '/Задание'], 'Position', [40 285 80 315], ...
    'Time', '0', 'Before', '0', 'After', 'G');          % параметры - имена переменных
...
set_param(mdl, 'StopTime', 'Tstop', 'Solver', 'ode45', 'RelTol', '1e-6', ...
    'AbsTol', '1e-8', 'MaxStep', '0.01', 'SignalLogging', 'on', 'SignalLoggingName', 'logsout');
save_system(mdl, fullfile(outdir, [mdl '.slx']));
```
`Position` = [лево верх право низ] в пикселях холста; y растёт вниз. Держать основной контур на одной
горизонтали (порты на одной высоте → прямые линии), шаг между блоками ≥ 80 px.

## Блоки, которые уже использовались
| Блок | Путь | Параметры |
|---|---|---|
| Ступенька | `simulink/Sources/Step` | `Time`, `Before`, `After` |
| Часы (время/аргумент) | `simulink/Sources/Clock` | — |
| Сумматор круглый | `simulink/Math Operations/Sum` | `Inputs '|+-'`, `IconShape 'round'`, `ShowName 'off'` |
| Усилитель | `simulink/Math Operations/Gain` | `Gain 'P1'` |
| Интегратор | `simulink/Continuous/Integrator` | — |
| Передаточная функция | `simulink/Continuous/Transfer Fcn` | `Numerator '[1]'`, `Denominator '[5.2 1]'` |
| Запаздывание | `simulink/Continuous/Transport Delay` | `DelayTime 'tau'` |
| Функция | `simulink/User-Defined Functions/Fcn` | `Expr` (вход — `u`, можно переменные рабочей области) |
| Модуль | `simulink/Math Operations/Abs` | — |
| Квадрат | `simulink/Math Operations/Math Function` | `Function 'square'` |
| Максимум | `simulink/Math Operations/MinMax` | `Function 'max'`, `Inputs '2'` |
| Память | `simulink/Discrete/Memory` | `InitialCondition '0'`, `Orientation 'left'` (обратная связь) |
| Ключ | `simulink/Signal Routing/Switch` | `Criteria 'u2 >= Threshold'`, `Threshold 'Delta'` |
| Сравнение | `simulink/Logic and Bit Operations/Compare To Constant` | `relop '<'`, `const '0'` |
| Останов | `simulink/Sinks/Stop Simulation` | — |
| Осциллограф | `simulink/Sinks/Scope` | — |
| Дисплей | `simulink/Sinks/Display` | — |
| XY Graph (новый) | `simulink/Sinks/XY Graph` | 2 входа: X, Y |
| Порты подсистемы | `simulink/Sources/In1`, `simulink/Sinks/Out1` | имя блока = подпись порта |
| Подсистема | `slNewSubsystem(path, pos)` | пустая, без In1→Out1 |

## Линии
```matlab
L = slWire(mdl, 'Задание', 1, 'Сумматор1', 1);          % прямая / ломаная через середину
p = slPort(mdl, 'Запаздывание', 'out', 1); q = slPort(mdl, 'Сумматор1', 'in', 2);
add_line(mdl, [p(1)+80 p(2); p(1)+80 470; q(1) 470; q]);  % ответвление: первая точка - на линии
set_param(L, 'Name', 'g');                                % подпись линии = имя сигнала в журнале
slLog(mdl, 'Задание');                                    % журналирование выхода блока
```

## Значения по умолчанию — в самой модели (обязательно)
Модель должна запускаться кнопкой Run без скриптов. Все переменные, на которые ссылаются блоки и
настройки (`P1`, `tau`, `Tstop`…), кладём в Model Workspace перед `save_system`:
```matlab
hws = get_param(mdl, 'ModelWorkspace');
assignin(hws, 'P1', 2.5717); assignin(hws, 'Tstop', 200);   % ... все переменные модели
save_system(mdl, file);
```
Проверка: свежий MATLAB → `load_system(file); sim(mdl)` — без ошибок.

## Прогоны
```matlab
in = Simulink.SimulationInput(mdl);
% переопределять там же, где лежат значения по умолчанию, - в Model Workspace
in = in.setVariable('P1', 2.57, 'Workspace', mdl).setVariable('Tstop', 200, 'Workspace', mdl);
out = sim(in);
x = out.logsout.getElement('x').Values;       % timeseries: x.Time, squeeze(x.Data)
ids = Simulink.sdi.getAllRunIDs; run = ids(end);   % тот же прогон в SDI - для графика
```
Переменные Model Workspace заслоняют базовую рабочую область, поэтому `setVariable` — с `'Workspace', mdl`,
и `assignin('base', ...)` на такую модель не действует.
Для снимка модели с живыми значениями на Display: записать нужные значения в Model Workspace
(`assignin(hws, ...)`, заодно `save_system` — пусть сданная модель по Run показывает то же) → `sim(mdl)` →
`slPrint`.

## Модель как «калькулятор» кривой (пример: линии равного затухания)
Fixed-step discrete, `StartTime`/`StopTime`/`FixedStep` задают сетку аргумента; Clock выдаёт аргумент,
Fcn считают функции, Compare To Constant + Stop Simulation обрывают расчёт по условию (последний шаг —
уже за границей, его отбрасывать). Результат — из `out.logsout`.
