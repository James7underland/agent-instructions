function p = slPort(sys, blk, kind, k)
%SLPORT  Координаты порта блока [x y] (пиксели холста Simulink).
%   p = slPort('mdl', 'Объект', 'out', 1)   % выход 1
%   p = slPort('mdl', 'Сумматор', 'in', 2)  % вход 2
%   Нужны, чтобы проводить линии ломаными по точкам: add_line(sys, [p1; ...; p2]).
%   У подсистемы порты появляются только после добавления внутрь In1/Out1 -
%   поэтому сначала заполнить подсистему, потом соединять её снаружи.
if nargin < 4, k = 1; end
ph = get_param([sys '/' blk], 'PortHandles');
switch lower(kind)
    case 'out', h = ph.Outport(k);
    case 'in',  h = ph.Inport(k);
    otherwise,  error('slPort: kind = in | out');
end
p = get_param(h, 'Position');
end
