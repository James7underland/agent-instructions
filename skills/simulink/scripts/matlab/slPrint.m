function slPrint(sys, pdf, fontSize)
%SLPRINT  Снимок модели или подсистемы в PDF (потом crop_pdf.py -> PNG).
%   slPrint('mdl', 'model_top.pdf')           % верхний уровень
%   slPrint('mdl/ПИ-регулятор', 'reg.pdf')    % подсистема
%   fontSize (по умолчанию 16) ставится всем блокам и линиям - при
%   уменьшении рисунка до ширины страницы подписи остаются читаемыми.
%   PNG напрямую не печатаем: Simulink теряет символы (s в 1/(Ts+1)).
if nargin < 3, fontSize = 16; end
mdl = bdroot(sys);
blk = find_system(sys, 'LookUnderMasks', 'all', 'Type', 'block');
for i = 1:numel(blk)
    if strcmp(blk{i}, sys), continue, end
    try, set_param(blk{i}, 'FontSize', fontSize); catch, end
end
lns = find_system(sys, 'FindAll', 'on', 'Type', 'line');
for i = 1:numel(lns)
    try, set_param(lns(i), 'FontSize', fontSize); catch, end
end
open_system(sys);
print(['-s' sys], '-dpdf', pdf);
fprintf('ok: %s (%s)\n', pdf, mdl);
end
