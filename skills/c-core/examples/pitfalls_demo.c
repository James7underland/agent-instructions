/*
 * pitfalls_demo.c - the classic C traps from K&R and how to write them correctly.
 * Every "wrong" form is shown in a comment; the code uses the correct form and
 * checks the result with assert, so the file compiles cleanly with
 *   gcc -std=c99 -Wall -Wextra -Werror -pedantic
 *
 * Build and run (with the other c-core examples):
 *   gcc -std=c99 -Wall -Wextra -Werror -pedantic -O2 -o pitfalls \
 *       pitfalls_demo.c bit_ops.c safe_string.c
 */
#include <assert.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "bit_ops.h"
#include "safe_string.h"

#define ARRAY_LEN(a) (sizeof(a) / sizeof((a)[0]))

/* Integer promotion: uint16_t * uint16_t is done in (signed) int on 32-bit targets. */
static uint32_t square_u16(uint16_t x)
{
    /* WRONG: return x * x;   -> int overflow (UB) for x > 46340 on 32-bit int */
    return (uint32_t)x * x;
}

/* Signed/unsigned comparison. */
static int index_is_valid(int idx, size_t len)
{
    /* WRONG: return idx < len;   -> -1 becomes SIZE_MAX, comparison is false/true wrongly */
    return idx >= 0 && (size_t)idx < len;
}

/* Precedence: bitwise & is lower than ==. */
static int flag_clear(uint32_t reg, uint32_t mask)
{
    /* WRONG: return reg & mask == 0;   -> reg & (mask == 0) */
    return (reg & mask) == 0u;
}

/* Binary search: overflow-free midpoint, correct bounds (the PDF copy of K&R has high = mid + 1). */
static int binsearch(int x, const int *v, int n)
{
    int low = 0, high = n - 1;
    while (low <= high) {
        int mid = low + (high - low) / 2;   /* not (low + high) / 2 */
        if (x < v[mid]) {
            high = mid - 1;
        } else if (x > v[mid]) {
            low = mid + 1;
        } else {
            return mid;
        }
    }
    return -1;
}

/* Rollover-safe elapsed time. */
static int timeout_expired(uint32_t now, uint32_t start, uint32_t period)
{
    /* WRONG: return now >= start + period;   -> breaks when start + period wraps */
    return (uint32_t)(now - start) >= period;
}

/* getchar() returns int so that EOF differs from every char. */
static size_t count_chars(FILE *f)
{
    size_t n = 0;
    int c;                                  /* WRONG: char c; */
    while ((c = getc(f)) != EOF) {          /* parentheses around the assignment are required */
        n++;
    }
    return n;
}

int main(void)
{
    static const int sorted[] = { 1, 3, 5, 7, 9, 11 };
    char name[8];
    uint8_t frame[4];
    uint16_t u16 = 0;
    int32_t i32 = 0;
    uint8_t narrow = 0xFE;

    assert(square_u16(0xFFFFu) == 0xFFFE0001UL);
    assert(!index_is_valid(-1, 10u) && index_is_valid(9, 10u) && !index_is_valid(10, 10u));
    assert(flag_clear(0x10u, 0x01u) && !flag_clear(0x11u, 0x01u));
    assert(binsearch(7, sorted, (int)ARRAY_LEN(sorted)) == 3);
    assert(binsearch(4, sorted, (int)ARRAY_LEN(sorted)) == -1);
    assert(timeout_expired(0x00000010u, 0xFFFFFFF0u, 0x20u));     /* across the wrap */
    assert(!timeout_expired(0x00000005u, 0xFFFFFFF0u, 0x20u));

    /* ~ on a narrow type is computed in int: cast back before comparing. */
    assert((uint8_t)~narrow == 0x01u);      /* WRONG: ~narrow == 0x01 */

    /* Shifts: unsigned, wide enough literal. */
    assert(BIT_U32(31) == 0x80000000UL);        /* WRONG: 1 << 31 is UB with 32-bit int */
    assert(bits_field_set(0u, 4u, 4u, 0xFu) == 0xF0u);
    assert(bits_reverse8(0x01u) == 0x80u && bits_popcount32(0xF0F0u) == 8u);

    /* Byte order is explicit, never *(uint32_t *)buf (alignment + strict aliasing). */
    bits_put_le32(frame, 0x12345678UL);
    assert(frame[0] == 0x78u && bits_get_le32(frame) == 0x12345678UL);

    /* Strings: bounded copy and checked parsing instead of strcpy/atoi. */
    assert(str_copy(name, sizeof name, "embedded-c") == 10u && strcmp(name, "embedde") == 0);
    assert(parse_u16("65535", &u16) == 0 && u16 == 65535u);
    assert(parse_u16("-1", &u16) != 0 && parse_u16("12x", &u16) != 0);
    assert(parse_i32("-2147483648", INT32_MIN, INT32_MAX, &i32) == 0 && i32 == INT32_MIN);

    /* Integer division truncates toward zero in C99. */
    assert(-7 / 2 == -3 && -7 % 2 == -1);

    printf("pitfalls demo OK, stdin chars: %u\n", (unsigned)count_chars(stdin));
    return 0;
}
