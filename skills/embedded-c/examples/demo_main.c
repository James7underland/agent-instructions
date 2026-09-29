/*
 * demo_main.c - runs every example module on a PC and simulates the interrupts.
 *
 * Build (from this folder):
 *   gcc -std=c99 -Wall -Wextra -Werror -pedantic -O2 -o demo \
 *       demo_main.c ring_buffer.c debounce.c state_machine.c fixed_point.c \
 *       register_access.c isr_events.c
 *
 * The "ISRs" are ordinary functions called at chosen moments, which is exactly
 * how the logic is unit tested before it goes on the target.
 */
#include <stdio.h>
#include <string.h>

#include "debounce.h"
#include "fixed_point.h"
#include "isr_events.h"
#include "register_access.h"
#include "ring_buffer.h"
#include "state_machine.h"

static int s_failures;
#define CHECK(cond) do { if (!(cond)) { s_failures++; \
    printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond); } } while (0)

static void demo_ring_buffer(void)
{
    static volatile uint8_t storage[8];
    ring_buffer_t rb;
    uint8_t out[8];
    const char *msg = "hello\n";
    size_t i, n;

    CHECK(rb_init(&rb, storage, 8u) == 0);
    CHECK(rb_init(&rb, storage, 6u) != 0);          /* not a power of two */
    CHECK(rb_init(&rb, storage, 8u) == 0);

    for (i = 0; msg[i] != '\0'; i++) {              /* "UART RX ISR" */
        (void)rb_put(&rb, (uint8_t)msg[i]);
    }
    n = rb_read(&rb, out, sizeof out);              /* main loop */
    CHECK(n == 6u && memcmp(out, "hello\n", 6u) == 0);
    printf("ring buffer: read %u bytes, dropped %lu\n", (unsigned)n, (unsigned long)rb.dropped);
}

static void demo_debounce(void)
{
    /* Button to GND with pull-up: active level 0. 10 ms tick, 3 samples. */
    static const uint8_t raw[] = { 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1 };
    debounce_t d;
    size_t i;
    int presses = 0, releases = 0;

    debounce_init(&d, 0u, 3u, 3u, 1u);
    for (i = 0; i < sizeof raw; i++) {
        debounce_event_t e = debounce_update(&d, raw[i]);
        if (e == DEBOUNCE_PRESSED)  { presses++; }
        if (e == DEBOUNCE_RELEASED) { releases++; }
    }
    CHECK(presses == 1 && releases == 1);
    printf("debounce: %d press, %d release from a bouncy signal\n", presses, releases);
}

static void demo_state_machine(void)
{
    light_fsm_t a, b;
    const uint32_t t0 = 0xFFFFFA00u;                /* 1536 ms before uint32 rollover: yellow crosses it */
    static const struct { light_event_t ev; uint32_t dt; } script[] = {
        { EV_STOP, 0 }, { EV_GO, 10 }, { EV_GO, 20 }, { EV_STOP, 30 },
        { EV_TICK, 1000 }, { EV_GO, 1500 }, { EV_TICK, 3100 }, { EV_TICK, 3200 },
    };
    size_t i;

    fsm_init(&a, t0);
    fsm_init(&b, t0);
    for (i = 0; i < sizeof script / sizeof script[0]; i++) {
        uint32_t now = t0 + script[i].dt;
        light_state_t sa = fsm_switch_step(&a, script[i].ev, now);
        light_state_t sb = fsm_table_step(&b, script[i].ev, now);
        CHECK(sa == sb);
    }
    CHECK(a.state == ST_RED && a.transitions == 3u);
    printf("state machine: final %s after %lu transitions (switch == table)\n",
           fsm_state_name(a.state), (unsigned long)a.transitions);
}

static void demo_fixed_point(void)
{
    char buf[24];
    fx16_t gain = FX_CONST(1.25);
    fx16_t temp = FX_CONST(-12.5);
    fx16_t r = fx_mul(temp, gain);                  /* -15.625 */
    fx16_t q;

    CHECK(r == FX_CONST(-15.625));
    CHECK(fx_div(FX_CONST(1.0), FX_CONST(3.0), &q) == 0);
    CHECK(fx_div(FX_ONE, 0, &q) != 0);
    CHECK(fx_add(FX_MAX, FX_ONE) == FX_MAX);         /* saturates, no UB */
    (void)fx_format(r, 3u, buf, sizeof buf);
    CHECK(strcmp(buf, "-15.625") == 0);
    printf("fixed point: -12.5 * 1.25 = %s\n", buf);
}

static void demo_registers(void)
{
    gpio_port_t port;
    memset(&port, 0, sizeof port);                  /* fake peripheral in RAM */

    gpio_set_mode(&port, 3u, PIN_OUTPUT);
    gpio_write(&port, 3u, 1);
    gpio_sim_latch(&port);
    CHECK(reg_field_get(port.MODE, 6u, 2u) == PIN_OUTPUT);
    CHECK(RA_READ_BIT(port.OUT, 3u) == 1u);
    port.IRQ_FLAG = RA_BIT(1) | RA_BIT(3);
    gpio_irq_clear(&port, 3u);
    CHECK(port.IRQ_FLAG == RA_BIT(3));             /* on real HW W1C would leave bit 1 pending */
    printf("registers: MODE=0x%08lX OUT=0x%08lX\n", (unsigned long)port.MODE, (unsigned long)port.OUT);
}

static void demo_isr_events(void)
{
    uint32_t ev;
    button_edge_isr();                              /* two presses before the loop runs */
    button_edge_isr();
    events_post_from_isr(EVT_TICK);

    ev = events_take();
    CHECK((ev & EVT_BUTTON) && (ev & EVT_TICK));
    CHECK(events_take() == 0u);                     /* taken and cleared */
    CHECK(button_new_presses() == 2u);              /* nothing lost */
    CHECK(button_new_presses() == 0u);
    printf("isr events: 0x%lX, presses counted correctly\n", (unsigned long)ev);
}

int main(void)
{
    demo_ring_buffer();
    demo_debounce();
    demo_state_machine();
    demo_fixed_point();
    demo_registers();
    demo_isr_events();
    printf("%s (%d failures)\n", s_failures ? "DEMO FAILED" : "DEMO OK", s_failures);
    return s_failures ? 1 : 0;
}
