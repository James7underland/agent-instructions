# Формулы в .xmcd: элементы Math20 и линейный синтаксис xmcd.py

Источник: скан 214 листов формата v2.0 из `qsheet\` (4485 формул, ~90 типов элементов) + `schema\Math20.xsd`
(92 элемента). Сырой дамп с частотами, атрибутами и примерами: `math-xml-corpus-dump.txt`.
Префикс `ml:` = `http://schemas.mathsoft.com/math20` (в файлах Mathcad 12 — `.../math10`, структура та же).

## Верхний уровень формулы (`<math>` в регионе)

| Линейно (xmcd.py) | XML | Примечание |
|---|---|---|
| `x := e` | `<ml:define><lhs/><rhs/></ml:define>` | Mathcad добавляет `warning="WarnRedefinedBIUnit"` и т.п., если имя совпало со встроенным |
| `f(x, y) := e` | `<ml:define><ml:function><ml:id>f</ml:id><ml:boundVars>x y</ml:boundVars></ml:function>e</ml:define>` | |
| `v[i] := e` | `<ml:define><ml:apply><ml:indexer/>v i</ml:apply>e</ml:define>` | |
| `x :== e` (≡) | `<ml:globalDefine>` | вычисляется до всех обычных определений |
| `e =` | `<ml:eval>e<result>…</result></ml:eval>` | `<result>` пишет Mathcad при сохранении (`save-numeric-results="true"`) |
| `e = kN*m` | `<ml:eval>e<ml:unitOverride>kN*m</ml:unitOverride></ml:eval>` | результат тогда хранится уже в этих единицах |
| `e ->` / `e -> simplify` / `e -> solve, x` | `<ml:symEval style="default" hide-keywords="false" hide-lhs="false">e<ml:command>…</ml:command>*<ml:symResult>…</ml:symResult></ml:symEval>` | команда: `<ml:id>simplify</ml:id>` или `<ml:sequence><ml:id>solve</ml:id><ml:id>x</ml:id></ml:sequence>`; цепочка — несколько `ml:command` |
| `Given` | `<ml:id>Given</ml:id>` | просто идентификатор в отдельном регионе |
| `a == b` | `<ml:apply><ml:equal/>a b</ml:apply>` | «жирное» равно (Ctrl+=) — ограничение в solve block |
| `x := Find(x, y)` | `<ml:apply><ml:Find auto-method=… /><ml:sequence>x y</ml:sequence></ml:apply>` | также `Minerr`, `Minimize`, `Maximize`, `Odesolve`, `polyroots`, `genfit`, `Pdesolve`, `numol` |
| `!x := 2` | `<math disable-calc="true">` | отключённая (не вычисляемая) формула |

Корень `<math>`: `<math optimize="false" disable-calc="false">…</math>`; после выражения может идти
`<resultFormat>` (формат вывода только этого региона). Выражение может быть обёрнуто в `<ml:provenance>` (след
копирования; служебные дети `originRef/parentRef/comment/contentHash` — пропускать).

**Атрибуты решателей** (по умолчанию в xmcd.py): `Find/Minimize/Maximize` — `auto-method="true" method="conjugate"
derivative-estimation="central" variable-estimation="tangent" linear-check multistart evolutionary="false"`;
`Minerr` — `auto-method="false" method="levenberg"` (с auto-method ответ МНК неверный); `Odesolve method=
adaptive|fixed|stiff`; `polyroots method=laguerre|companion-matrix`; `genfit method="optimized levenberg-marquardt"`
(**обязателен по схеме**). Векторная левая часть: `[xa; ya] := Odesolve([xa; ya], τ, 3)`, `[α1; β1] := Minerr(α, β)`.

### Формат результата (`@…` в конце строки build)
`σ = MPa @prec=2 zeros` → `<resultFormat><general precision="2" show-trailing-zeros="true" radix="dec"
complex-threshold="10" exponential-threshold="3"/><matrix display-style="auto" expand-nested-arrays="false"/>
<unit format-units="true" simplify-units="true"/></resultFormat>`. Опции: `prec=N` (знаков после запятой),
`zeros`, вид `gen|dec|sci|eng` (элементы `general/decimal/scientific/engineering`; `fraction` тоже есть в схеме),
`exp=N` (порог экспоненты для general), `matrix|table` (вывод массива). Без `@matrix` вектор длиннее 9
показывается прокручиваемой таблицей и в экспорт попадают 16 строк.

