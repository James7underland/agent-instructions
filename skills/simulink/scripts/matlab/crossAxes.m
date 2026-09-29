function crossAxes(ax, xlab, ylab)
%CROSSAXES  Оформление осей графика для отчёта.
%   Оси - жирные линии через ноль (если ноль вне диапазона - по краю
%   сетки), на концах стрелки за пределами сетки, подписи осей у стрелок:
%   горизонтальной - справа от острия, вертикальной - над остриём.
%   Числа шкал - по нижнему и левому краю сетки (у оси, проходящей через
%   середину графика, их закрывали бы кривые). Десятичная запятая.
%   Вызывать после того, как заданы пределы осей и положение axes.
drawnow;
xl = ax.XLim; yl = ax.YLim;
ax.XLimMode = 'manual'; ax.YLimMode = 'manual';
xt = ax.XTick; yt = ax.YTick;
ax.XTickMode = 'manual'; ax.YTickMode = 'manual';

% --- сетка без рамки и без встроенных шкал ---
box(ax, 'off'); grid(ax, 'on');
ax.XColor = 'none'; ax.YColor = 'none';
ax.GridColor = [0.72 0.72 0.72]; ax.GridAlpha = 1; ax.GridLineStyle = '-';
ax.Layer = 'bottom';
xlabel(ax, ''); ylabel(ax, ''); title(ax, '');

% --- масштаб: сколько единиц данных в одном пикселе ---
old = ax.Units; ax.Units = 'pixels'; p = ax.Position; ax.Units = old;
sx = diff(xl)/p(3); sy = diff(yl)/p(4);

x0 = 0; if x0 < xl(1) || x0 > xl(2), x0 = xl(1); end   % вертикальная ось
y0 = 0; if y0 < yl(1) || y0 > yl(2), y0 = yl(1); end   % горизонтальная ось
ext = 24;  L = 12;  w = 4;  lw = 1.4;                  % вынос, стрелка, толщина, px
fs = ax.FontSize; fn = ax.FontName;

% горизонтальная ось со стрелкой
xtip = xl(2) + ext*sx;
line(ax, [xl(1) xtip - L*sx], [y0 y0], 'Color', 'k', 'LineWidth', lw, ...
    'Clipping', 'off', 'HandleVisibility', 'off');
patch(ax, xtip - [0 L L]*sx, y0 + [0 w -w]*sy, 'k', 'EdgeColor', 'k', ...
    'Clipping', 'off', 'HandleVisibility', 'off');
text(ax, xtip + 5*sx, y0, xlab, 'FontSize', fs + 1, 'FontName', fn, ...
    'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle', 'Clipping', 'off', 'Interpreter', 'tex');

% вертикальная ось со стрелкой
ytip = yl(2) + ext*sy;
line(ax, [x0 x0], [yl(1) ytip - L*sy], 'Color', 'k', 'LineWidth', lw, ...
    'Clipping', 'off', 'HandleVisibility', 'off');
patch(ax, x0 + [0 w -w]*sx, ytip - [0 L L]*sy, 'k', 'EdgeColor', 'k', ...
    'Clipping', 'off', 'HandleVisibility', 'off');
text(ax, x0, ytip + 5*sy, ylab, 'FontSize', fs + 1, 'FontName', fn, ...
    'HorizontalAlignment', 'center', 'VerticalAlignment', 'bottom', 'Clipping', 'off', 'Interpreter', 'tex');

% числа шкал
for v = xt
    if abs(v - x0) < 1e-12 && abs(y0 - yl(1)) < 1e-12 && x0 == xl(1) ...
            && any(abs(yt - y0) < 1e-12)
        continue                         % «0» в углу ставится один раз (по Y)
    end
    text(ax, v, yl(1) - 6*sy, num(v), 'FontSize', fs, 'FontName', fn, ...
        'HorizontalAlignment', 'center', 'VerticalAlignment', 'top', 'Clipping', 'off', 'Interpreter', 'tex');
end
for v = yt
    text(ax, xl(1) - 7*sx, v, num(v), 'FontSize', fs, 'FontName', fn, ...
        'HorizontalAlignment', 'right', 'VerticalAlignment', 'middle', 'Clipping', 'off', 'Interpreter', 'tex');
end
end

function s = num(v)
s = strrep(num2str(round(v, 9)), '.', ',');
s = strrep(s, '-', char(8722));          % типографский минус
end
