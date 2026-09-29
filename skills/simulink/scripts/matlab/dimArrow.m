function dimArrow(ax, t1, t2, y)
%DIMARROW  Размерная линия со стрелками на обоих концах: отрезок [t1, t2]
%   на уровне y (например, период T между двумя соседними пиками).
%   Выносные линии от точек кривой до размерной рисовать отдельно, подпись
%   ставить над серединой. Вызывать после crossAxes (пределы уже заданы).
drawnow;
old = ax.Units; ax.Units = 'pixels'; p = ax.Position; ax.Units = old;
sx = diff(ax.XLim)/p(3); sy = diff(ax.YLim)/p(4);
L = 10; w = 3.5;
plot(ax, [t1 t2], [y y], 'k-', 'LineWidth', 1.0, 'HandleVisibility', 'off');
patch(ax, t1 + [0 L L]*sx, y + [0 w -w]*sy, 'k', 'EdgeColor', 'k', 'HandleVisibility', 'off');
patch(ax, t2 - [0 L L]*sx, y + [0 w -w]*sy, 'k', 'EdgeColor', 'k', 'HandleVisibility', 'off');
end
