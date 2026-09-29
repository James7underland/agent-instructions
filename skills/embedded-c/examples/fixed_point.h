/*
 * fixed_point.h - Q16.16 signed fixed-point arithmetic in int32_t.
 *
 * value = raw / 65536. Range about -32768.0 .. +32767.99998, step 1.53e-5.
 * All operations saturate instead of overflowing (signed overflow is UB in C).
 * Multiplication and division use a 64-bit intermediate.
 * Constants are converted at compile time with FX_CONST(1.25).
 */
#ifndef FIXED_POINT_H
#define FIXED_POINT_H

#include <stddef.h>
#include <stdint.h>

typedef int32_t fx16_t;                 /* Q16.16 */

#define FX_FRAC_BITS 16
#define FX_ONE       ((fx16_t)1 << FX_FRAC_BITS)
#define FX_MAX       INT32_MAX
#define FX_MIN       INT32_MIN

/* Compile-time conversion of a literal; rounds half away from zero. */
#define FX_CONST(x)  ((fx16_t)((x) * 65536.0 + (((x) >= 0) ? 0.5 : -0.5)))

fx16_t  fx_from_int(int32_t i);            /* saturates outside +-32767 */
int32_t fx_to_int_round(fx16_t a);         /* round to nearest, halves away from zero */
int32_t fx_to_int_floor(fx16_t a);         /* toward -infinity */
fx16_t  fx_add(fx16_t a, fx16_t b);        /* saturating */
fx16_t  fx_sub(fx16_t a, fx16_t b);        /* saturating */
fx16_t  fx_mul(fx16_t a, fx16_t b);        /* rounded, saturating */
int     fx_div(fx16_t a, fx16_t b, fx16_t *out);   /* returns -1 on division by zero */

/* Formats with 'decimals' (0..4) digits after the point, e.g. "-12.3456". Returns chars written. */
int     fx_format(fx16_t a, unsigned decimals, char *buf, size_t size);

#endif /* FIXED_POINT_H */
