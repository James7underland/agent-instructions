"""Независимая проверка результатов ТАУ-3 (numpy). Многочлены — коэффициенты по убыванию степеней, через пробел.

python check.py roots "1 3 3 1"
python check.py step --num "1.8" --den "3.6 2 1"            # h(t)=L^-1[W/p]: слагаемые (как «Аналитич. формула»), h(∞), перерегулирование
python check.py impulse --num … --den …                        # весовая функция w(t)=L^-1[W]
python check.py closed --wn … --wd … [--rn 1 --rd 1] [--k K]   # Ф = K·R·W/(1+K·R·W): числитель/знаменатель/корни
python check.py freq --num … --den … --w "0.1 1 10"            # |W|, arg W (град), 20lg|W|
python check.py routh "1 2 3 4"                                # таблица Рауса, число правых корней
python check.py lqr --den "2 0 2 1" --q "1 1 1" --p 1          # ANACON: W=1/A(p), x=(y,y',…), R, S, корни замкнутой
python check.py lqrm --A "[[..]]" --B "[[..]]" --Q "1 1" --P "1"   # ANACON2/KALMAN: матричный LQR
python check.py ztf --num … --den … --T 0.5                    # Z-преобразование W(p)/p с экстраполятором 0-го порядка: (1-z^-1)Z{W/p}
python check.py mul "1 2" "1 3"                                # MULPOL
python check.py prony PRONI.DAT --n 4                         # метод Прони: N точек на [0,tmax] (линейная интерполяция)
"""
import sys, argparse, json
import numpy as np


def P(s):
    return np.array([float(x) for x in str(s).replace(',', ' ').split()])


def fmt(z, d=6):
    z = complex(z)
    return ('%.*g' % (d, z.real)) if abs(z.imag) < 1e-9 else '%.*g%+.*gj' % (d, z.real, d, z.imag)


def residues(num, den):
    """Разложение num/den на простые дроби: [(корень, кратность, [коэф при 1/(p-r)^k, k=1..m])]."""
    num = np.trim_zeros(num, 'f'); den = np.trim_zeros(den, 'f')
    r = np.roots(den)
    # сгруппировать кратные корни
    groups = []
    for z in r:
        for g in groups:
            if abs(g[0] - z) < 1e-3 * max(1, abs(z)):
                g[1].append(z); break
        else:
            groups.append([z, [z]])
    res = []
    lead = den[0]
    for z0, zs in groups:
        m = len(zs); z = np.mean(zs)
        others = np.poly([w for g in groups if g[0] is not z0 for w in [np.mean(g[1])] * len(g[1])]) * lead
        # f(p) = num/others ; коэффициент при 1/(p-z)^(m-j) = f^(j)(z)/j!
        cs = []
        fn, fd = np.poly1d(num), np.poly1d(others)
        for j in range(m):
            # производная j-го порядка от fn/fd в точке z (численно через ряд Тейлора)
            h = 1e-3 * max(1, abs(z))
            pts = [z + h * np.exp(2j * np.pi * k / 32) for k in range(32)]
            vals = [fn(p) / fd(p) for p in pts]
            coef = np.mean([v * np.exp(-2j * np.pi * k * j / 32) for k, v in enumerate(vals)]) / h ** j
            cs.append(coef)
        res.append((z, m, cs[::-1]))  # cs[::-1][k-1] — при 1/(p-z)^k
    return res