### Символьные команды (проверено; синтаксис после `->`, цепочка через `|`)
| Команда | Пример | Результат |
|---|---|---|
| `simplify`, `expand`, `factor` | `x^2 - 5*x + 6 -> factor` | `(x−2)(x−3)` |
| `collect, x` | `a*x^2 + b*x^2 + a*x -> collect, x` | `(a+b)x² + ax` |
| `coeffs, x` | `3*x^3 + 2*x - 7 -> coeffs, x` | `[−7; 2; 0; 3]` |
| `substitute, a == 2` | `x^2 + a1 -> substitute, a1 == 2` | `x² + 2` |
| `solve, x` / `float, N` / `complex` | `P(s) -> solve, s \| float, 4` | вектор корней |
| `series, x == 0, N` | `exp(x) -> series, x == 0, 4` | `1 + x + x²/2 + x³/6` |
| `convert, parfrac, x` | дробь `-> convert, parfrac, x` | простые дроби |
| `assume, a > 0` | `int(exp(-a*t), t, 0, ∞) -> assume, a > 0` | `1/a` |
| `laplace, t` / `invlaplace, s` | `1/(s*(s + 1)) -> invlaplace, s` | `1 − e^(−t)` |
| `ztrans, n` / `invztrans, z` | `n -> ztrans, n` | `z/(z−1)²` |
| `fourier, t` / `invfourier, ω` | `cos(2*π*τ/τ0) -> fourier, τ` | δ-функции `Δ(…)` |
| `explicit` | показывает выражение с подставленными значениями | |
В XML: `<ml:command><ml:id>simplify</ml:id></ml:command>` или `<ml:command><ml:sequence><ml:id>laplace</ml:id>
<ml:id>t</ml:id></ml:sequence></ml:command>`. `s` и `t` в символьных выражениях допустимы, хотя это единицы.

### Текст (`text` регион)
`<p style="Normal">обычный <b>жирный</b> <i>курсив</i> <u>подчёркнутый</u> σ<sub>max</sub> м<sup>2</sup><br/>…</p>`,
также `<f family=… size=…>`, `<tab/>`. В build: `**жирный**`, `*курсив*`, `_{sub}`, `^{sup}`; строка `---` —
регион `<pageBreak/>`.

## Выражения

| Линейно | XML |
|---|---|
| `2.5`, `1.5e-3` | `<ml:real>2.5</ml:real>` (экспоненту xmcd.py разворачивает: `0.0015`); атрибут `base="16"`/`2` для hex/bin |
| `4i`, `3 + 4i` | `<ml:imag symbol="i">4</ml:imag>`; результат-комплекс: `<ml:complex><ml:real/><ml:imag/></ml:complex>` |
| `x`, `σ.max` | `<ml:id xml:space="preserve">x</ml:id>`, `<ml:id subscript="max">σ</ml:id>` (литеральный индекс) |
| `"text"` | `<ml:str xml:space="preserve">text</ml:str>` — **только ASCII** (кириллица портится) |
| `(e)` | `<ml:parens>e</ml:parens>` — явные скобки хранятся отдельно |
| `a + b`, `a - b`, `a*b`, `a/b`, `a^b` | `<ml:apply><ml:plus/>a b</ml:apply>`, `minus`, `mult style="default"`, `div`, `pow` |
| `-a` | `<ml:apply><ml:neg/>a</ml:apply>` |
| `10 kN`, `2 m^2` | число + единица = неявное умножение → `ml:mult` (единицы — обычные `ml:id`) |
| `a < b` `<=` `>` `>=` `!=` | `lessThan`, `lessOrEqual`, `greaterThan`, `greaterOrEqual`, `notEqual` |
| `a and b`, `or`, `xor`, `not(a)` | `and`, `or`, `xor`, `not` |
| `n!` | `<ml:apply><ml:factorial/>n</ml:apply>` |
| `f(x)`, `f(x, y)` | `<ml:apply><ml:id>f</ml:id>x</ml:apply>`, несколько аргументов — в `<ml:sequence>` |
| `v[i]`, `M[i, j]` | `<ml:apply><ml:indexer/>v i</ml:apply>`, `…<ml:indexer/>M<ml:sequence>i j</ml:sequence>` |
| `col(M, j)` | `<ml:apply><ml:matcol/>M j</ml:apply>` (M⟨j⟩). **Оператора строки в MC13 нет** (`ml:matrow` есть в схеме, но регион молча удаляется) |
| `[1, 2; 3, 4]` | `<ml:matrix rows="2" cols="2">` — элементы **по столбцам**: 1 3 2 4 |
| `i := 0..10`, `t := 0, 0.1..1` | `<ml:range>0 10</ml:range>`, `<ml:range><ml:sequence>0 0.1</ml:sequence>1</ml:range>` |
| `sqrt(x)`, `nthroot(3, x)` | `ml:sqrt`, `ml:nthRoot` (сначала степень, потом подкоренное) |
| `abs(x)`, `det(M)` | `ml:absval` (\|x\|), `ml:determinant` |
| `transpose(M)`, `M^-1` | `ml:transpose`, `pow` c `-1` |
| `vsum(v)`, `vectorize(e)`, `conj(z)`, `cross(a, b)` | `ml:vectorSum` (Σv), `ml:vectorize` (стрелка), `ml:conjugate`, `ml:crossProduct` |
| `sum(e, k, 1, 10)` / `sum(e, i)` | `<ml:apply><ml:summation/><ml:lambda><ml:boundVars>k</ml:boundVars>e</ml:lambda><ml:bounds>1 10</ml:bounds></ml:apply>`; без `bounds` — сумма по ранжированной переменной |
| `prod(…)` | то же с `ml:product` |
| `int(e, x, a, b)` / `int(e, x)` | `ml:integral` + `lambda` + `bounds` (неопределённый — без `bounds`, для символьного →) |
| `diff(e, x)` / `diff(e, x, 2)` | `ml:derivative` + `lambda` [+ `<ml:degree>2</ml:degree>`] |
| `lim(e, x, a)` / `lim(e, x, a, "left")` | `<ml:apply><ml:limit direction="left"/><ml:lambda>…</ml:lambda>a</ml:apply>` |
| `y'(t)`, `y''(t)` | штрих — часть имени: `<ml:id>y''</ml:id>` (для Odesolve) |
| `if(c, a, b)` | обычная функция `if` |

