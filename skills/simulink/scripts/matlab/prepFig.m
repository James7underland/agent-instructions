function prepFig(fig, axs, W, H)
%PREPFIG  Размеры и шрифт рисунка для отчёта.
%   axs - оси сверху вниз (одинаковой высоты). Поля вокруг сетки оставлены
%   под числа шкал (слева и снизу) и под стрелки с подписями осей
%   (справа и сверху), которые потом рисует crossAxes.
L = 66; R = 92; T = 60; B = 38;
fig.Color = 'w';
fig.Units = 'pixels';
fig.Position = [60 60 W H];
n = numel(axs);
h = (H - n*(T + B))/n;
for i = 1:n
    ax = axs(i);
    ax.Units = 'pixels';
    ax.Position = [L, H - i*(T + h + B) + B, W - L - R, h];
    ax.Color = 'w';
    ax.FontName = 'Times New Roman';
    ax.FontSize = 13;
    title(ax, ''); xlabel(ax, ''); ylabel(ax, '');
    try, ax.Toolbar.Visible = 'off'; catch, end
    try, disableDefaultInteractivity(ax); catch, end
    hold(ax, 'on');
end
end