def time_terms(num, den):
    """Слагаемые f(t) = L^-1[num/den] в виде строк и функция f(t)."""
    terms, parts = [], []
    done = set()
    for z, m, cs in residues(num, den):
        key = (round(z.real, 6), round(abs(z.imag), 6))
        if abs(z.imag) > 1e-9 and key in done:
            continue
        done.add(key)
        for k in range(1, m + 1):
            c = cs[k - 1]
            fact = float(np.prod(range(1, k)))
            if abs(z.imag) < 1e-9:
                a = (c.real / fact)
                if abs(a) < 1e-12: continue
                terms.append('%.5g%s%s' % (a, ' t^%d' % (k - 1) if k > 1 else '', ' exp(%.5gt)' % z.real if abs(z.real) > 1e-12 else ''))
                parts.append(lambda t, a=a, k=k, s=z.real: a * t ** (k - 1) * np.exp(s * t))
            else:
                a, b = 2 * c.real / fact, -2 * c.imag / fact  # 2Re[c e^{zt}] = e^{σt}(2Re c cos ωt − 2Im c sin ωt)
                s, w = z.real, abs(z.imag)
                if z.imag < 0: b = -b
                tk = ' t^%d' % (k - 1) if k > 1 else ''
                terms.append('%.5g%s exp(%.5gt) cos(%.5gt)' % (a, tk, s, w))
                terms.append('%.5g%s exp(%.5gt) sin(%.5gt)' % (b, tk, s, w))
                parts.append(lambda t, a=a, b=b, k=k, s=s, w=w: t ** (k - 1) * np.exp(s * t) * (a * np.cos(w * t) + b * np.sin(w * t)))
    return terms, (lambda t: sum(f(t) for f in parts))


def cancel(num, den, tol=1e-7):
    """Сократить общие корни числителя и знаменателя."""
    num = np.trim_zeros(np.where(abs(num) < 1e-13, 0, num), 'f'); den = np.trim_zeros(np.where(abs(den) < 1e-13, 0, den), 'f')
    rn, rd = list(np.roots(num)), list(np.roots(den))
    for z in list(rn):
        m = [w for w in rd if abs(w - z) < tol * max(1, abs(z))]
        if m:
            rn.remove(z); rd.remove(m[0])
    return np.real(num[0] * np.poly(rn)), np.real(den[0] * np.poly(rd))


def routh(c):
    c = list(c); n = len(c)
    rows = [c[0::2], c[1::2]]
    w = len(rows[0])
    rows = [r + [0.0] * (w - len(r)) for r in rows]
    for i in range(2, n):
        a, b = rows[-2], rows[-1]
        if b[0] == 0: b = b[:]; b[0] = 1e-12
        rows.append([(b[0] * a[j + 1] - a[0] * b[j + 1]) / b[0] if j + 1 < w else 0.0 for j in range(w)])
    first = [r[0] for r in rows]
    changes = sum(1 for x, y in zip(first, first[1:]) if x * y < 0)
    return rows, changes


