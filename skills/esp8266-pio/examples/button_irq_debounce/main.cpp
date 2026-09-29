/*
 * button_irq_debounce - button on an interrupt + software debounce.
 *
 * Hardware (D1 mini): push button between D2 (GPIO4) and GND, internal pull-up.
 *                     Built-in LED D4 (GPIO2) toggles on every accepted press.
 * Design:
 *  - the ISR only records "an edge happened" (volatile flag + counter) - short, in IRAM;
 *  - loop() then confirms the press by sampling the pin every 5 ms until it has been
 *    stable LOW for DEBOUNCE_SAMPLES samples (bounces and glitches are rejected);
 *  - the raw edge count is kept to show how much the contact bounces.
 * The interrupt is useful for waking up / catching short presses; the decision is
 * always made by the debounce logic in loop().
 */
#include <Arduino.h>

static const uint8_t  PIN_BUTTON       = D2;          /* GPIO4 */
static const uint8_t  PIN_LED          = LED_BUILTIN;  /* GPIO2, active LOW */
static const uint32_t SAMPLE_MS        = 5u;
static const uint8_t  DEBOUNCE_SAMPLES = 4u;           /* 4 x 5 ms = 20 ms stable */

/* ---- shared with the ISR --------------------------------------------------------- */
static volatile bool     s_edge_seen;     /* set by ISR, cleared by loop */
static volatile uint32_t s_edge_count;    /* written only by the ISR */

static void IRAM_ATTR on_button_edge(void)
{
    s_edge_count = s_edge_count + 1u;
    s_edge_seen = true;
}

/* ---- debounce state machine (loop context only) ---------------------------------- */
typedef enum { BTN_IDLE, BTN_CONFIRMING, BTN_HELD } btn_state_t;

static btn_state_t s_state = BTN_IDLE;
static uint32_t    s_last_sample;
static uint8_t     s_stable_count;
static uint32_t    s_presses;
static bool        s_led_on;

static void on_press(void)
{
    s_presses++;
    s_led_on = !s_led_on;
    digitalWrite(PIN_LED, s_led_on ? LOW : HIGH);
    Serial.printf("press #%lu (raw edges so far: %lu)\n",
                  (unsigned long)s_presses, (unsigned long)s_edge_count);
}

static void button_poll(uint32_t now)
{
    switch (s_state) {
    case BTN_IDLE:
        if (s_edge_seen) {
            s_edge_seen = false;            /* bool store is atomic; a new edge just sets it again */
            s_stable_count = 0;
            s_last_sample = now;
            s_state = BTN_CONFIRMING;
        }
        break;

    case BTN_CONFIRMING:
        if (now - s_last_sample >= SAMPLE_MS) {
            s_last_sample = now;
            if (digitalRead(PIN_BUTTON) == LOW) {
                if (++s_stable_count >= DEBOUNCE_SAMPLES) {
                    on_press();
                    s_stable_count = 0;     /* now counts stable HIGH samples of the release */
                    s_state = BTN_HELD;
                }
            } else {
                s_state = BTN_IDLE;         /* it was a glitch or bounce */
            }
        }
        break;

    case BTN_HELD:                          /* wait for a stable release before re-arming */
        if (now - s_last_sample >= SAMPLE_MS) {
            s_last_sample = now;
            s_stable_count = (digitalRead(PIN_BUTTON) == HIGH) ? (uint8_t)(s_stable_count + 1u) : 0u;
            if (s_stable_count >= DEBOUNCE_SAMPLES) {
                s_edge_seen = false;        /* discard edges produced by the release bounce */
                s_state = BTN_IDLE;
            }
        }
        break;

    default:
        s_state = BTN_IDLE;
        break;
    }
}

void setup()
{
    Serial.begin(115200);
    Serial.println(F("\nbutton_irq_debounce: press the button on D2"));
    digitalWrite(PIN_LED, HIGH);                 /* LED off: level first, then output */
    pinMode(PIN_LED, OUTPUT);
    pinMode(PIN_BUTTON, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(PIN_BUTTON), on_button_edge, FALLING);
}

void loop()
{
    button_poll(millis());
}
