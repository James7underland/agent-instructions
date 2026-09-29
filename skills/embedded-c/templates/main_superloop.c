/**
 * @file    main_superloop.c
 * @brief   Template: event-driven super loop for a bare-metal MCU.
 *
 * ISRs only post events (bits). The loop takes all events atomically, handles
 * them, feeds the watchdog in ONE place and sleeps when there is nothing to do.
 * Replace the hal_* / board_* stubs with the real target functions.
 */
#include <stdbool.h>
#include <stdint.h>

/* ---- target hooks (implement per board) ------------------------------------- */
typedef uint32_t irq_state_t;
static irq_state_t irq_save_disable(void)    { return 0u; }      /* e.g. xt_rsil(15) / PRIMASK */
static void        irq_restore(irq_state_t s) { (void)s; }
static void        cpu_sleep(void)           { }                 /* e.g. __WFI(); nothing on a PC */
static void        watchdog_feed(void)       { }
static void        board_init(void)          { }                 /* clocks, pins, peripherals */

/* ---- events ------------------------------------------------------------------ */
#define EV_TICK_1MS   (1UL << 0)
#define EV_UART_RX    (1UL << 1)
#define EV_BUTTON     (1UL << 2)

static volatile uint32_t s_events;
static volatile uint32_t s_ticks_ms;

void systick_isr(void)                       /* 1 kHz timer interrupt */
{
    s_ticks_ms = s_ticks_ms + 1u;
    s_events |= EV_TICK_1MS;                 /* ISRs do not nest here; otherwise guard it */
}

static uint32_t events_take(void)
{
    irq_state_t st = irq_save_disable();
    uint32_t ev = s_events;
    s_events = 0u;
    irq_restore(st);
    return ev;
}

uint32_t time_now_ms(void) { return s_ticks_ms; }   /* atomic on 32-bit MCUs */

/* ---- application handlers (each returns quickly, never blocks) --------------- */
static void app_init(void)            { }
static void app_on_tick(uint32_t now) { (void)now; }  /* periodic work via (now - last >= period) */
static void app_on_uart(void)         { }
static void app_on_button(void)       { }
static bool app_all_alive(void)       { return true; }  /* every subsystem made progress */

int main(void)
{
    board_init();
    app_init();

    for (;;) {
        uint32_t ev = events_take();

        if (ev & EV_TICK_1MS) { app_on_tick(time_now_ms()); }
        if (ev & EV_UART_RX)  { app_on_uart(); }
        if (ev & EV_BUTTON)   { app_on_button(); }

        if (app_all_alive()) {
            watchdog_feed();                 /* the only place the watchdog is fed */
        }

        /* Sleep only if no event arrived meanwhile (check + sleep with IRQs masked
           on MCUs where a pending IRQ still wakes the core, e.g. Cortex-M WFI). */
        {
            irq_state_t st = irq_save_disable();
            if (s_events == 0u) {
                cpu_sleep();
            }
            irq_restore(st);
        }
    }
}
