function putLegend(ax, h, strs, loc)
%PUTLEGEND  Легенда в стиле отчёта; сетка расширяется, если легенда
%   закрывает кривые (fitLegend). Вызывать до crossAxes.
lg = legend(ax, h, strs, 'Location', loc);
lg.FontName = 'Times New Roman'; lg.FontSize = 13;
lg.Interpreter = 'tex'; lg.Color = 'w'; lg.EdgeColor = [0.3 0.3 0.3];
lg.AutoUpdate = 'off';
fitLegend(ax, h);
end
