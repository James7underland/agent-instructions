function L = slWire(sys, src, ks, dst, kd, xm)
%SLWIRE  Линия от выхода ks блока src к входу kd блока dst.
%   На одной высоте - прямая; иначе ломаная с вертикальным участком на
%   x = xm (по умолчанию посередине). Возвращает handle линии (для имени:
%   set_param(L, 'Name', 'x')).
%   Ответвление от существующей линии: add_line(sys, [x_ветвл y_линии; ...; вход])
%   - начальная точка должна лежать на линии.
a = slPort(sys, src, 'out', ks);
b = slPort(sys, dst, 'in', kd);
if abs(a(2) - b(2)) < 1
    L = add_line(sys, [a; b]);
else
    if nargin < 6 || isempty(xm), xm = round((a(1) + b(1))/2); end
    L = add_line(sys, [a; xm a(2); xm b(2); b]);
end
end
