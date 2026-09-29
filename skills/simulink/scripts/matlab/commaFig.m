function commaFig(f)
%COMMAFIG  Десятичная запятая в подписях осей, легендах и надписях рисунка.
%   Заодно в строках с TeX-разметкой ({\it..}, индексы) обычный пробел
%   заменяется пробелом 1/3 em (U+2004): интерпретатор tex рисует обычный
%   пробел вдвое шире, и «t, с», «m = 0» выглядят разорванными.
drawnow;
for ax = findall(f, 'Type', 'axes')'
    for name = {'XAxis', 'YAxis'}
        r = ax.(name{1});
        t = r.TickValues;
        r.TickValues = t;                         % зафиксировать деления
        r.TickLabels = arrayfun(@(v) strrep(num2str(round(v, 9)), '.', ','), ...
            t, 'UniformOutput', false);
    end
end
for lg = findall(f, 'Type', 'legend')'
    lg.String = cellfun(@fix, lg.String, 'UniformOutput', false);
end
for tx = findall(f, 'Type', 'text')'
    if ischar(tx.String) || isstring(tx.String)
        tx.String = fix(char(tx.String));
    end
end
end

function s = fix(s)
s = strrep(s, '.', ',');
if any(ismember(s, '{}_^\'))
    s = strrep(s, ' ', char(8196));
end
end
