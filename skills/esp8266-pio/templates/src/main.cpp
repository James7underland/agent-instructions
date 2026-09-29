/*
 * main.cpp - non-blocking skeleton for Wemos D1 mini (ESP8266, Arduino core).
 *
 * Rules this skeleton follows:
 *  - loop() never blocks: no delay(), every job is "if (now - last >= PERIOD)";
 *  - time math is unsigned 32-bit and rollover-safe;
 *  - ISRs (if any) are IRAM_ATTR, only set volatile flags; work is done in loop();
 *  - fixed-size buffers, no String, no malloc after setup();
 *  - the version and the reset reason are printed at start-up.
 * Add modules as src/<module>.cpp + include/<module>.h and call their poll() below.
 */
#include <Arduino.h>

#ifndef FW_VERSION
#define FW_VERSION "0.0.0-dev"
#endif

/* ---- pins (see esp8266-pio/references/pinout-d1mini.md) ---------------------- */
static const uint8_t PIN_LED    = LED_BUILTIN;   /* D4 / GPIO2, lit when LOW */
static const uint8_t PIN_BUTTON = D2;            /* GPIO4, button to GND, INPUT_PULLUP */

/* ---- timing ------------------------------------------------------------------ */
static const uint32_t HEARTBEAT_MS    = 500u;
static const uint32_t BUTTON_POLL_MS  = 10u;
static const uint8_t  DEBOUNCE_COUNT  = 3u;      /* 3 x 10 ms stable = press accepted */
static const uint32_t STATUS_MS       = 10000u;

/* ---- LED heartbeat ------------------------------------------------------------ */
static void led_write(bool on) { digitalWrite(PIN_LED, on ? LOW : HIGH); }  /* inverted LED */

static void heartbeat_poll(uint32_t now)
{
    static uint32_t last;
    static bool on;
    if (now - last >= HEARTBEAT_MS) {
        last += HEARTBEAT_MS;                    /* drift-free */
        on = !on;
        led_write(on);
    }
}

/* ---- button with debounce (polled, no interrupt needed) ----------------------- */
static void on_button_pressed(void)
{
    Serial.println(F("button pressed"));
}

static void button_poll(uint32_t now)
{
    static uint32_t last;
    static uint8_t stable = HIGH;
    static uint8_t count;
    if (now - last < BUTTON_POLL_MS) {
        return;
    }
    last = now;
    uint8_t raw = (uint8_t)digitalRead(PIN_BUTTON);
    if (raw == stable) {
        count = 0;
        return;
    }
    if (++count >= DEBOUNCE_COUNT) {
        stable = raw;
        count = 0;
        if (stable == LOW) {
            on_button_pressed();
        }
    }
}

/* ---- serial line input (bounded, non-blocking) -------------------------------- */
static void handle_line(char *line)
{
    if (strcmp(line, "ver") == 0) {
        Serial.println(F(FW_VERSION));
    } else if (line[0] != '\0') {
        Serial.print(F("ERR unknown command: "));
        Serial.println(line);
    }
}

static void serial_poll(void)
{
    static char buf[64];
    static size_t len;
    static bool overflow;
    while (Serial.available() > 0) {
        int c = Serial.read();
        if (c == '\r') {
            continue;
        }
        if (c == '\n') {
            if (overflow) {
                Serial.println(F("ERR line too long"));
            } else {
                buf[len] = '\0';
                handle_line(buf);
            }
            len = 0;
            overflow = false;
        } else if (len < sizeof buf - 1u) {
            buf[len++] = (char)c;
        } else {
            overflow = true;                     /* keep reading until '\n', then report */
        }
    }
}

/* ---- periodic status ---------------------------------------------------------- */
static void status_poll(uint32_t now)
{
    static uint32_t last;
    if (now - last >= STATUS_MS) {
        last = now;
        Serial.printf("uptime %lu s, free heap %u\n",
                      (unsigned long)(now / 1000u), (unsigned)ESP.getFreeHeap());
    }
}

void setup()
{
    Serial.begin(115200);
    Serial.println();
    Serial.printf("fw %s, core %s, reset: %s\n",
                  FW_VERSION, ESP.getCoreVersion().c_str(), ESP.getResetReason().c_str());

    led_write(false);                /* level first, then output: no LED flash at boot */
    pinMode(PIN_LED, OUTPUT);
    pinMode(PIN_BUTTON, INPUT_PULLUP);
}

void loop()
{
    uint32_t now = millis();
    heartbeat_poll(now);
    button_poll(now);
    serial_poll();
    status_poll(now);
    /* no delay(): loop() returns quickly so Wi-Fi and the watchdog are serviced */
}
