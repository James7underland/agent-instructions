function fitLegend(ax, lns)
%FITLEGEND  Легенда не должна закрывать кривые: пока под рамкой легенды
%   есть точки кривых, сетка расширяется на одно деление в сторону
%   легенды (вверх, если легенда в верхней половине, иначе вниз).
lg = ax.Legend;
if isempty(lg), return, end
% легенда не должна закрывать горизонтальную ось (y = 0): сдвигаем её
% за ось в свою половину графика
if ax.YLim(1) < 0 && ax.YLim(2) > 0
    drawnow;
    [~, ~, y1, y2] = boxData(ax, lg);
    if y1 < 0 && y2 > 0
        ua = ax.Units; ax.Units = 'pixels'; pa = ax.Position; ax.Units = ua;
        ul = lg.Units; lg.Units = 'pixels'; pl = lg.Position;
        y0 = pa(2) + (0 - ax.YLim(1))/diff(ax.YLim)*pa(4);
        lg.Location = 'none';
        if ax.YLim(2) > -ax.YLim(1)          % сверху от оси места больше
            pl(2) = y0 + 10;
        else
            pl(2) = y0 - 10 - pl(4);
        end
        lg.Position = pl; lg.Units = ul;
    end
end
for it = 1:8
    drawnow;
    [x1, x2, y1, y2] = boxData(ax, lg);
    hit = false;
    for l = lns(:)'
        k = l.XData >= x1 & l.XData <= x2 & l.YData >= y1 & l.YData <= y2;
        if any(k), hit = true; break, end
    end
    if ~hit, return, end
    s = ax.YTick(2) - ax.YTick(1);
    ax.YTickMode = 'manual';
    if (y1 + y2)/2 > mean(ax.YLim)
        ax.YLim(2) = ax.YLim(2) + s;
    else
        ax.YLim(1) = ax.YLim(1) - s;
    end
    ax.YTick = round((ax.YLim(1):s:ax.YLim(2) + s/1e6)/s)*s;
end
warning('fitLegend: легенда всё ещё закрывает кривую');
end

function [x1, x2, y1, y2] = boxData(ax, lg)
% рамка легенды (с зазором 6 px) в единицах данных
u = ax.Units; ax.Units = 'pixels'; pa = ax.Position; ax.Units = u;
u = lg.Units; lg.Units = 'pixels'; pl = lg.Position; lg.Units = u;
g = 6;
fx = @(px) ax.XLim(1) + (px - pa(1))/pa(3)*diff(ax.XLim);
fy = @(py) ax.YLim(1) + (py - pa(2))/pa(4)*diff(ax.YLim);
x1 = fx(pl(1) - g); x2 = fx(pl(1) + pl(3) + g);
y1 = fy(pl(2) - g); y2 = fy(pl(2) + pl(4) + g);
end
