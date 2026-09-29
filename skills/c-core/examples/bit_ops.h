/*
 * bit_ops.h - portable bit manipulation helpers (C99).
 *
 * All masks are unsigned long (at least 32 bits), so BIT_U32(31) is defined
 * behaviour even where int is 16 bits. Shift counts must be 0..31.
 */
#ifndef BIT_OPS_H
#define BIT_OPS_H

#include <stdint.h>

#define BIT_U32(n)               (1UL << (n))
#define BIT_SET(x, n)        ((x) |=  BIT_U32(n))
#define BIT_CLEAR(x, n)      ((x) &= ~BIT_U32(n))
#define BIT_TOGGLE(x, n)     ((x) ^=  BIT_U32(n))
#define BIT_READ(x, n)       (((x) >> (n)) & 1UL)
#define MASK_LOW(n)          (((n) >= 32u) ? 0xFFFFFFFFUL : (BIT_U32(n) - 1UL))

uint32_t bits_field_get(uint32_t x, unsigned pos, unsigned width);
uint32_t bits_field_set(uint32_t x, unsigned pos, unsigned width, uint32_t value);
unsigned bits_popcount32(uint32_t x);            /* number of 1 bits */
uint8_t  bits_reverse8(uint8_t v);               /* 0b00000001 -> 0b10000000 */
int      bits_is_power_of_two(uint32_t x);       /* 0 is not a power of two */

/* Endianness-independent packing (the byte order is defined by the protocol, not the CPU). */
uint16_t bits_get_be16(const uint8_t *p);
uint32_t bits_get_le32(const uint8_t *p);
void     bits_put_be16(uint8_t *p, uint16_t v);
void     bits_put_le32(uint8_t *p, uint32_t v);

#endif /* BIT_OPS_H */
