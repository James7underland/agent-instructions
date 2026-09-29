/*
 * blink_nonblocking - two LEDs blinking at unrelated rates without delay().
 *
 * Hardware (D1 mini): built-in LED on D4 (GPIO2, active LOW);
 *                     external LED + 330 ohm resistor from D5 (GPIO14) to GND.
 * Shows: millis()-based scheduling, rollover-safe math, drift-free periods,
 * a blinker "object" (struct + functions) reused for both LEDs.
 */
#include <Arduino.h>

typedef struct {
    uint8_t  pin;
    bool     active_low;
    uint32_t on_ms;
    uint32_t off_ms;
    uint32_t next_ms;    /* deadline of the next toggle */
    bool     on;
} blinker_t;

static void blinker_write(const blinker_t *b)
{
    bool level = b->active_low ? !b->on : b->on;
    digitalWrite(b->pin, level ? HIGH : LOW);
}

static void blinker_init(blinker_t *b, uint32_t now)
{
    b->on = false;
    b->next_ms = now + b->off_ms;
    blinker_write(b);                /* level first, then output: no glitch */
    pinMode(b->pin, OUTPUT);
}

static void blinker_poll(blinker_t *b, uint32_t now)
{
    /* (int32_t)(now - deadline) >= 0 is true once the deadline is reached, even across the
       2^32 rollover (valid while periods are < 2^31 ms). */
    if ((int32_t)(now - b->next_ms) >= 0) {
        b->on = !b->on;
        b->next_ms += b->on ? b->on_ms : b->off_ms;   /* schedule from the deadline: no drift */
        blinker_write(b);
    }
}

static blinker_t s_builtin = { LED_BUILTIN, true,  100u,  900u, 0u, false };  /* short flash */
static blinker_t s_outer   = { D5,          false, 250u,  250u, 0u, false };  /* 2 Hz */

void setup()
{
    uint32_t now = millis();
    blinker_init(&s_builtin, now);
    blinker_init(&s_outer, now);
}

void loop()
{
    uint32_t now = millis();
    blinker_poll(&s_builtin, now);
    blinker_poll(&s_outer, now);
    /* other non-blocking work goes here */
}
