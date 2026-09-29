function niceY(ax, xl, lns, pad)
%NICEY  Пределы осей: по X - заданные, по Y - по видимой части кривых,
%   с запасом pad (доля размаха) и округлением до шага делений.
if nargin < 4, pad = 0.05; end
xlim(ax, xl);
lo = Inf; hi = -Inf;
for l = lns(:)'
    k = l.XData >= xl(1) & l.XData <= xl(2);
    lo = min(lo, min(l.YData(k)));
    hi = max(hi, max(l.YData(k)));
end
d = hi - lo;
lo = lo - pad*d; hi = hi + pad*d;
ylim(ax, [lo hi]);
ax.YTickMode = 'auto'; drawnow;
t = ax.YTick; s = t(2) - t(1);
y1 = floor(lo/s + 1e-9)*s; y2 = ceil(hi/s - 1e-9)*s;
ylim(ax, [y1 y2]);
ax.YTick = round((y1:s:y2 + s/1e6)/s)*s;        % деления кратны шагу (через ноль)
ax.XTickMode = 'auto';
end