Постфиксные/инфиксные формы (`-10 °F`, `2 ∠ 30`) — `<ml:apply fixity="postfix">`; xmcd.py печатает их
как вызов `°F(-10)` (вычисляется так же).

## Программы (панель Programming)

```
f(n) := prog { s <- 0; for k in 0..n { if k > 5 { break }; s <- s + k }; s }
```
| Линейно | XML |
|---|---|
| `prog { … }` | `<ml:program>stmt*</ml:program>` — значение последнего оператора = результат |
| `x <- e` | `<ml:localDefine>x e</ml:localDefine>` |
| `if c { … }` / `if c: stmt` | `<ml:ifThen>c body</ml:ifThen>` (тело из нескольких операторов → вложенный `ml:program`) |
| `else { … }` | `<ml:otherwise>body</ml:otherwise>` |
| `for k in 0..n { … }` | `<ml:for><ml:id>k</ml:id><ml:range>…</ml:range>body</ml:for>` (можно `for k in v` — по вектору) |
| `while c { … }` | `<ml:while>c body</ml:while>` |
| `return e`, `break`, `continue` | `ml:return`, `ml:break`, `ml:continue` |
| `try { … } catch { … }` | `<ml:tryCatch>a b</ml:tryCatch>` (on error) |

## Результаты (что сохраняет Mathcad)

```xml
<ml:eval><ml:id>F</ml:id>
  <result xmlns="http://schemas.mathsoft.com/math20">
    <unitedValue><ml:real>5</ml:real>
      <unitMonomial xmlns="http://schemas.mathsoft.com/units10">
        <unitReference unit="kilogram"/><unitReference unit="meter" power-numerator="-1"/>
        <unitReference unit="second" power-numerator="-2"/></unitMonomial></unitedValue></result></ml:eval>
```
- без `unitOverride` значение в **базовых SI** (kg, m, s, A, K, mol, cd); с `unitOverride` — в указанных
  единицах, имена полные (`kilonewton`, `megapascal`).
- матрица результата — `<ml:matrix>` (по столбцам); строка — `<ml:str>`; комплекс — `<ml:complex>`.
- символьный результат — `<ml:symResult>` внутри `ml:symEval`, в виде выражения.
- Ошибки в файл **не пишутся** — их видно только через COM (`MathInterface.HasError/ErrorMsg`), `mc.ps1` их выводит.

## Встроенные имена, которые легко случайно переопределить (проверено на Mathcad 13)

Переопределение `имя := 1` разрешено, но Mathcad ставит `warning=…` и рисует зелёную волнистую черту,
а единица/функция теряется ниже по листу.

| Предупреждение | Имена |
|---|---|
| `WarnRedefinedBIUnit` (единица) | `c g l m s A C F G H J K L N R S T V W Pa Hz ft in yd mi lb lbf min hr day kg cm mm km kN MPa GPa psi ksi rad deg sr mol cd Ω` (+ все из `units.md`) |
| `WarnRedefinedBIConstant` | `e π` |
| `WarnRedefinedBIFunction` | `ε δ` (символ Леви-Чивиты, дельта Кронекера) и все встроенные функции |
| свободны | `a b d f h i j k n o p q r t u v w x y z B D E I M O P Q U X Y Z α β γ θ λ μ ν ρ σ τ φ ω` |

`g` — это ускорение свободного падения, грамм — `gm`; `c` — скорость света; `L`/`l` — литр; `R` — градус Ренкина;
`G` — гаусс; `T` — тесла; `S` — сименс; `C` — кулон; `F` — фарад; `A` — ампер; `K` — кельвин.
Рекомендация: литеральные индексы `F.1`, `L.p`, `A.s`, `R.u`, `E.m`, `M.max` — они никогда не конфликтуют.
