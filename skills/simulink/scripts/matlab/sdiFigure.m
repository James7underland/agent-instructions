function [fig, axs, lns] = sdiFigure(series, nRows, W, H)
%SDIFIGURE  График из Simulink: снимок Simulation Data Inspector в фигуру.
%   series - массив структур с полями run (ID прогона в SDI), sig (имя
%   сигнала: x, y, e, g, f) и row (номер графика сверху вниз).
%   Каждый прогон модели записывает сигналы журнала в SDI; снимок строит
%   выбранные сигналы разных прогонов на общих осях (как в окне SDI) и
%   отдаёт их фигурой MATLAB, которую затем оформляем для отчёта.
%   axs - оси сверху вниз, lns{k} - линия k-й записи series.
if nargin < 2, nRows = 1; end

% режим графиков SDI хранится в настройках между сеансами: если хоть раз
% включали XY, снимок приходит пустым - возвращаем обычный график по времени
Simulink.sdi.setSubPlotLayout(nRows, 1);
for r = 1:nRows
    Simulink.sdi.setVisualization(r, 1, 'timeplot');
end

snap = Simulink.sdi.CustomSnapshot;
snap.Rows = nRows; snap.Columns = 1;
snap.Width = W; snap.Height = H;
sigs = cell(1, numel(series));
for k = 1:numel(series)
    run = Simulink.sdi.getRun(series(k).run);
    sigs{k} = run.getSignalsByName(series(k).sig);
    assert(numel(sigs{k}) == 1, 'SDI: в прогоне %d нет сигнала %s', ...
        series(k).run, series(k).sig);
    snap.plotOnSubPlot(series(k).row, 1, sigs{k}, true);
end
fig = Simulink.sdi.snapshot('from', 'custom', 'to', 'figure', 'settings', snap);

% линии дорисовываются асинхронно (первый снимок - до 10 с): ждём, пока
% каждой записи series найдётся своя линия, совпадающая с данными сигнала
t0 = tic;
while true
    drawnow;
    axs = findall(fig, 'Type', 'axes');
    [~, ord] = sort(arrayfun(@(a) a.Position(2), axs), 'descend');
    axs = axs(ord);
    [lns, bad] = match(axs, series, sigs);
    if isempty(bad) && numel(axs) == nRows, break, end
    if toc(t0) > 60
        error('SDI: за 60 с не найдены линии сигналов %s', strjoin({series(bad).sig}, ', '));
    end
    pause(0.5);
end
delete(findall(fig, 'Type', 'legend'));
end

function [lns, bad] = match(axs, series, sigs)
lns = cell(1, numel(series)); bad = [];
used = [];
for k = 1:numel(series)
    if series(k).row > numel(axs), bad(end+1) = k; continue, end %#ok<AGROW>
    v = sigs{k}.Values;
    [tu, iu] = unique(v.Time, 'last');          % на разрывах время повторяется
    yu = double(squeeze(v.Data)); yu = yu(iu);
    best = []; err = Inf;
    % сигналы блоков Step (g, f) SDI рисует ступенькой - объектом Stair
    ax = axs(series(k).row);
    for c = [findall(ax, 'Type', 'line'); findall(ax, 'Type', 'stair')]'
        if any(used == c) || numel(c.XData) < 2, continue, end
        if numel(tu) < 2
            e = max(abs(c.YData - yu(1)));
        else
            yi = interp1(tu, yu, c.XData(:), 'previous', NaN);
            yl = interp1(tu, yu, c.XData(:), 'linear', NaN);
            e = min(max(abs(yi - c.YData(:)), [], 'omitnan'), ...
                    max(abs(yl - c.YData(:)), [], 'omitnan'));
        end
        if e < err, err = e; best = c; end
    end
    if isempty(best) || err > 1e-6
        bad(end+1) = k; %#ok<AGROW>
    else
        lns{k} = best;
        used = [used best]; %#ok<AGROW>
    end
end
end
