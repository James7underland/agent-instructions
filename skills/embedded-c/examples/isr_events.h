/*
 * isr_events.h - passing events and counts from interrupts to the main loop.
 *
 * Two patterns:
 *  1) event bit mask: ISRs set bits, the main loop takes (reads and clears) all
 *     bits atomically inside a short critical section;
 *  2) single-writer counter: the ISR only increments, the main loop only reads
 *     and remembers the last value it has processed -> no read-and-clear race,
 *     and no press is lost even if several happen between two loop passes.
 */
#ifndef ISR_EVENTS_H
#define ISR_EVENTS_H

#include <stdint.h>

#define EVT_TICK      (1UL << 0)
#define EVT_BUTTON    (1UL << 1)
#define EVT_RX        (1UL << 2)

/* Called from ISRs (ESP8266: they are placed in IRAM through PORT_ISR_ATTR). */
void     events_post_from_isr(uint32_t mask);
void     button_edge_isr(void);

/* Called from the main loop. */
uint32_t events_take(void);                 /* returns and clears all pending bits */
uint32_t button_new_presses(void);          /* presses since the previous call */

#endif /* ISR_EVENTS_H */
