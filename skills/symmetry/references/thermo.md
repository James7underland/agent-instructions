# Термодинамика: пакеты свойств и компоненты

Команда: `$RootThermo = VirtualMaterials.<ИмяПакета>` → `/ -> $RootThermo` → `$RootThermo + КОМПОНЕНТЫ`.
Полный список имён пакетов этого движка (`ThermoAdmin.AvPropPkgNames`, проверено):
APRD, APRLK, APRNGL, APRNGL2, APRSolidCO2, **Advanced_Peng-Robinson**, Advanced_Peng-Robinson_HC_HC, Amine,
AmineElectrolyte, BK10, BWR, BWRS, ChaoSeader, Claus, ESRK, FATTY, GasWater, GasWaterMK2, GasWaterMK3, Gasification,
Gasification_2010, Ge_Peng-Robinson, GraysonStreed, IdealLiquid/Ideal/Chemical, IdealLiquid/Ideal/HC, KabadiDannerTwu,
Kalina, LK, LKP, MSRKExp, Margules/Ideal/Chemical, Margules/Ideal/HC, Margules4/Ideal/…, MargulesSOUR, MaxwellBonell,
NGLPR, NH3FlueGasTreating, **NRTL/Ideal/Chemical**, NRTL/Ideal/HC, PSRK, **Peng-Robinson**, PhysicalSolvent, RK,
**RefineryAPR**, RefinerySRK, RefinerySRKLK, SARARegSolModified, SARARegularSolution, **SRK**, Steam95, **Steam97**,
TKWilson/Ideal/…, **UNIFAC/Ideal/Chemical**, UNIQUAC/Ideal/Chemical, Urea2011, Urea40, VMGElectrolyte,
VMGNRTLExtraction, VMGRefPropAGA8, VMGRefPropGERG, VMGRefPropPR, VMGRefprop, VMGScatchardHamer,
**Wilson/Ideal/Chemical**, ZSRK, vanLaar/Ideal/Chemical.
Активностные модели записываются тройкой `Жидкость/Пар/Семейство` (`NRTL/Ideal/Chemical` — NRTL + идеальный газ).

## Что выбирать (по VMGInitScript.txt и примерам)
| Задача | Пакет |
|---|---|
| Природный газ, НГК, углеводороды, нефтепереработка без спецсистем | `Advanced_Peng-Robinson` (стандарт VMG, 230 из 296 примеров) |
| Газ с водой/гликолями/метанолом, гидраты | `APRNGL2` (или APRNGL) |
| Нефтепереработка (крекинг, колонны с псевдокомпонентами) | `RefineryAPR`, `GraysonStreed`, `ChaoSeader`, `BK10` |
| Учебные задачи «по PR/SRK» (как в учебнике) | `Peng-Robinson`, `SRK` |
| Полярные смеси при низком давлении (спирты, вода, кислоты, эфиры) | `NRTL/Ideal/Chemical`, `Wilson/Ideal/Chemical`, `UNIQUAC/Ideal/Chemical`, `UNIFAC/Ideal/Chemical` (предсказательная) |
| Вода/пар (энергетика) | `Steam97` |
| Аминовая очистка | `Amine` (+ операции AmineDetail) |
| Физические абсорбенты | `PhysicalSolvent` |
| Установки Клауса | `Claus` |
| Кислые воды | `MargulesSOUR` |
| Точные плотности/Z газа | `BWRS`, `VMGRefPropGERG`, `VMGRefPropAGA8` |

## Компоненты
- Имена — как в базе VMG, заглавными, пробел → `_`: `METHANE`, `CARBON_DIOXIDE`, `HYDROGEN_SULFIDE`, `n-BUTANE`,
  `ISOBUTANE` (i-BUTANE тоже принимается), `n-HEXANE`, `WATER`, `NITROGEN`, `OXYGEN`, `METHANOL`, `ETHANOL`,
  `BENZENE`, `TOLUENE`, `ETHYLENE_GLYCOL`, `TRIETHYLENE_GLYCOL`, `MONOETHANOLAMINE`, `AMMONIA`, `HYDROGEN`, `CARBON_MONOXIDE`.
- Алиасы (`C:\Program Files\VMG\Symmetry\alias.txt`, 863 шт.): `C1 C2 C3 iC4 nC4 iC5 nC5 nC6 H2O CO2 H2S N2 H2`
  и др. (`O2`, `CO` — **нет**, пишите OXYGEN, CARBON_MONOXIDE) — `$RootThermo + C1 C2 nC4 H2O` работает (проверено). Формулы → имена: `AliasFor.txt` (`CH3OH METHANOL`).
- Поиск имени: `grep -i "метан\\|METHANOL" "C:/Program Files/VMG/Symmetry/alias.txt"`, полный индекс Yaws —
  `yaws.txt` (`"NAME","formula","CAS",…`).
- В выводе движка имена показываются с пробелом (`CARBON DIOXIDE`) — в командах пишите с `_`.
- Порядок компонентов = порядок добавления; векторы `Fraction` задаются в этом порядке. Показать: `$RootThermo`.
- Индексы компонентов (0, 1, …) нужны для формул реакций (`Rxn0.Formula`).

## Опорные состояния
По руководству (`helpdoc.py show "Reference States in VMGSim"`): энтальпия идеального газа каждого компонента = 0 при
0 K и 1 атм, энтропия = 0 при 1 K и 1 атм. Теплоты образования в H потока **не входят**, поэтому через реактор поток
энтальпии не сохраняется (пример 07: адиабатный реактор 244 → 1942 кВт по потокам — это нормально). Для аппаратов без
реакций балансы сходятся до ~1e-15 (check.py). Стандартный объём газа — идеальный газ при 1 атм и 60 °F
(`/StdGasRefT_SI`, `/StdGasRefP_SI` на корневой схеме), стандартный объём жидкости — при `/StdLiqVolRefT` (60 °F).
