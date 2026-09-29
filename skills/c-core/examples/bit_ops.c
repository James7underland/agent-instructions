/*
 * bit_ops.c - see bit_ops.h.
 */
#include "bit_ops.h"

uint32_t bits_field_get(uint32_t x, unsigned pos, unsigned width)
{
    return (x >> pos) & MASK_LOW(width);
}

uint32_t bits_field_set(uint32_t x, unsigned pos, unsigned width, uint32_t value)
{
    uint32_t mask = (uint32_t)(MASK_LOW(width) << pos);
    return (x & ~mask) | ((value << pos) & mask);
}

unsigned bits_popcount32(uint32_t x)
{
    unsigned n = 0;
    while (x != 0u) {
        x &= x - 1u;        /* clears the lowest set bit (K&R exercise 2-9) */
        n++;
    }
    return n;
}

uint8_t bits_reverse8(uint8_t v)
{
    /* Swap neighbours, then pairs, then nibbles. Casts keep results in 8 bits
       because the operands are promoted to int. */
    v = (uint8_t)(((v & 0x55u) << 1) | ((v & 0xAAu) >> 1));
    v = (uint8_t)(((v & 0x33u) << 2) | ((v & 0xCCu) >> 2));
    v = (uint8_t)(((v & 0x0Fu) << 4) | ((v & 0xF0u) >> 4));
    return v;
}

int bits_is_power_of_two(uint32_t x)
{
    return x != 0u && (x & (x - 1u)) == 0u;
}

uint16_t bits_get_be16(const uint8_t *p)
{
    return (uint16_t)(((uint16_t)p[0] << 8) | p[1]);
}

uint32_t bits_get_le32(const uint8_t *p)
{
    return (uint32_t)p[0]
         | ((uint32_t)p[1] << 8)
         | ((uint32_t)p[2] << 16)
         | ((uint32_t)p[3] << 24);
}

void bits_put_be16(uint8_t *p, uint16_t v)
{
    p[0] = (uint8_t)(v >> 8);
    p[1] = (uint8_t)v;
}

void bits_put_le32(uint8_t *p, uint32_t v)
{
    p[0] = (uint8_t)v;
    p[1] = (uint8_t)(v >> 8);
    p[2] = (uint8_t)(v >> 16);
    p[3] = (uint8_t)(v >> 24);
}
