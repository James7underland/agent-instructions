/*
 * ring_buffer.c - see ring_buffer.h for the concurrency contract.
 */
#include "ring_buffer.h"
#include "port.h"

int rb_init(ring_buffer_t *rb, volatile uint8_t *storage, uint32_t capacity)
{
    if (rb == NULL || storage == NULL || capacity < 2u || (capacity & (capacity - 1u)) != 0u) {
        return -1;
    }
    rb->buf     = storage;
    rb->mask    = capacity - 1u;
    rb->head    = 0u;
    rb->tail    = 0u;
    rb->dropped = 0u;
    return 0;
}

int PORT_ISR_ATTR rb_put(ring_buffer_t *rb, uint8_t byte)
{
    uint32_t head = rb->head;
    if ((uint32_t)(head - rb->tail) > rb->mask) {    /* used == capacity: full */
        rb->dropped++;
        return 0;
    }
    rb->buf[head & rb->mask] = byte;
    PORT_COMPILER_BARRIER();                          /* data first, then publish */
    rb->head = head + 1u;
    return 1;
}

int rb_get(ring_buffer_t *rb, uint8_t *out)
{
    uint32_t tail = rb->tail;
    if (rb->head == tail) {
        return 0;                                     /* empty */
    }
    *out = rb->buf[tail & rb->mask];
    PORT_COMPILER_BARRIER();                          /* read data before freeing the slot */
    rb->tail = tail + 1u;
    return 1;
}

size_t rb_read(ring_buffer_t *rb, uint8_t *dst, size_t max)
{
    size_t n = 0;
    while (n < max && rb_get(rb, &dst[n])) {
        n++;
    }
    return n;
}

uint32_t rb_count(const ring_buffer_t *rb)
{
    return (uint32_t)(rb->head - rb->tail);
}

uint32_t rb_free(const ring_buffer_t *rb)
{
    return rb_capacity(rb) - rb_count(rb);
}

uint32_t rb_capacity(const ring_buffer_t *rb)
{
    return rb->mask + 1u;
}
