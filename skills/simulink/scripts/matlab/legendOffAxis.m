function legendOffAxis(f)
%LEGENDOFFAXIS  Легенда не должна лежать на горизонтальной оси (y = 0):
%   если рамка легенды пересекает ось, легенда сдвигается за неё в ту
%   половину графика, где больше места. Вызывать последним шагом перед
%   экспортом (после commaFig): смена текста легенды меняет её размер,
%   и сдвиг, сделанный раньше, «съезжает».
drawnow;
for ax = findall(f, 'Type', 'axes')'
    lg = ax.Legend;
    if isempty(lg) || ~(ax.YLim(1) < 0 && ax.YLim(2) > 0), continue, end
    ua = ax.Units; ax.Units = 'pixels'; pa = ax.Position; ax.Units = ua;
    ul = lg.Units; lg.Units = 'pixels'; pl = lg.Position;
    y0 = pa(2) + (0 - ax.YLim(1))/diff(ax.YLim)*pa(4);    % ось в пикселях
    g = 6;
    if pl(2) - g < y0 && pl(2) + pl(4) + g > y0
        lg.Location = 'none';
        if ax.YLim(2) > -ax.YLim(1)
            pl(2) = y0 + 10;
        else
            pl(2) = y0 - 10 - pl(4);
        end
        lg.Position = pl;
    end
    lg.Units = ul;
end
drawnow;
end