def lqr(A, B, Q, R):
    n = A.shape[0]
    Ri = np.linalg.inv(R)
    H = np.block([[A, -B @ Ri @ B.T], [-Q, -A.T]])
    w, V = np.linalg.eig(H)
    V = V[:, w.real < 0]
    S = np.real(V[n:] @ np.linalg.inv(V[:n]))
    K = Ri @ B.T @ S
    return K, S, np.linalg.eigvals(A - B @ K)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd'); ap.add_argument('args', nargs='*')
    for o in ('num', 'den', 'wn', 'wd', 'rn', 'rd', 'w', 'q', 'A', 'B', 'Q', 'P'):
        ap.add_argument('--' + o)
    ap.add_argument('--p', type=float, default=1.0); ap.add_argument('--k', type=float, default=1.0)
    ap.add_argument('--T', type=float); ap.add_argument('--n', type=int, default=4)
    ap.add_argument('--tmax', type=float, default=10)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    c = a.cmd
    if c == 'roots':
        print([fmt(z) for z in np.roots(P(a.args[0]))]); return
    if c in ('step', 'impulse'):
        num, den = P(a.num), P(a.den)
        if c == 'step':
            den = np.append(den, 0.0)
        terms, f = time_terms(num, den)
        print('f(t) = сумма:'); [print('  ', t) for t in terms]
        ts = np.linspace(0, a.tmax, 2001); ys = f(ts)
        print('f(0)=%.5g  f(tmax)=%.5g  max=%.5g при t=%.4g' % (ys[0], ys[-1], ys.max(), ts[ys.argmax()]))
        if c == 'step':
            yinf = num[-1] / den[-2] if den[-2] != 0 else float('inf')
            print('h(∞)=%.6g  перерегулирование=%.2f%%' % (yinf, (ys.max() - yinf) / yinf * 100 if yinf else 0))
        return
    if c == 'closed':
        wn, wd = P(a.wn), P(a.wd)
        rn, rd = P(a.rn or '1'), P(a.rd or '1')
        n = a.k * np.polymul(rn, wn); d = np.polyadd(np.polymul(rd, wd), n)
        print('num', n.round(8).tolist()); print('den', d.round(8).tolist()); print('roots', [fmt(z) for z in np.roots(d)]); return
    if c == 'freq':
        num, den = P(a.num), P(a.den)
        for w in P(a.w):
            v = np.polyval(num, 1j * w) / np.polyval(den, 1j * w)
            print('w=%-8g |W|=%-10.6g arg=%-9.4f° 20lg=%-9.4f Re=%-10.6g Im=%.6g' % (w, abs(v), np.degrees(np.angle(v)), 20 * np.log10(abs(v)), v.real, v.imag))
        return
    if c == 'routh':
        rows, ch = routh(list(P(a.args[0])))
        for r in rows: print(['%.6g' % x for x in r])
        print('смен знака в 1-м столбце (правых корней):', ch); return
    if c == 'lqr':
        den = P(a.den); n = len(den) - 1
        A = np.zeros((n, n)); A[:-1, 1:] = np.eye(n - 1); A[-1, :] = -den[:0:-1] / den[0]
        B = np.zeros((n, 1)); B[-1, 0] = 1 / den[0]
        K, S, ev = lqr(A, B, np.diag(P(a.q)), np.array([[a.p]]))
        print('R =', K.round(5).tolist()); print('S =', S.round(5).tolist()); print('корни:', [fmt(z, 5) for z in ev]); return
    if c == 'lqrm':
        A = np.array(json.loads(a.A), float); B = np.array(json.loads(a.B), float)
        K, S, ev = lqr(A, B, np.diag(P(a.Q)), np.diag(P(a.P)))
        print('R =', K.round(5).tolist()); print('S =', S.round(5).tolist()); print('корни:', [fmt(z, 5) for z in ev]); return
    if c == 'ztf':
        # Z{W(p)/p} через вычеты: sum Res[W(p)/p * z/(z-e^{pT})], затем * (z-1)/z
        num, den, T = P(a.num), np.append(P(a.den), 0.0), a.T
        zn = np.array([0.0]); zd = np.array([1.0])
        for z0, m, cs in residues(num, den):
            if m > 1:
                print('кратные корни — не поддержано'); return
            e = np.exp(z0 * T)
            # c/(p-z0) -> c z/(z-e)
            zn = np.polyadd(np.polymul(zn, [1, -e]), np.polymul(zd, [cs[0], 0]))
            zd = np.polymul(zd, [1, -e])
        zn = np.polymul(zn, [1, -1]); zd = np.polymul(zd, [1, 0])
        zn, zd = cancel(np.real(zn), np.real(zd))
        print('D(z)=num/den, num', np.real(zn).round(8).tolist(), 'den', np.real(zd).round(8).tolist())
        print('полюса', [fmt(z) for z in np.roots(np.real(zd))]); return
    if c == 'mul':
        print(np.polymul(P(a.args[0]), P(a.args[1])).tolist()); return
    if c == 'prony':
        # как в PRONI: N (чётное) равноотстоящих точек на [0, tmax] включая t=0; n = N/2 экспонент
        d = np.loadtxt(a.args[0]); t, y = d[:, 0], d[:, 1]
        N = a.n; n = N // 2
        ts = np.linspace(0, t[-1], N); ys = np.interp(ts, t, y); h = ts[1] - ts[0]
        M = np.array([ys[i:i + n] for i in range(n)]); rhs = -ys[n:2 * n]
        cf = np.linalg.solve(M, rhs)
        zs = np.roots(np.concatenate(([1], cf[::-1])))
        lam = np.log(zs.astype(complex)) / h
        V = np.array([[z ** k for z in zs] for k in range(N)])
        amp = np.linalg.lstsq(V, ys.astype(complex), rcond=None)[0]
        print('точки t:', ts.round(4).tolist())
        for A_, l in zip(amp, lam): print('%s * exp(%s t)' % (fmt(A_), fmt(l)))
        return
    ap.error('команда?')


if __name__ == '__main__':
    main()
