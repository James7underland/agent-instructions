/*
 * ring_buffer.h - single-producer / single-consumer byte FIFO.
 *
 * Typical use: a UART RX interrupt calls rb_put(), the main loop calls rb_get().
 * No locking is needed as long as exactly one context writes (producer) and
 * exactly one context reads (consumer):
 *   - head is written only by the producer, tail only by the consumer;
 *   - indices are free-running uint32_t, the used length is (head - tail);
 *   - capacity must be a power of two, the slot is (index & mask).
 * uint32_t loads/stores must be atomic on the target (true on 32-bit MCUs,
 * NOT on 8-bit AVR - use uint8_t indices there).
 */
#ifndef RING_BUFFER_H
#define RING_BUFFER_H

#include <stddef.h>
#include <stdint.h>

typedef struct {
    volatile uint8_t *buf;       /* storage provided by the caller */
    uint32_t          mask;      /* capacity - 1, capacity is a power of two */
    volatile uint32_t head;      /* next write position (producer only) */
    volatile uint32_t tail;      /* next read position (consumer only) */
    volatile uint32_t dropped;   /* bytes rejected because the buffer was full (producer only) */
} ring_buffer_t;

/* Returns 0 on success, -1 if capacity is not a power of two (>= 2) or buf is NULL. */
int      rb_init(ring_buffer_t *rb, volatile uint8_t *storage, uint32_t capacity);

/* Producer side (may be called from an ISR). Returns 1 if stored, 0 if full. */
int      rb_put(ring_buffer_t *rb, uint8_t byte);

/* Consumer side. Returns 1 and writes *out if a byte was available, 0 if empty. */
int      rb_get(ring_buffer_t *rb, uint8_t *out);

/* Copies up to max bytes out; returns the number of bytes copied. Consumer side. */
size_t   rb_read(ring_buffer_t *rb, uint8_t *dst, size_t max);

uint32_t rb_count(const ring_buffer_t *rb);   /* bytes stored (snapshot) */
uint32_t rb_free(const ring_buffer_t *rb);    /* free slots (snapshot) */
uint32_t rb_capacity(const ring_buffer_t *rb);

#endif /* RING_BUFFER_H */
