/*
 * register_access.h - safe access to memory-mapped peripheral registers.
 *
 * Rules shown here:
 *  - registers are volatile and described by a struct overlay with fixed-width types;
 *  - masks are unsigned 32-bit (1UL << n), never (1 << 31) on a 32-bit int;
 *  - multi-bit fields are changed with read-modify-write inside a critical section
 *    unless the hardware offers atomic SET/CLR registers;
 *  - write-1-to-clear (W1C) status flags are cleared with '=' not '|='.
 *
 * On a PC the "peripheral" is an ordinary struct in RAM, so the code can be tested.
 */
#ifndef REGISTER_ACCESS_H
#define REGISTER_ACCESS_H

#include <stdint.h>

#define RA_BIT(n)                 (1UL << (n))
#define RA_MASK(width)            (((width) >= 32u) ? 0xFFFFFFFFUL : (RA_BIT(width) - 1UL))

/* Single-bit helpers for a volatile register lvalue. Each one is a read-modify-write! */
#define RA_SET_BIT(reg, n)        ((reg) |=  RA_BIT(n))
#define RA_CLEAR_BIT(reg, n)      ((reg) &= ~RA_BIT(n))
#define RA_TOGGLE_BIT(reg, n)     ((reg) ^=  RA_BIT(n))
#define RA_READ_BIT(reg, n)       ((uint32_t)(((reg) >> (n)) & 1UL))

/* Example peripheral: a GPIO port with atomic set/clear registers and a W1C status. */
typedef struct {
    volatile uint32_t MODE;      /* 2 bits per pin: 0 = input, 1 = output, 2 = alt, 3 = analog */
    volatile uint32_t IN;        /* input levels (read-only on real hardware) */
    volatile uint32_t OUT;       /* output latch */
    volatile uint32_t SET;       /* write 1 -> OUT bit becomes 1 (atomic) */
    volatile uint32_t CLR;       /* write 1 -> OUT bit becomes 0 (atomic) */
    volatile uint32_t IRQ_FLAG;  /* write 1 to clear (W1C) */
} gpio_port_t;

/* On a real MCU:  #define GPIOA ((gpio_port_t *)0x40010800UL)  */

typedef enum { PIN_INPUT = 0u, PIN_OUTPUT = 1u, PIN_ALT = 2u, PIN_ANALOG = 3u } pin_mode_t;

uint32_t reg_field_get(uint32_t value, unsigned pos, unsigned width);
uint32_t reg_field_set(uint32_t value, unsigned pos, unsigned width, uint32_t field);

void     gpio_set_mode(gpio_port_t *port, unsigned pin, pin_mode_t mode);  /* RMW in critical section */
void     gpio_write(gpio_port_t *port, unsigned pin, int level);            /* atomic via SET/CLR */
int      gpio_read(const gpio_port_t *port, unsigned pin);
void     gpio_irq_clear(gpio_port_t *port, unsigned pin);                   /* W1C */

/* PC simulation only: applies SET/CLR writes to OUT like the hardware would. */
void     gpio_sim_latch(gpio_port_t *port);

#endif /* REGISTER_ACCESS_H */
