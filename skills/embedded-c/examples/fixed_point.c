/*
 * fixed_point.c - see fixed_point.h.
 * No floating point is used at run time (FX_CONST is evaluated by the compiler).
 */
#include "fixed_point.h"
#include <stdio.h>

static fx16_t saturate64(int64_t v)
{
    if (v > (int64_t)FX_MAX) { return FX_MAX; }
    if (v < (int64_t)FX_MIN) { return FX_MIN; }
    return (fx16_t)v;
}

fx16_t fx_from_int(int32_t i)
{
    return saturate64((int64_t)i * FX_ONE);    /* multiply instead of shifting a signed value */
}

int32_t fx_to_int_floor(fx16_t a)
{
    /* Floor division by 2^16 without right-shifting a negative number. */
    int64_t q = (int64_t)a / FX_ONE;
    if ((int64_t)a % FX_ONE < 0) {
        q -= 1;
    }
    return (int32_t)q;
}

int32_t fx_to_int_round(fx16_t a)
{
    int64_t half = FX_ONE / 2;
    int64_t v = (a >= 0) ? ((int64_t)a + half) : ((int64_t)a - half);
    return (int32_t)(v / FX_ONE);               /* '/' truncates toward zero (C99) */
}

fx16_t fx_add(fx16_t a, fx16_t b)
{
    return saturate64((int64_t)a + b);
}

fx16_t fx_sub(fx16_t a, fx16_t b)
{
    return saturate64((int64_t)a - b);
}

fx16_t fx_mul(fx16_t a, fx16_t b)
{
    int64_t p = (int64_t)a * b;                 /* Q32.32 */
    int64_t half = (int64_t)1 << (FX_FRAC_BITS - 1);
    p = (p >= 0) ? (p + half) : (p - half);     /* round half away from zero */
    return saturate64(p / FX_ONE);
}

int fx_div(fx16_t a, fx16_t b, fx16_t *out)
{
    int64_t n;
    if (b == 0) {
        return -1;
    }
    n = (int64_t)a * FX_ONE;                    /* Q32.32 numerator, no signed shift */
    *out = saturate64(n / b);
    return 0;
}

int fx_format(fx16_t a, unsigned decimals, char *buf, size_t size)
{
    static const uint32_t pow10[5] = { 1u, 10u, 100u, 1000u, 10000u };
    int64_t  v = a;
    int      neg = (v < 0);
    uint64_t mag = (uint64_t)(neg ? -v : v);    /* safe: |INT32_MIN| fits in 64 bits */
    uint64_t ipart;
    uint64_t frac;

    if (decimals > 4u) {
        decimals = 4u;
    }
    /* Scale the fraction to 'decimals' digits with rounding. */
    frac = ((mag & (uint64_t)(FX_ONE - 1)) * pow10[decimals] + (uint64_t)(FX_ONE / 2)) >> FX_FRAC_BITS;
    ipart = mag >> FX_FRAC_BITS;
    if (frac >= pow10[decimals]) {              /* rounding carried into the integer part */
        frac -= pow10[decimals];
        ipart += 1u;
    }
    if (decimals == 0u) {
        return snprintf(buf, size, "%s%lu", neg ? "-" : "", (unsigned long)ipart);
    }
    return snprintf(buf, size, "%s%lu.%0*lu", neg ? "-" : "", (unsigned long)ipart,
                    (int)decimals, (unsigned long)frac);
}
