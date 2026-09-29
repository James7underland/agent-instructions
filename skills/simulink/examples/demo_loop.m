%% Пример скилла simulink: модель контура, два прогона, график из SDI, снимок модели
% Запуск: python <скилл>/scripts/mlrun.py --cd <скилл>/examples "demo_loop(pwd)"
% Результат в папке out: demo_x.png (график), demo_model.pdf/.png (модель).
function demo_loop(outdir)
out = fullfile(outdir, 'out');
if ~exist(out, 'dir'), mkdir(out); end
try
    s = settings; s.matlab.appearance.figure.GraphicsTheme.TemporaryValue = 'light';
catch
end

%% модель: g -> (+-) -> ПИ -> объект 1/(T s + 1) с запаздыванием -> x
mdl = 'demo_loop_mdl';
if bdIsLoaded(mdl), close_system(mdl, 0); end
new_system(mdl);
add = @(src, name, pos, varargin) add_block(src, [mdl '/' name], 'Position', pos, varargin{:});
add('simulink/Sources/Step', 'Задание', [40 185 80 215], 'Time', '0', 'Before', '0', 'After', '1');
add('simulink/Math Operations/Sum', 'Сумматор', [150 185 180 215], ...
    'Inputs', '|+-', 'IconShape', 'round', 'ShowName', 'off');
add('simulink/Continuous/PID Controller', 'ПИ-регулятор', [260 175 360 225], ...
    'Controller', 'PI', 'P', 'Kp', 'I', 'Ki');
add('simulink/Continuous/Transfer Fcn', 'Объект', [440 175 540 225], 'Denominator', '[5 1]');
add('simulink/Continuous/Transport Delay', 'Запаздывание', [610 175 710 225], 'DelayTime', '1');
add('simulink/Sinks/Scope', 'Осциллограф', [850 180 890 220]);
Lg = slWire(mdl, 'Задание', 1, 'Сумматор', 1);
Le = slWire(mdl, 'Сумматор', 1, 'ПИ-регулятор', 1);
slWire(mdl, 'ПИ-регулятор', 1, 'Объект', 1);
slWire(mdl, 'Объект', 1, 'Запаздывание', 1);
Lx = slWire(mdl, 'Запаздывание', 1, 'Осциллограф', 1);
p = slPort(mdl, 'Запаздывание', 'out', 1); q = slPort(mdl, 'Сумматор', 'in', 2);
add_line(mdl, [p(1) + 60 p(2); p(1) + 60 300; q(1) 300; q]);   % обратная связь снизу
set_param(Lg, 'Name', 'g'); set_param(Le, 'Name', 'e'); set_param(Lx, 'Name', 'x');
slLog(mdl, 'Задание'); slLog(mdl, 'Запаздывание');
set_param(mdl, 'StopTime', '40', 'MaxStep', '0.01', 'SignalLogging', 'on', ...
    'SignalLoggingName', 'logsout');
hws = get_param(mdl, 'ModelWorkspace');       % модель запускается и кнопкой Run
assignin(hws, 'Kp', 1.0); assignin(hws, 'Ki', 0.4);
save_system(mdl, fullfile(out, [mdl '.slx']));

%% два прогона с разными настройками -> SDI
Simulink.sdi.clear;
Simulink.sdi.setAutoArchiveMode(false);
K = [1.0 0.4; 2.0 0.6];                      % [Kp Ki]
runs = zeros(1, 2);
for i = 1:2
    in = Simulink.SimulationInput(mdl);
    in = in.setVariable('Kp', K(i, 1), 'Workspace', mdl).setVariable('Ki', K(i, 2), 'Workspace', mdl);
    sim(in);
    ids = Simulink.sdi.getAllRunIDs; runs(i) = ids(end);
end

%% график: задание g и выход x двух прогонов
S = struct('run', {runs(1), runs(1), runs(2)}, 'sig', {'g', 'x', 'x'}, 'row', 1);
[f, axs, ln] = sdiFigure(S, 1, 820, 470);
ax = axs(1);
prepFig(f, ax, 820, 470);
set(ln{1}, 'Color', 'k', 'LineWidth', 1.2, 'LineStyle', '--');
set(ln{2}, 'Color', [0 0.3 0.85], 'LineWidth', 1.8);
set(ln{3}, 'Color', [0.85 0.15 0.1], 'LineWidth', 1.8);
niceY(ax, [0 40], [ln{:}]);
putLegend(ax, [ln{:}], {'{\itg}({\itt})', sprintf('{\\itK}_p = %.1f, {\\itK}_i = %.1f', K(1, :)), ...
    sprintf('{\\itK}_p = %.1f, {\\itK}_i = %.1f', K(2, :))}, 'southeast');
crossAxes(ax, '{\itt}, с', '{\itg}, {\itx}');
commaFig(f);
legendOffAxis(f);
exportgraphics(f, fullfile(out, 'demo_x.png'), 'Resolution', 200);
close(f);

%% снимок модели
slPrint(mdl, fullfile(out, 'demo_model.pdf'));
close_system(mdl, 0);
fprintf('Готово: %s\n', out);
end
