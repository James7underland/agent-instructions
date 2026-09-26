# Встроенные функции Mathcad 13 (375)

Сгенерировано из `C:\Program Files (x86)\Mathsoft\Mathcad 13\doc\funcdoc\mathcad_EN.xml`.
Полное описание функции: `doc\Help_EN\Help\<help_topic>` (HTML) — имя темы в том же XML.

Имена регистрозависимы. Необязательные аргументы — в квадратных скобках. Функции решателей
(`Find`, `Minerr`, `Minimize`, `Maximize`, `Odesolve`, `polyroots`, `genfit`, `Pdesolve`, `numol`) в XML
записываются отдельными элементами `ml:Find` и т.п. — `xmcd.py` делает это сам.

## Категории
[Bessel](#bessel) (36), [Complex Numbers](#complex-numbers) (5), [Curve Fitting and Smoothing](#curve-fitting-and-smoothing) (18), [Debugging](#debugging) (2), [Differential Equation Solving](#differential-equation-solving) (18), [Expression Type](#expression-type) (3), [File Access](#file-access) (27), [Finance](#finance) (18), [Fourier Transform](#fourier-transform) (8), [Graphing](#graphing) (12), [Hyperbolic](#hyperbolic) (12), [Interpolation and Prediction](#interpolation-and-prediction) (7), [Log and Exponential](#log-and-exponential) (5), [Lookup](#lookup) (4), [Number Theory/Combinatorics](#number-theorycombinatorics) (5), [Piecewise Continuous](#piecewise-continuous) (6), [Probability Density](#probability-density) (17), [Probability Distribution](#probability-distribution) (35), [Random Numbers](#random-numbers) (19), [Solving](#solving) (7), [Sorting](#sorting) (4), [Special](#special) (16), [Statistics](#statistics) (15), [String](#string) (11), [Trigonometric](#trigonometric) (15), [Truncation and Round-Off](#truncation-and-round-off) (8), [Vector and Matrix](#vector-and-matrix) (40), [Wavelet Transform](#wavelet-transform) (2)

## Bessel

| Функция | Описание |
|---|---|
| `Ai(z)` | Returns the value of the Airy function of the first kind. |
| `Ai.sc(x)` | Returns the value of the Airy function of the first kind, scaled by the factor exp(/Re(2/3*z^3/2)/). |
| `bei(m, x)` | Returns the value of the imaginary Bessel Kelvin function of order m. |
| `ber(m, x)` | Returns the value of the real Bessel Kelvin function of order m. |
| `Bi(x)` | Returns the value of the Airy function of the second kind. |
| `Bi.sc(x)` | Returns the value of the Airy function of the second kind, scaled by the factor exp(/Re(2/3*z^3/2)/). |
| `H1(m, z)` | Returns the Hankel function of the first kind (Bessel function of the third kind). |
| `H1.sc(m, z)` | Returns the Hankel function of the first kind (Bessel function of the third kind), scaled by the factor exp((3 - 2*m)*z*i). |
| `H2(m, z)` | Returns the Hankel function of the second kind (Bessel function of the third kind). |
| `H2.sc(m, z)` | Returns the Hankel function of the second kind (Bessel function of the third kind), scaled by the factor exp(-(3 - 2*m)*z*i). |
| `I0(z)` | Returns the zeroth order modified Bessel function of the first kind. |
| `I0.sc(z)` | Returns the zeroth order modified Bessel function of the first kind, scaled by the factor exp(-/Re(z)/). |
| `I1(z)` | Returns the first order modified Bessel function of the first kind. |
| `I1.sc(z)` | Returns the first order modified Bessel function of the first kind, scaled by the factor exp(-/Re(z)/). |
| `In(m, z)` | Returns the mth order modified Bessel function of the first kind. |
| `In.sc(m, z)` | Returns the mth order modified Bessel function of the first kind, scaled by the factor exp(-/Re(z)/). |
| `J0(z)` | Returns the zeroth order Bessel function of the first kind. |
| `J0.sc(z)` | Returns the zeroth order Bessel function of the first kind, scaled by exp(-/Im(z)/). |
| `J1(z)` | Returns the first order Bessel function of the first kind. |
| `J1.sc(z)` | Returns the first order Bessel function of the first kind, scaled by exp(-/Im(z)/). |
| `Jn(m, z)` | Returns the mth order Bessel function of the first kind. |
| `Jn.sc(m, z)` | Returns the mth order Bessel function of the first kind, scaled by exp(-/Im(z)/). |
| `js(m, z)` | Returns the value of the spherical Bessel function of the first kind, of order m. |
| `K0(z)` | Returns the zeroth order modified Bessel function of the second kind. |
| `K0.sc(z)` | Returns the zeroth order modified Bessel function of the second kind, scaled by the factor exp(z). |
| `K1(z)` | Returns the first order modified Bessel function of the second kind. |
| `K1.sc(z)` | Returns the first order modified Bessel function of the second kind, scaled by the factor exp(z). |
| `Kn(m, z)` | Returns the mth order modified Bessel function of the second kind. |
| `Kn.sc(m, z)` | Returns the mth order modified Bessel function of the second kind, scaled by the factor exp(z). |
| `Y0(z)` | Returns the zeroth order Bessel function of the second kind. |
| `Y0.sc(z)` | Returns the zeroth order Bessel function of the second kind, scaled by the factor exp(-/Im(z)/). |
| `Y1(z)` | Returns the first order Bessel function of the second kind. |
| `Y1.sc(z)` | Returns the first order Bessel function of the second kind, scaled by the factor exp(-/Im(z)/). |
| `Yn(m, z)` | Returns the mth order Bessel function of the second kind. |
| `Yn.sc(m, z)` | Returns the mth order Bessel function of the second kind, scaled by the factor exp(-/Im(z)/). |
| `ys(m, z)` | Returns the value of the spherical Bessel function of the second kind, of order m. |

## Complex Numbers

| Функция | Описание |
|---|---|
| `arg(z)` | Returns the principal argument of the complex number z, between -pi and pi, including pi. |
| `csgn(z)` | Returns the complex sign of z, given by 0 if z = 0, 1 if the real or imaginary part of z is > 0, and -1 otherwise. |
| `Im(z)` | Returns the imaginary part of complex number, vector, or matrix, z. |
| `Re(z)` | Returns the real part of complex number z. |
| `signum(z)` | Returns 1 if z = 0 and z//z/ otherwise. |

## Curve Fitting and Smoothing

| Функция | Описание |
|---|---|
| `expfit(vx, vy, [vg])` | Returns a vector containing three coefficients for an exponential curve of the form a*e^(b*x)+c that best approximates the data in vectors vx and vy. The optional vector vg contains guess values for the three coefficients. |
| `genfit(vx, vy, vg, F)` | Returns a vector of parameters that make the first function in the vector F best fit the data in the vectors vx and vy. The remaining elements in F are partial derivatives of the fitting function with respect to its n parameters, and vg is a vector of guess values. Right-click on this function to choose a solver. |
| `intercept(vx, vy)` | Returns the intercept of line that best fits data in vx and vy. |
| `ksmooth(vx, vy, b)` | Returns a vector of local weighted averages of vy using a Gaussian kernel with bandwidth b. |
| `lgsfit(vx, vy, vg)` | Returns a vector containing the 3 coefficients for a logistic curve of the form a/(1+b*e^(-c*x)) that best approximates the data in vectors vx and vy, using guess values in vg. |
| `line(vx, vy)` | Returns a vector containing the coefficients for a line of the form a + bx that best approximates the data in vectors vx and vy. |
| `linfit(vx, vy, F)` | Returns a vector containing the coefficients used to create a linear combination of the functions in vector F which best approximates the data in vx and vy. |
| `lnfit(vx, vy)` | Returns a vector containing the 2 coefficients for a logarithmic curve of the form a*ln(x) + b that best approximates the data in vx and vy. |
| `loess(vx, vy, span)` | Returns a vector used by the interp function to find a set of second order polynomials that best fit a neighborhood of data values in vectors or matrices vx and vy. The size of the neighborhood is controlled by span. |
| `logfit(vx, vy, vg)` | Returns a vector containing the three coefficients for a logarithmic curve of the form a*ln(x+b)+c that best approximates the data in vectors vx and vy. Vector vg contains guess values for the three coefficients. |
| `medfit(vx, vy)` | Returns a vector containing the coefficients for a line of the form a + bx that best approximates the data in vectors vx and vy using median-median regression. |
| `medsmooth(vy, n)` | Returns a smoothed vector by replacing each value in vy with the median of the n points centered on that value. |
| `pwrfit(vx, vy, vg)` | Returns a vector containing the coefficients for a power curve of the form a*x^b + c that best approximates the data in vectors vx and vy. Vector vg contains guess values for the three coefficients. |
| `regress(vx, vy, n)` | Returns a vector of coefficients for the multivariate nth degree least-squares polynomial fit of the data in vx and vy. This vector becomes the first argument of the interp function. |
| `sinfit(vx, vy, vg)` | Returns a vector containing the coefficients for a sine curve of the form a*sin(x +b) + c that best approximates the data in vectors vx and vy. Vector vg contains guess values for the three coefficients. |
| `slope(vx, vy)` | Returns the slope of line that best fits data in vx and vy. |
| `stderr(vx, vy)` | Returns the standard error associated with a linear regression for the points described by the vectors vx and vy. Measures the spread of data points about the regression line. |
| `supsmooth(vx, vy)` | Returns a vector created by the piecewise use of a symmetric nearest neighbor linear least-squares fitting on each element in vy, in which the number of nearest neighbors is adaptively chosen. |

## Debugging

| Функция | Описание |
|---|---|
| `pause(S, x, y, z, ...)` | Returns a string containing the value of the arguments x, y, z, ... with print order and surrounding text specified by S. Prints values in the Trace Window and pauses execution when debug mode is on. S is optional if only one value is printed. |
| `trace(S, x, y, z, ...)` | Returns a string containing the value of the arguments x, y, z, ... with print order and surrounding text specified by S. Prints values in the Trace Window when debug mode is on. S is optional if only one value is printed. |

## Differential Equation Solving

| Функция | Описание |
|---|---|
| `bulstoer(y, x1, x2, acc, D, kmax, s)` | Returns the solution values at the x2 endpoint of the integration interval for the smooth differential equation specified by the derivatives in D using a variable step Bulirsch-Stoer method. Use Bulstoer to return the solution over the whole range. |
| `Bulstoer(y, x1, x2, npoints, D)` | Returns a matrix of solution values for the smooth differential equation specified by the derivatives in D using a Bulirsch-Stoer method. |
| `bvalfit(v1, v2, x1, x2, xf, D, load1, load2, score)` | Returns a vector of initial conditions for the boundary value problem specified by the derivatives in D where the solution is known at the intermediate point xf. |
| `multigrid(M, ncycle)` | Returns a square matrix of solution values for Poisson's partial differential equation, controlled by ncycle, in the case of zero boundaries. Otherwise, use the relax function. |
| `numol(x_endpts, xpts, t_endpts, tpts, num_pde, num_pae, pde_func, pinit, bc_func)` | Returns an xpts by tpts matrix containing the solutions to the one-dimensional PDEs in pde_func. Each column represents a solution over 1-D space at a single solution time. For a system of equations, the solution for each function is appended horizontally, so the matrix always has xpts rows, and tpts * (num_pde + num_pae) columns. |
| `Odesolve([vf], x, b, [step])` | Returns a function or vector of functions of x representing the solution to a system of ordinary differential equations in a Solve Block over the range 0 to b; vf is omitted when solving a single ODE. |
| `Pdesolve(u, x, xrange, t, trange, [xpts], [tpts])` | Returns a vector u of functions of x and t representing the solution to a system of partial differential equations in a Solve Block over the ranges specified in xrange and trange. |
| `radau(y, x1, x2, acc, D, kmax, s)` | Returns the solution values at the x2 endpoint of the integration interval for the stiff differential equation specified by the derivatives in D using the RADAU5 method. Use Radau to return the solution over the whole range. |
| `Radau(y, x1, x2, npoints, D)` | Returns a matrix of solution values for the stiff differential equation specified by the derivatives in D, and initial conditions y on the interval [x1,x2], using a RADAU5 method. Parameter npoints controls the number of rows in the matrix output. |
| `relax(A, B, C, D, E, F, U, rjac)` | Returns a square matrix of solution values for Poisson's equation for source function F. Matrices A, B, C, D, and E specify coefficients for linearly approximating the Laplacian operator. Matrix U gives boundary values along the edges. If these are zero, use multigrid. |
| `rkadapt(y, x1, x2, acc, D, kmax, s)` | Returns the solution values at the x2 endpoint of the integration interval for the differential equation specified by the derivatives in D using an adaptive step Runge-Kutta method. Use Rkadapt to return the solution over the whole range. |
| `Rkadapt(y, x1, x2, npoints, D)` | Returns a matrix of solution values for the differential equation specified by the derivatives in D and having initial conditions y on the interval [x1,x2] using an adaptive step Runge-Kutta method. Parameter npoints controls the number of rows in the matrix output. |
| `rkfixed(y, x1, x2, npoints, D)` | Returns a matrix of solution values for the differential equation specified by the derivatives in D and having initial conditions y on the interval [x1,x2] using a fixed step Runge-Kutta method. Parameter npoints controls the number of rows in the matrix output. |
| `sbval(v, x1, x2, D, load, score)` | Returns a set of initial conditions for the boundary value problem specified by the derivatives in D and guess values in v on the interval [x1,x2]. Parameter load contains both known initial conditions and guess values from v, and score measures solution discrepancy at x2. |
| `stiffb(y, x1, x2, acc, D, J, kmax, s)` | Returns the solution values at the x2 endpoint of the integration interval for the stiff differential equation specified by the derivatives in D using a Bulirsch-Stoer method. Use Stiffb to return the solution over the whole range. |
| `Stiffb(y, x1, x2, npoints, D, J)` | Returns a matrix of solution values for the stiff differential equation specified by the derivatives in D, the Jacobian function J, and initial conditions y on the interval [x1,x2] using a Bulirsch-Stoer method. Parameter npoints controls the number of rows in the matrix output. |
| `stiffr(y, x1, x2, acc, D, J, kmax, s)` | Returns the solution values at the x2 endpoint of the integration interval for the stiff differential equation specified by the derivatives in D using the variable step Rosenbrock method. Use Stiffr to return the solution over the whole range. |
| `Stiffr(y, x1, x2, npoints, D, J)` | Returns a matrix of solution values for the stiff differential equation specified by the derivatives in D, the Jacobian function J, and initial conditions y on the interval [x1,x2] using a Rosenbrock method. Parameter npoints controls the number of rows in the matrix output. |

## Expression Type

| Функция | Описание |
|---|---|
| `IsNaN(x)` | Returns 1 if x is NaN. Returns 0 otherwise. |
| `SIUnitsOf(x)` | Returns the units of x scaled to the default SI unit, regardless of your chosen unit system. If x has no units, returns 1. |
| `UnitsOf(x)` | Returns the units of x scaled to the default SI unit. If x has no units, returns 1. |

## File Access

| Функция | Описание |
|---|---|
| `APPENDPRN(file, [M])` | Writes the contents of an array to the end of a delimited ASCII file. |
| `GETWAVINFO(file)` | Returns a vector containing, in order, the number of channels, the sample rate, the bit resolution, and the average bytes per second for a WAV file. |
| `READ_BLUE(file)` | Returns a matrix representing the RGB blue component of the BMP, GIF, JPG, or TGA color image in file. |
| `READ_GREEN(file)` | Returns a matrix representing the RGB green component of the BMP, GIF, JPG, or TGA color image in file. |
| `READ_HLS(file)` | Returns a packed matrix of hue, lightness, and saturation components based on the Ostwald color model for the BMP, GIF, JPG, or TGA color image in file. The returned matrix contains the H, L, and S matrices packed side by side. |
| `READ_HLS_HUE(file)` | Returns a matrix representing the HLS hues based on the Ostwald color model for the BMP, GIF, JPG, or TGA color image in file. |
| `READ_HLS_LIGHT(file)` | Returns a matrix representing the HLS lightness components based on the Ostwald color model for the BMP, GIF, JPG, or TGA color image in file. |
| `READ_HLS_SAT(file)` | Returns a matrix representing the HLS saturation components based on the Ostwald color model for the BMP, GIF, JPG, or TGA color image in file. |
| `READ_HSV(file)` | Returns a packed matrix of hue, saturation, and value components based on Smith's HSV color model for the BMP, GIF, JPG, or TGA color image in file. The returned matrix contains the H, S, and V matrices packed side by side. |
| `READ_HSV_HUE(file)` | Returns a matrix representing the HSV hues based on Smith's HSV color model for the BMP, GIF, JPG, or TGA color image in file. |
| `READ_HSV_SAT(file)` | Returns a matrix representing the HSV saturation components based on Smith's HSV color model for the BMP, GIF, JPG, or TGA color image in file. |
| `READ_HSV_VALUE(file)` | Returns a matrix representing the HSV value components based on Smith's HSV color model for the BMP, GIF, JPG, or TGA color image in file. |
| `READ_IMAGE(file)` | Returns a matrix containing a grayscale representation of the BMP, GIF, JPG, or TGA image in file. |
| `READ_RED(file)` | Returns a matrix representing the RGB red component of the BMP, GIF, JPG, or TGA image in file. |
| `READBIN(file, type, [[endian], [cols], [skip], [maxrows]])` | Returns a matrix from a single-format binary data file of specified type. |
| `READBMP(file)` | Returns an array of integers between 0 (black) and 255 (white) representing the grayscale BMP image in file. |
| `READFILE(file, type, [[colwidths], [rows], [cols], [emptyfill]])` | Returns a matrix from the contents of a file of specified type (delimited, fixed-width, or Excel). |
| `READPRN(file)` | Returns a matrix formed from a structured data file on your file system. |
| `READRGB(file)` | Returns a packed matrix of red, green, and blue components for the BMP color image in file. The returned matrix contains the R, G, and B matrices packed side by side. |
| `READWAV(file)` | Creates a matrix containing signal amplitudes in file. Each column represents a separate channel of data. Each row corresponds to a moment in time. |
| `WRITE_HLS(file)` | Writes a packed matrix consisting of the hue, lightness, and saturation components of an image to a 16 million color Windows BMP file on your file system. |
| `WRITE_HSV(file)` | Writes a packed matrix consisting of the hue, saturation, and value components of an image to a 16 million color Windows BMP file on your file system. |
| `WRITEBIN(file, type, endian)` | Writes an array of scalars to the binary data file named file. |
| `WRITEBMP(file)` | Writes an array into a grayscale BMP file on your file system. |
| `WRITEPRN(file)` | Writes an array into a file on your file system. |
| `WRITERGB(file)` | Writes a packed matrix consisting of the red, green, and blue components image to a 16 million color Windows BMP file on your file system. |
| `WRITEWAV(file, s, b)` | Writes a WAV signal file out of a matrix. |

## Finance

| Функция | Описание |
|---|---|
| `cnper(rate, pv, fv)` | Returns the number of compounding periods for an investment to yield a specified future value. |
| `crate(nper, pv, fv)` | Returns the fixed interest rate per period required for an investment at present value to yield a specified future value over a number of compounding periods. |
| `cumint(rate, nper, pv, start, end, [type])` | Returns the cumulative interest paid on a loan between a starting period and an ending period given a fixed interest rate, the total number of compounding periods, and the present value of the loan. |
| `cumprn(rate, nper, pv, start, end, [type])` | Returns the cumulative principal paid on a loan between a starting period and an ending period given a fixed interest rate, the total number of compounding periods, and the present value of the loan. |
| `eff(rate, npery)` | Returns the effective annual interest rate (APR), given the nominal interest rate and the number of compounding periods per year. |
| `fv(rate, nper, pmt, [[pv], [type]])` | Returns the future value of an investment or loan given a periodic, constant payment and a fixed interest rate. |
| `fvadj(prin, v)` | Returns the future value of an initial principal after applying the series of compound interest rates in vector v. |
| `fvc(rate, v)` | Returns the future value of a vector of cash flows, v, earning a specified interest rate. |
| `ipmt(rate, per, nper, pv, [[fv], [type]])` | Returns the interest payment of an investment or loan for a given period based on periodic, constant payments over a given number of compounding periods using a fixed interest rate and a specified present value. |
| `irr(v, [guess])` | Returns the internal rate of return for a series of cash flows occurring at regular intervals. |
| `mirr(v, fin_rate, rein_rate)` | Returns the modified internal rate of return for a vector v of cash flows given a finance rate and a reinvestment rate. |
| `nom(APR, npery)` | Returns the nominal interest rate, given the effective annual interest rate (APR) and the number of compounding periods per year. |
| `nper(rate, pmt, pv, [[fv], [type]])` | Returns the number of compounding periods for an investment or loan based on periodic, constant payments using a fixed interest rate and a specified present value. |
| `npv(rate, v)` | Returns the net present value of an investment given a discount rate and a series of cash flows occuring at regular intervals. |
| `pmt(rate, nper, pv, [[fv], [type]])` | Returns the payment for an investment or loan based on periodic, constant payments over a given number of compounding periods using a fixed interest rate and a specified present value. |
| `ppmt(rate, per, nper, pv, [[fv], [type]])` | Returns the payment on the principal of an investment or loan for a given period based on periodic, constant payments over a given number of compounding periods using a fixed interest rate and a specified present value. |
| `pv(rate, nper, pmt, [[fv], [type]])` | Returns the present value of an investment or loan based on periodic, constant payments over a given number of compounding periods using a fixed interest rate and a specified payment. |
| `rate(nper, pmt, pv, [[fv], [type], [guess]])` | Returns the interest rate per period of an investment or loan over a specified number of compounding periods given a periodic, constant payment and a specified present value. |

## Fourier Transform

| Функция | Описание |
|---|---|
| `cfft(A)` | Returns the Discrete Fourier transform of any size vector or matrix of real or complex numbers. Returns an array of the same size as its argument. |
| `CFFT(A)` | Returns the Discrete Fourier transform of any size vector or matrix of real or complex numbers. Returns an array of the same size as its argument. Similar to cfft(A), with a different normalizing factor and sign convention. |
| `fft(v)` | Returns the fast Fourier transform of real data vector v with 2^n elements. Returns a vector of size 2^n-1 + 1. Similar to FFT(v), except uses a different normalizing factor and sign convention. |
| `FFT(v)` | Returns the fast Fourier transform of real data vector v with 2^n elements. Returns a vector of size 2^n-1 + 1. Similar to fft(v), except uses a different normalizing factor and sign convention. |
| `icfft(A)` | Returns the inverse Fourier transform corresponding to cfft. Returns an array of the same size as its argument. |
| `ICFFT(A)` | Returns the inverse Fourier transform corresponding to CFFT. Returns an array of the same size as its argument. |
| `ifft(u)` | Returns the inverse Fourier transform corresponding to fft. Takes a vector of size 1 + 2^n-1, where n is an integer. Returns a real vector of size 2^n. |
| `IFFT(u)` | Returns the inverse Fourier transform corresponding to FFT. Takes a vector of size 1 + 2^n-1, where n is an integer. Returns a real vector of size 2^n. |

## Graphing

| Функция | Описание |
|---|---|
| `cyl2xyz(r, q, f)` | Converts the cylindrical coordinates of a point in 3D space to rectangular coordinates. |
| `LoadColormap(file)` | Returns an array containing the values in the colormap named file. |
| `logpts(minexp, dec, dnpts)` | Returns a vector with dec decades of evenly-spaced points starting at 10 raised to the exponent minexp, with dnpts points per decade. |
| `logspace(min, max, npts)` | Returns a vector of npts logarithmically-spaced points starting at min, ending at max. |
| `pol2xy(r, theta)` | Converts the polar coordinates of a point in 2D space to rectangular coordinates. |
| `Polyhedron(S)` | Generates the uniform polyhedron whose name, number code, or Wythoff symbol is string S. |
| `PolyLookup(n)` | Returns a vector containing the name, the dual name, and the Wythoff symbol for the polyhedron whose number code is n. |
| `SaveColormap(file, M)` | Creates a colormap named file containing the values in the matrix M. Returns the number of rows written to the file. |
| `sph2xyz(r, theta, phi)` | Converts the spherical coordinates of a point in 3D space to rectangular coordinates. |
| `xy2pol(x, y)` | Converts the rectangular coordinates of a point in 2D space to polar coordinates. |
| `xyz2cyl(x, y, z)` | Converts the rectangular coordinates of a point in 3D space to cylindrical coordinates. |
| `xyz2sph(x, y, z)` | Converts the rectangular coordinates of a point in 3D space to spherical coordinates. |

## Hyperbolic

| Функция | Описание |
|---|---|
| `acosh(z)` | Returns the angle (in radians) whose hyperbolic cosine is z. The result is the principal value for complex z. |
| `acoth(z)` | Returns the angle (in radians) whose hyperbolic cotangent is z. The result is the principal value for complex z. |
| `acsch(z)` | Returns the angle (in radians) whose hyperbolic arccosecant is z. The result is the principal value for complex z. |
| `asech(z)` | Returns the angle (in radians) whose hyperbolic secant is z. Result is the principal value for complex z. |
| `asinh(z)` | Returns the angle (in radians) whose hyperbolic sine is z. Principal value for complex z. |
| `atanh(z)` | Returns the angle (in radians) whose hyperbolic tangent is z. Principal value for complex z. |
| `cosh(z)` | Returns the hyperbolic cosine of z. |
| `coth(z)` | Returns the hyperbolic cotangent of z. |
| `csch(z)` | Returns the hyperbolic cosecant of z. |
| `sech(z)` | Returns the hyperbolic secant of z. |
| `sinh(z)` | Returns the hyperbolic sine of z. |
| `tanh(z)` | Returns the hyperbolic tangent of z. |

## Interpolation and Prediction

| Функция | Описание |
|---|---|
| `bspline(vx, vy, u, n)` | Returns a vector of the coefficients of a B-spline of degree n for the data in vx and vy, given the knot values in u. The vector returned becomes the first argument of the interp function. |
| `cspline(vx, vy)` | Returns a vector of cubic spline coefficients with cubic endpoints which fits the independent data in vector or matrix vx and dependent data in vy. This vector becomes the first argument of the interp function. |
| `interp(vs, vx, vy, x)` | Returns an interpolated value at x from the coefficients in vector vs, and the original data in vx and vy. Coefficient vector vs is the output of one of the following: cspline, lspline, pspline, bspline, loess, or regress. |
| `linterp(vx, vy, x)` | Returns a linearly interpolated value at x for data vectors vx and vy of the same size. |
| `lspline(vx, vy)` | Returns a vector of cubic spline coefficients with linear endpoints which fits the independent data in vector or matrix vx and dependent data in vy. This vector becomes the first argument of the interp function. |
| `predict(v, m, n)` | Returns a vector of n predicted values past the last element in v, based on autocorrelation coefficients of m consecutive values in a sliding window. |
| `pspline(vx, vy)` | Returns a vector of cubic spline coefficients with parabolic endpoints that fits the independent data in vector or matrix vx and dependent data in vy. This vector becomes the first argument of the interp function. |

## Log and Exponential

| Функция | Описание |
|---|---|
| `exp(z)` | Returns the number e raised to the power z. |
| `ln(z)` | Returns the natural logarithm (base e) of z. Returns principal value (imaginary part between pi and -pi) for complex z. |
| `ln0(z)` | Returns the natural logarithm (base e) of z but allows z = 0. Returns principal value (imaginary part between pi and -pi) for complex z. |
| `ln\G(z)` | Returns the natural logarithm of Euler's gamma function, evaluated at z. To type G, press G[Ctrl]G. |
| `log(z, [b])` | Returns the base b logarithm of z. If b is omitted, returns the base 10 logarithm. |

## Lookup

| Функция | Описание |
|---|---|
| `hlookup(z, A, r)` | Looks in the first row of a matrix, A, for a given value, z, and returns the value(s) in the same column(s) in the row specified, r. When multiple values are returned, they appear in a vector. |
| `lookup(z, A, B)` | Looks in a vector or matrix, A, for a given value, z, and returns the value(s) in the same position(s) (i.e., with the same row and column numbers) in another matrix, B. When multiple values are returned, they appear in a vector. |
| `match(z, A)` | Looks in a vector or matrix, A, for a given value, z, and returns the index (indices) of its positions in A. |
| `vlookup(z, A, c)` | Looks in the first column of a matrix, A, for a given value, z, and returns the value(s) in the same row(s) in the column specified, c. When multiple values are returned, they appear in a vector. |

## Number Theory/Combinatorics

| Функция | Описание |
|---|---|
| `combin(n, k)` | Returns the number of subsets (combinations) of k elements that can be formed from n elements. |
| `gcd(A, B, C, ...)` | Returns the greatest common divisor: the largest integer that evenly divides all the elements of A, B, C, ... |
| `lcm(A, B, C, ...)` | Returns the least common multiple: the smallest positive integer that is a multiple of all the elements of A, B, C, ... |
| `mod(x, y)` | Returns the remainder on dividing x by y (x modulo y). Result has the same sign as x. |
| `permut(n, k)` | Returns the number of ways of ordering n distinct objects taken k at a time (permutations). |

## Piecewise Continuous

| Функция | Описание |
|---|---|
| `\d(x, y)` | Returns the Kronecker delta function with value 1 if x = y, 0 otherwise. To type Delta, press d+[Ctrl]+G. |
| `\e(i, j, k)` | Returns the completely antisymmetric tensor of rank 3. Result is 0 if any two arguments are the same, 1 for even permutations, -1 for odd permutations.. |
| `\F(x)` | Returns the heaviside step function with value 1 if x is greater than or equal to 0, 0 otherwise. To type Phi, press F+[Ctrl]+G. |
| `if(cond, x, y)` | Returns x if logical condition cond is true (non-zero), y otherwise. |
| `sign(x)` | Returns 0 if x = 0, 1 if x > 0, and -1 otherwise. For complex values, use csgn. |
| `until(icond, x)` | Returns x until icond is negative. |

## Probability Density

| Функция | Описание |
|---|---|
| `dbeta(x, s1, s2)` | Returns the probability density for the beta distribution with shape parameters s1 and s2. |
| `dbinom(k, n, p)` | Returns the probability density for the Binomial distribution. |
| `dcauchy(x, l, s)` | Returns the probability density for the Cauchy distribution with location l and scale s. |
| `dchisq(x, d)` | Returns the probability density for the chi-squared distribution with degrees of freedom d. |
| `dexp(x, r)` | Returns the probability density for the exponential distribution with rate of decay r. |
| `dF(x, d1, d2)` | Returns the probability density for the F distribution with degrees of freedom d1 and d2. |
| `dgamma(x, s)` | Returns the probability density for the gamma distribution with shape parameter s. |
| `dgeom(k, p)` | Returns the probability density for the Geometric distribtuion, with probability of success p. |
| `dhypergeom(m, a, b, n)` | Returns the probability density for the hypergeometric distribution. |
| `dlnorm(x, mu, sigma)` | Returns the probability density for the lognormal distribution with logmean mu and logdeviation sigma. |
| `dlogis(x, l, s)` | Returns the probability density for the logistic distribution with location l and scale s. |
| `dnbinom(k, n, p)` | Returns the probability density for the negative binomial distribution with size n and probability of failure p. |
| `dnorm(x, mu, sigma)` | Returns the probability density for the normal distribution with mean mu and standard deviation sigma. |
| `dpois(k, l)` | Returns the probability density for the Poisson distribution in which mean l. |
| `dt(x, d)` | Returns the probability density for Student's t distribution with degrees of freedom d. |
| `dunif(x, a, b)` | Returns the probability density for the uniform distribution on an interval [a,b]. |
| `dweibull(x, s)` | Returns the probability density for the Weibull distribution with shape parameter s. |

## Probability Distribution

| Функция | Описание |
|---|---|
| `cnorm(x)` | Returns the cumulative probability distribution with mean 0 and variance 1. |
| `pbeta(x, s1, s2)` | Returns the cumulative probability beta distribution with shape parameters s1 and s2. |
| `pbinom(k, n, p)` | Returns the cumulative probability binomial distribution for k successes in n trials. |
| `pcauchy(x, l, s)` | Returns the cumulative probability Cauchy distribution with location l and scale s. |
| `pchisq(x, d)` | Returns the cumulative probability chi-squared distribution with degrees of freedom d. |
| `pexp(x, r)` | Returns the cumulative exponential probability distribution with rate r. |
| `pF(x, d1, d2)` | Returns the cumulative F probability distribution with degrees of freedom d1 and d2. |
| `pgamma(x, s)` | Returns the cumulative gamma probability distribution with shape parameter s. |
| `pgeom(k, p)` | Returns the cumulative geometric probability distribution with probability of success p. |
| `phypergeom(m, a, b, n)` | Returns the cumulative hypergeometric probability distribution. |
| `plnorm(x, mu, sigma)` | Returns the cumulative lognormal probability distribution with logmean mu and logdeviation sigma. |
| `plogis(x, l, s)` | Returns the cumulative logistic probability distribution with location l and scale s. |
| `pnbinom(k, n, p)` | Returns the cumulative negative binomial probability distribution with size n and probability of failure p. |
| `pnorm(x, mu, sigma)` | Returns the cumulative normal probability distribution with mean mu and standard deviation sigma. |
| `ppois(k, l)` | Returns the cumulative Poisson probability distribution in which l > 0. |
| `pt(x, d)` | Returns the cumulative probability Student's t distribution with degrees of freedom d. |
| `punif(x, a, b)` | Returns the cumulative uniform probability distribution on the interval [a,b]. |
| `pweibull(x, s)` | Returns the cumulative Weibull probability distribution with shape parameter s. |
| `qbeta(p, s1, s2)` | Returns the inverse cumulative beta distribution with shape parameters s1 and s2. |
| `qbinom(p, n, q)` | Returns the inverse cumulative binomial distribution with size n and probability of success q. |
| `qcauchy(p, l, s)` | Returns the inverse cumulative Cauchy distribution with location l and scale s. |
| `qchisq(p, d)` | Returns the inverse cumulative chi-squared distribution with degrees of freedom d. |
| `qexp(p, r)` | Returns the inverse cumulative exponential distribution with rate r. |
| `qF(p, d1, d2)` | Returns the inverse cumulative F distribution with degrees of freedom d1 and d2. |
| `qgamma(p, s)` | Returns the inverse cumulative gamma distribution with shape parameter s. |
| `qgeom(p, q)` | Returns the inverse cumulative geometric distribution with probability of success q. |
| `qhypergeom(p, a, b, n)` | Returns the inverse cumulative probability distribution for the hypergeometric distribution. p is a real number between 0 and 1. a, b, and n are integers. |
| `qlnorm(p, mu, sigma)` | Returns the inverse cumulative lognormal distribution with logmean mu and logdeviation sigma. |
| `qlogis(p, l, s)` | Returns the inverse cumulative logistic distribution with location l and scale s. |
| `qnbinom(p, n, q)` | Returns the inverse cumulative negative binomial distribution with size n and probability of failure q. |
| `qnorm(p, mu, sigma)` | Returns the inverse cumulative normal distribution with mean mu and standard deviation sigma. |
| `qpois(p, l)` | Returns the inverse cumulative Poisson distribution with l > 0. |
| `qt(p, d)` | Returns the inverse cumulative Student's t distribution with degrees of freedom d. |
| `qunif(p, a, b)` | Returns the inverse cumulative uniform distribution on the interval [a,b]. |
| `qweibull(p, s)` | Returns the inverse cumulative Weibull distribution with shape parameter s. |

## Random Numbers

| Функция | Описание |
|---|---|
| `rbeta(m, s1, s2)` | Returns a vector of m random numbers having the beta distribution with shape parameters s1 and s2. |
| `rbinom(m, n, p)` | Returns a vector of m random numbers having the binomial distribution with size n and probability of success p. |
| `rcauchy(m, l, s)` | Returns a vector of m random numbers having the Cauchy distribution with location l and scale s. |
| `rchisq(m, d)` | Returns a vector of m random numbers having the chi-squared distribution with degrees of freedom d. |
| `rexp(m, r)` | Returns a vector of m random numbers having the exponential distribution with rate r. |
| `rF(m, d1, d2)` | Returns a vector of m random numbers having the F distribution with degrees of freedom d1 and d2. |
| `rgamma(m, s)` | Returns a vector of m random numbers having the gamma distribution with shape parameter s. |
| `rgeom(m, q)` | Returns a vector of m random numbers having the geometric distribution with probability of success q. |
| `rhypergeom(m, a, b, n)` | Returns a vector of m random numbers having the hypergeometric distribution. |
| `rlnorm(m, mu, sigma)` | Returns a vector of m random numbers having the lognormal distribution with logmean mu and logdeviation sigma. |
| `rlogis(m, l, s)` | Returns a vector of m random numbers having the logistic distribution with location l and scale s. |
| `rnbinom(m, n, p)` | Returns a vector of m random numbers having the negative binomial distribution with size n and probability of failure p. |
| `rnd(x)` | Returns a uniformly distributed random number between 0 and x. |
| `rnorm(m, mu, sigma)` | Returns a vector of m random numbers having the normal distribution with mean mu and standard deviation sigma. |
| `rpois(m, l)` | Returns a vector of m random numbers having the Poisson distribution with l > 0. |
| `rt(m, d)` | Returns a vector of m random numbers having Student's t distribution with d degrees of freedom. |
| `runif(m, a, b)` | Returns a vector of m random numbers having the uniform distribution on interval [a,b]. |
| `rweibull(m, s)` | Returns a vector of m random numbers having the Weibull distribution with shape parameter s. |
| `Seed(x)` | Resets the random number seed to x and returns the previous value. |

## Solving

| Функция | Описание |
|---|---|
| `Find(var1, var2, ...)` | Returns the values of var1, var2, ..., that solve a system of equations in a Solve Block. Returns a scalar if there is only one argument, otherwise returns a vector of answers. |
| `lsolve(M, v)` | Returns the vector x solving the linear system of equations M*x = v. |
| `Maximize(f, var1, var2, ...)` | Returns the values of var1, var2, ..., that satisfy the constraints in a Solve Block, and make the function f take on its greatest value. Returns a scalar if there is only one argument, otherwise returns a vector of answers. |
| `Minerr(var1, var2, ...)` | Returns the values of var1, var2, ..., coming closest to satisfying a system of equations and constraints in a Solve Block. Returns a scalar if only one argument, otherwise returns a vector of answers. If Minerr cannot converge, it returns the results of the last iteration. |
| `Minimize(f, var1, var2, ...)` | Returns the values of var1, var2, ..., that satisfy the constraints in a Solve Block, and make the function f take on its smallest value. Returns a scalar if there is only one variable, otherwise returns a vector of answers. |
| `polyroots(v)` | Returns a vector containing all the roots of the polynomial whose coefficients are in v. Right-click on this function to choose a solver. |
| `root(f(var), var, [a, b])` | Returns the value of var to make the function f equal to zero. If a and b are specified, root finds var on this interval. Otherwise, var must be defined with a guess value before root is called. |

## Sorting

| Функция | Описание |
|---|---|
| `csort(A, n)` | Returns an array formed by rearranging rows of A until column n is in ascending order. |
| `reverse(A)` | Reverses the order of elements in a vector, or of rows in a matrix A. |
| `rsort(A, n)` | Returns an array formed by rearranging columns of A until row n is in ascending order. |
| `sort(v)` | Returns a vector with the values from v sorted in ascending order. |

## Special

| Функция | Описание |
|---|---|
| `\G([a], z)` | Returns either Euler's gamma function of z, or the incomplete gamma function of z with degree a. To type G, press G+[Ctrl]+G. |
| `DMS(x)` | Returns the angle in radians given a vector containing degrees, minutes, and seconds; or returns the vector given the angle when used in the units placeholder. |
| `erf(z)` | Returns the error function. |
| `erfc(x)` | Returns the complementary error function. |
| `fhyper(a, b, c, x)` | Returns the value of the Gauss hypergeometric function at the point x given parameters a, b, c. |
| `FIF(x)` | Returns a length given a string representing feet-inches-fractions; or returns the FIF string given a length when used in the units placeholder. |
| `Her(n, x)` | Returns the value of the Hermite polynomial of degree n at x. |
| `hhmmss(x)` | Returns a time given a string containing hours:minutes:seconds; or returns the string given a time when used in the units placeholder. |
| `ibeta(a, x, y)` | Returns the value of the incomplete beta function of x and y with parameter a. |
| `Jac(n, a, b, x)` | Returns the value of the Jacobi polynomial of degree n at x with parameters a and b. |
| `Lag(n, x)` | Returns the value of the Laguerre polynomial of degree n at x. |
| `Leg(n, x)` | Returns the value of the Legendre polynomial of degree n at x. |
| `mhyper(a, b, x)` | Returns the value of the confluent hypergeometric function, M(a,b,x), at the point x with parameters a and b. |
| `Tcheb(n, x)` | Returns the value of the Chebyshev polynomial of degree n, of the first kind, at x. |
| `time(z)` | Returns the current system time. The value z is an arbitrary Mathcad expression with no impact on the return. |
| `Ucheb(n, x)` | Returns the value of the Chebyshev polynomial of degree n, of the second kind, at x. |

## Statistics

| Функция | Описание |
|---|---|
| `corr(A, B)` | Returns the Pearson's r correlation coefficient of the elements in A and B. |
| `cvar(A, B)` | Returns the covariance of the elements in A and B. |
| `gmean(A, B, C, ...)` | Returns the geometric mean of the elements of A, B, C, ... |
| `hist(intvls, data)` | Returns a vector representing the frequencies with which values in data fall into the intervals represented by intvls. intvls can be a vector of interval endpoints, or an integer number of subintervals of equal length. |
| `histogram(intvls, data)` | Returns a two-column matrix containing the midpoints of the intvls subintervals. The second column is identical to the vector returned by hist. The resulting matrix has intvls rows. |
| `hmean(A, B, C, ...)` | Returns the harmonic mean of the elements of A, B, C, ... |
| `kurt(A, B, C, ...)` | Returns the kurtosis of the elements of A, B, C, ... |
| `mean(A, B, C, ...)` | Returns the arithmetic mean, or average, of the elements of A, B, C, ... |
| `median(A, B, C, ...)` | Returns the median of the elements of A, B, C ... |
| `mode(A, B, C, ...)` | Returns the value in A, B, C, ... that occurs most often. |
| `skew(A, B, C, ...)` | Returns the skewness of the elements of A, B, C, ... |
| `stdev(A, B, C, ...)` | Returns the population standard deviation of the elements of A, B, C, ... |
| `Stdev(A, B, C, ...)` | Returns the sample standard deviation of the elements of A, B, C ... |
| `var(A, B, C, ...)` | Returns the population variance of the elements of A, B, C, ... |
| `Var(A, B, C, ...)` | Returns the sample variance of the elements of A, B, C, ... |

## String

| Функция | Описание |
|---|---|
| `concat(S1, S2, S3, ...)` | Returns the string formed by concatenating strings S1, S2, and so on. |
| `error(S)` | Returns the string S as a Mathcad error tip. |
| `format(S, x, y, z, ...)` | Returns a string containing the value of the arguments x, y, z, ... with print order and surrounding text specified by S. S is optional if only one value is printed. |
| `IsString(x)` | Returns 1 if x is a string. Returns 0 otherwise. |
| `num2str(z)` | Returns the number z to a string. |
| `search(S1, SubS, m)` | Returns the starting position of the substring SubS in S1 beginning from position m. |
| `str2num(S)` | Returns a constant formed by converting string S into a number. |
| `str2vec(S)` | Returns a vector of ASCII codes corresponding to the characters in S. |
| `strlen(S)` | Returns the number of characters in string S. |
| `substr(S, m, n)` | Returns a substring of S beginning at character m and having maximum length n. |
| `vec2str(v)` | Returns a string formed by converting the ASCII codes in v to characters. |

## Trigonometric

| Функция | Описание |
|---|---|
| `acos(z)` | Returns the angle (in radians) whose cosine is z. Principal value for complex z. |
| `acot(z)` | Returns the angle (in radians) whose cotangent is z. The result is between 0 and pi if z is real, and the principal value if z is complex. |
| `acsc(z)` | Returns the angle (in radians) whose cosecant is z. The result is the principal value for complex z. |
| `angle(x, y)` | Returns the angle (in radians) between the x-axis and the point (x, y). x and y must be real. |
| `asec(z)` | Returns the angle (in radians) whose secant is z. The result is the principal value for complex z. |
| `asin(z)` | Returns the angle (in radians) whose sine is z. Principal value for complex z. |
| `atan(z)` | Returns the angle (in radians) whose tangent is z. Principal value for complex z. |
| `atan2(x, y)` | Returns the angle (in radians) from the x-axis to a line containing the origin (0,0) and the point (x,y). Both x and y must be real. |
| `cos(z)` | Returns the cosine of z. |
| `cot(z)` | Returns the cotangent of z. |
| `csc(z)` | Returns the cosecant of z. |
| `sec(z)` | Returns the secant of z. |
| `sin(z)` | Returns the sine of z. |
| `sinc(z)` | Returns the value of sin(z)/z, with correct behavior in the limit as z approaches 0. |
| `tan(z)` | Returns the tangent of z. |

## Truncation and Round-Off

| Функция | Описание |
|---|---|
| `ceil(z)` | Returns the smallest integer greater than or equal to z. |
| `Ceil(z, y)` | Returns the smallest multiple of y greater than or equal to z, typically used for correct unit scaling. |
| `floor(z)` | Returns the greatest integer less than or equal to z. |
| `Floor(z, y)` | Returns the greatest multiple of y less than or equal to z, typically used for correct unit scaling. |
| `round(z, n)` | Rounds z to n places. If n is omitted, z is rounded to the nearest integer. If n < 0, z is rounded to the left of the decimal point. |
| `Round(z, y)` | Rounds z to the closest multiple of y, typically used for correct unit scaling. |
| `trunc(z)` | Returns the integer part of z by removing the fractional part. |
| `Trunc(z, y)` | Returns the value of trunc(z/y)*y, typically used for correct unit scaling. |

## Vector and Matrix

| Функция | Описание |
|---|---|
| `augment(A, B, C, ...)` | Returns an array formed by placing A, B, C, ... left to right |
| `cholesky(M)` | Returns the lower triangular matrix L such that L times L transpose is M. L is the cholesky square root of the input matrix. |
| `cols(A)` | Returns the number of columns in A. |
| `cond1(M)` | Returns the condition number of the matrix M based on the L1 norm. |
| `cond2(M)` | Returns the condition number of the matrix M based on the L2 norm. |
| `conde(M)` | Returns the condition number of the matrix M based on the Euclidean norm. |
| `condi(M)` | Returns the condition number of the matrix M based on the infinity norm. |
| `correl(vx, vy)` | Returns the correlation of vectors vx and vy. Result is a vector for which each element contains the summed vector product of vx and a shifted version of vy. |
| `correl2d(M, K)` | Returns the 2D correlation of matrix M with kernel K. The resulting matrix contains the summed element-wise product of K overlapped with a subset of M. |
| `CreateMesh(function(s), [s0, s1, t0, t1], [sgrid, tgrid], [fmap])` | Returns a nested array of three matrices representing the x-, y-, and z-coordinates of a parametric surface defined by the function(s) of two variables in the first argument(s). |
| `CreateSpace(function(s), [t0, t1], [tgrid], [fmap])` | Returns a nested array of three vectors representing the x-, y-, and z-coordinates of a space curve defined by the function(s) of one variable in the first argument. |
| `diag(v)` | Returns a matrix containing on its diagonal the elements of v. |
| `eigenvals(M)` | Returns a vector of eigenvalues for the square matrix M. |
| `eigenvec(M, z)` | Returns the normalized eigenvector associated with eigenvalue z of the square matrix M. The eigenvector is normalized to unit length. |
| `eigenvecs(M)` | Returns a matrix containing the normalized eigenvectors corresponding to the eigenvalues of the square matrix M. The nth column of the matrix returned is an eigenvector corresponding to the nth eigenvalue returned by eigenvals. Optional last argument "L" specifies the left eigenvalue. |
| `geninv(A)` | Returns the generalized (pseudo) inverse of the input matrix A, giving the least-squares solution to a system of equations.. |
| `genvals(M, N)` | Returns a vector of eigenvalues which satisfy the generalized eigenvalue problem. |
| `genvecs(M, N)` | Returns a matrix of normalized eigenvectors corresponding to the eigenvalues returned by genvals. Optional last argument "L" specifies the left eigenvalue. |
| `identity(n)` | Returns an n x n identity matrix (a matrix of 0's with 1's along the diagonal). |
| `IsArray(x)` | Returns 1 if x is a matrix or vector. Returns 0 otherwise. |
| `IsScalar(x)` | Returns 1 if x is a real or complex scalar. Returns 0 otherwise. |
| `last(v)` | Returns the scalar index of the last element in vector v. |
| `length(v)` | Returns the integer number of elements in vector v. |
| `lu(M)` | Returns a matrix containing three augmented square matrices P, L, and U, all having the same size as M; these satisfy the equation P M = L U. |
| `matrix(m, n, f)` | Returns a m x n matrix in which the ijth element is given by f(i,j). |
| `max(A, B, C, ...)` | Returns the largest value from A, B, C, ... If any value is complex, returns max(Re(A, B, C, ...)) + i*max(Im(A, B, C, ...)). |
| `min(A, B, C, ...)` | Returns the smallest value in A, B, C, ... If any value is complex, returns min(Re(A, B, C, ...)) + i*min(Im(A, B, C, ...)). |
| `norm1(M)` | Returns the L1 norm of the matrix M. |
| `norm2(M)` | Returns the L2 norm of the matrix M. |
| `norme(M)` | Returns the Euclidean norm of the matrix M. |
| `normi(M)` | Returns the infinity norm of the matrix M. |
| `qr(A)` | Returns a matrix whose first n columns contain the square, orthonormal matrix, Q, and whose remaining columns contain the upper triangular matrix, R, forming the QR decomposition of the input matrix Q*R = A. |
| `rank(A)` | Returns the rank of matrix A, the number of linearly independent columns. |
| `rows(A)` | Returns the number of rows in A. |
| `rref(A)` | Returns a matrix representing the row-reduced echelon form of A. |
| `stack(A, B, C, ...)` | Returns an array formed by placing A, B, C, ... top to bottom. A, B, C, ... are arrays having the same number of columns, or they are scalars and column vectors. |
| `submatrix(A, ir, jr, ic, jc)` | Returns the submatrix of array A consisting of elements in rows ir through jr and columns ic through jc of A. |
| `svd2(A)` | Returns a vector of 3 nested arrays. The first array contains the vector of singular values. The following two arrays are the matrices U and V. |
| `svds(A)` | Returns a vector containing the singular values of A. |
| `tr(M)` | Returns the trace of square matrix M: sum of diagonal elements. |

## Wavelet Transform

| Функция | Описание |
|---|---|
| `iwave(v)` | Returns the inverse one-dimensional discrete wavelet transform of v computed using the Daubechies 4-coefficient wavelet filter in the wave function. |
| `wave(v)` | Returns the one-dimensional discrete wavelet transform of the data in v using the Daubechies 4-coefficient wavelet filter. |
