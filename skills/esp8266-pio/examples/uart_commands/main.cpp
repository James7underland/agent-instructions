/*
 * uart_commands - simple text command protocol over Serial (115200 8N1).
 *
 * Protocol: one command per line ('\n', '\r' ignored), words separated by spaces.
 * Replies start with "OK" or "ERR" so a PC script can parse them.
 *   help                 list commands
 *   ver                  firmware version
 *   info                 uptime, free heap, reset reason
 *   led on|off           built-in LED (D4, active LOW)
 *   blink <ms>           blink the LED with a half-period of 20..5000 ms (0 = stop)
 *   echo <text>          repeat text
 * Design: bounded line buffer (overlong lines are rejected, not truncated silently),
 * command table with function pointers (command pattern), strict number parsing
 * with strtoul + range check, non-blocking loop (blink runs while waiting for input).
 */
#include <Arduino.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>

#ifndef FW_VERSION
#define FW_VERSION "0.1.0"
#endif

static const uint8_t PIN_LED   = LED_BUILTIN;
static const size_t  LINE_MAX  = 64u;
static const uint8_t ARGS_MAX  = 4u;

/* ---- LED state (loop context) ----------------------------------------------- */
static bool     s_led_on;
static uint32_t s_blink_half_ms;    /* 0 = not blinking */
static uint32_t s_blink_last;

static void led_set(bool on)
{
    s_led_on = on;
    digitalWrite(PIN_LED, on ? LOW : HIGH);
}

static void blink_poll(uint32_t now)
{
    if (s_blink_half_ms != 0u && now - s_blink_last >= s_blink_half_ms) {
        s_blink_last = now;
        led_set(!s_led_on);
    }
}

/* ---- helpers -------------------------------------------------------------------- */
static bool parse_u32(const char *s, uint32_t min, uint32_t max, uint32_t *out)
{
    char *end;
    unsigned long v;
    if (s == NULL || *s == '\0' || *s == '-' || *s == '+') {
        return false;
    }
    errno = 0;
    v = strtoul(s, &end, 10);
    if (*end != '\0' || errno == ERANGE || v < min || v > max) {
        return false;
    }
    *out = (uint32_t)v;
    return true;
}

/* ---- command handlers ------------------------------------------------------------ */
typedef void (*cmd_fn_t)(int argc, char *argv[]);
typedef struct {
    const char *name;
    cmd_fn_t    fn;
    const char *help;
} cmd_t;

static void cmd_help(int argc, char *argv[]);

static void cmd_ver(int argc, char *argv[])
{
    (void)argc; (void)argv;
    Serial.printf("OK %s\n", FW_VERSION);
}

static void cmd_info(int argc, char *argv[])
{
    (void)argc; (void)argv;
    Serial.printf("OK uptime_s=%lu heap=%u reset=%s\n",
                  (unsigned long)(millis() / 1000u), (unsigned)ESP.getFreeHeap(),
                  ESP.getResetReason().c_str());
}

static void cmd_led(int argc, char *argv[])
{
    if (argc != 2) {
        Serial.println(F("ERR usage: led on|off"));
        return;
    }
    s_blink_half_ms = 0u;
    if (strcmp(argv[1], "on") == 0) {
        led_set(true);
    } else if (strcmp(argv[1], "off") == 0) {
        led_set(false);
    } else {
        Serial.println(F("ERR usage: led on|off"));
        return;
    }
    Serial.println(F("OK"));
}

static void cmd_blink(int argc, char *argv[])
{
    uint32_t ms;
    if (argc != 2 || !parse_u32(argv[1], 0u, 5000u, &ms) || (ms != 0u && ms < 20u)) {
        Serial.println(F("ERR usage: blink <0 | 20..5000>"));
        return;
    }
    s_blink_half_ms = ms;
    s_blink_last = millis();
    if (ms == 0u) {
        led_set(false);
    }
    Serial.println(F("OK"));
}

static void cmd_echo(int argc, char *argv[])
{
    Serial.print(F("OK"));
    for (int i = 1; i < argc; i++) {
        Serial.print(' ');
        Serial.print(argv[i]);
    }
    Serial.println();
}

static const cmd_t s_commands[] = {
    { "help",  cmd_help,  "list commands" },
    { "ver",   cmd_ver,   "firmware version" },
    { "info",  cmd_info,  "uptime, free heap, reset reason" },
    { "led",   cmd_led,   "led on|off" },
    { "blink", cmd_blink, "blink <ms> (0 = stop)" },
    { "echo",  cmd_echo,  "echo <text>" },
};
static const size_t CMD_COUNT = sizeof s_commands / sizeof s_commands[0];

static void cmd_help(int argc, char *argv[])
{
    (void)argc; (void)argv;
    for (size_t i = 0; i < CMD_COUNT; i++) {
        Serial.printf("  %-6s %s\n", s_commands[i].name, s_commands[i].help);
    }
    Serial.println(F("OK"));
}

/* ---- line parsing ----------------------------------------------------------------- */
static void execute_line(char *line)
{
    char *argv[ARGS_MAX];
    int argc = 0;
    char *save = NULL;

    for (char *tok = strtok_r(line, " \t", &save); tok != NULL; tok = strtok_r(NULL, " \t", &save)) {
        if (argc == (int)ARGS_MAX) {
            Serial.println(F("ERR too many arguments"));
            return;
        }
        argv[argc++] = tok;
    }
    if (argc == 0) {
        return;                                   /* empty line */
    }
    for (size_t i = 0; i < CMD_COUNT; i++) {
        if (strcmp(argv[0], s_commands[i].name) == 0) {
            s_commands[i].fn(argc, argv);
            return;
        }
    }
    Serial.printf("ERR unknown command '%s' (try help)\n", argv[0]);
}

static void serial_poll(void)
{
    static char buf[LINE_MAX];
    static size_t len;
    static bool overflow;

    while (Serial.available() > 0) {
        int c = Serial.read();
        if (c < 0 || c == '\r') {
            continue;
        }
        if (c == '\n') {
            if (overflow) {
                Serial.println(F("ERR line too long"));
            } else {
                buf[len] = '\0';
                execute_line(buf);
            }
            len = 0u;
            overflow = false;
        } else if (len < LINE_MAX - 1u) {
            buf[len++] = (char)c;
        } else {
            overflow = true;
        }
    }
}

void setup()
{
    Serial.begin(115200);
    led_set(false);                  /* level first, then output */
    pinMode(PIN_LED, OUTPUT);
    Serial.printf("\nuart_commands %s ready, type 'help'\n", FW_VERSION);
}

void loop()
{
    serial_poll();
    blink_poll(millis());
}
