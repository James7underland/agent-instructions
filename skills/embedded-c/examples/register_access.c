/*
 * register_access.c - see register_access.h.
 */
#include "register_access.h"
#include "port.h"

uint32_t reg_field_get(uint32_t value, unsigned pos, unsigned width)
{
    return (value >> pos) & RA_MASK(width);
}

uint32_t reg_field_set(uint32_t value, unsigned pos, unsigned width, uint32_t field)
{
    uint32_t mask = RA_MASK(width) << pos;
    return (value & ~mask) | ((field << pos) & mask);
}

void gpio_set_mode(gpio_port_t *port, unsigned pin, pin_mode_t mode)
{
    /* Two bits per pin -> read-modify-write of a shared register: protect it. */
    port_irq_state_t st = PORT_IRQ_SAVE_DISABLE();
    port->MODE = reg_field_set(port->MODE, pin * 2u, 2u, (uint32_t)mode);
    PORT_IRQ_RESTORE(st);
}

void gpio_write(gpio_port_t *port, unsigned pin, int level)
{
    /* Atomic: a single store, other pins are not touched, no critical section needed. */
    if (level) {
        port->SET = RA_BIT(pin);
    } else {
        port->CLR = RA_BIT(pin);
    }
}

int gpio_read(const gpio_port_t *port, unsigned pin)
{
    return (int)RA_READ_BIT(port->IN, pin);
}

void gpio_irq_clear(gpio_port_t *port, unsigned pin)
{
    port->IRQ_FLAG = RA_BIT(pin);   /* NOT |= : that would clear every pending flag */
}

void gpio_sim_latch(gpio_port_t *port)
{
    port->OUT = (port->OUT | port->SET) & ~port->CLR;
    port->SET = 0u;
    port->CLR = 0u;
}
