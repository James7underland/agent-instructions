# Единицы измерения Mathcad 13 (система SI)

Источник: `C:\Program Files (x86)\Mathsoft\Mathcad 13\units\unit-system-SI.xml` (145 единиц; есть также
`-MKS`, `-CGS`, `-US`, `-None`). Система листа задаётся в `<settings><calculation><units><currentUnitSystem name="si"/>`.
Внутри Mathcad всё хранится в базовых СИ (kg, m, s, A, K, mol, cd); `GetValue` через COM возвращает число
**в базовых СИ без единицы** (например `σ = 150 MPa` → `150000000`).

## Чего НЕТ (частые ошибки)
`kPa`, `kJ`, `MJ`, `MN`, `kNm`, `tf` (есть `tonf`), `cm2`, `Gcal`, `t` (тонна — это `tonne`).
Нужное определяйте в начале листа: `kPa := 1000*Pa`, `MN := 1000*kN`, `kJ := 1000*J`, `tf := 1000*kgf`.
Грамм — `gm` (не `g`!), `g` = 9.80665 m/s² (ускорение свободного падения).

## Полный список (символ = имя)

**Длина:** m, cm, mm, km, μm/micron, nm, in, ft, yd, mi, nmi, mil, Angstrom, a.0/bohr, cubit, furlong, FIF
**Площадь/объём:** acre, hectare, barn, L/l/liter, mL, gal, galUK, fl_oz
**Масса:** kg, gm, mg, tonne, lb, oz, slug, ton
**Время:** s/sec, ms, μs, min, hr, day, yr, fortnight, hhmmss
**Сила:** N/newton, kN, kgf, tonf, dyne, lbf, kip; погонная: klf, plf
**Давление/напряжение:** Pa, MPa, GPa, bar, atm, torr, psi, ksi, psf, ksf, in_Hg
**Энергия:** J/joule, erg, cal, kcal, BTU (+ BTU15, CBTU, IBTU, mBTU, tBTU, cal15, cal20, dcal, mcal, tcal)
**Мощность:** W/watt, kW, MW, mW, hp, bhp, ehp, mhp, hhp, hpUK
**Температура:** K, R (Ренкин), °C, °F, Δ°C, Δ°F  (°C/°F — функции-единицы: `°C(20)`; разности — Δ°C)
**Угол:** rad, deg, sr, DMS
**Скорость/частота:** kph, mph, knot, c (скорость света); Hz, kHz, MHz, GHz, Hza (угловая)
**Электричество:** A/amp, mA, μA, kA; V/volt, mV, kV; Ω/ohm, kΩ, MΩ; C/coul; F/farad, μF, nF, pF; H/henry, mH, μH; S/mho/siemens
**Магнетизм/свет:** Wb, T/tesla, G/gauss, Oe, cd, lm, lx
**Прочее:** mol/mole, katal, Bq, Gy, Sv, poise, stokes, gpm, pcf, pci, μ.0, ε.0, g

## Вывод результата в нужных единицах
`σ = MPa` в линейном синтаксисе → `ml:unitOverride`. Без него Mathcad показывает базовые/упрощённые
единицы (в шаблоне `minimal20.xmcd` включено `format-units="true" simplify-units="true"`, поэтому
`kg·m⁻¹·s⁻²` показывается как `Pa`, а момент `N·m` — как `J`; для момента явно пишите `M = kN*m`).
