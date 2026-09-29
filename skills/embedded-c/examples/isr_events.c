/*
 * isr_events.c - see isr_events.h.
 *
 * Why each piece is needed:
 *  - volatile: the main loop must re-read the variables on every access,
 *    otherwise the optimizer may cache them and never see the ISR's writes;
 *  - critical section in events_take(): "read then clear" is two accesses; an ISR
 *    firing between them would have its event erased;
 *  - the counter is written only by the ISR (single writer) and is 32-bit, which
 *    is a single atomic store on a 32-bit MCU (on an 8-bit MCU read it inside a
 *    critical section).
 */
#include "isr_events.h"
#include "port.h"

static volatile uint32_t s_events;          /* bits set by ISRs, cleared by main */
static volatile uint32_t s_press_count;     /* written only by button_edge_isr() */
static uint32_t          s_press_seen;      /* main-loop private copy */

void PORT_ISR_ATTR events_post_from_isr(uint32_t mask)
{
    /* RMW inside an ISR is safe only if ISRs cannot preempt each other.
       With nested interrupts protect it with a critical section as well. */
    port_irq_state_t st = PORT_IRQ_SAVE_DISABLE();
    s_events |= mask;
    PORT_IRQ_RESTORE(st);
}

void PORT_ISR_ATTR button_edge_isr(void)
{
    s_press_count = s_press_count + 1u;      /* single writer */
    events_post_from_isr(EVT_BUTTON);
}

uint32_t events_take(void)
{
    uint32_t ev;
    port_irq_state_t st = PORT_IRQ_SAVE_DISABLE();
    ev = s_events;
    s_events = 0u;
    PORT_IRQ_RESTORE(st);
    return ev;
}

uint32_t button_new_presses(void)
{
    uint32_t now = s_press_count;            /* one atomic 32-bit load */
    uint32_t n = now - s_press_seen;         /* unsigned: correct across wrap-around */
    s_press_seen = now;
    return n;
}
