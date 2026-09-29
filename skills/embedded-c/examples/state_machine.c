/*
 * state_machine.c - see state_machine.h.
 *
 * The "output" (turning lamps on/off) is a stub here; on hardware it would call
 * a lamp driver. Timeouts are evaluated on EV_TICK with rollover-safe math.
 */
#include "state_machine.h"
#include <stddef.h>

static void lamp_show(light_state_t s)
{
    (void)s;    /* hardware hook: led_set(RED/YELLOW/GREEN) */
}

static void enter(light_fsm_t *f, light_state_t next, uint32_t now_ms)
{
    if (next != f->state) {
        f->state = next;
        f->entered_ms = now_ms;
        f->transitions++;
        lamp_show(next);
    }
}

static int yellow_expired(const light_fsm_t *f, uint32_t now_ms)
{
    return (uint32_t)(now_ms - f->entered_ms) >= YELLOW_TIME_MS;   /* safe across rollover */
}

void fsm_init(light_fsm_t *f, uint32_t now_ms)
{
    f->state = ST_RED;
    f->entered_ms = now_ms;
    f->transitions = 0u;
    lamp_show(ST_RED);
}

/* ---- 1) state-centric switch ------------------------------------------- */
light_state_t fsm_switch_step(light_fsm_t *f, light_event_t ev, uint32_t now_ms)
{
    switch (f->state) {
    case ST_RED:
        if (ev == EV_GO) {
            enter(f, ST_GREEN, now_ms);
        }
        break;
    case ST_GREEN:
        if (ev == EV_STOP) {
            enter(f, ST_YELLOW, now_ms);
        }
        break;
    case ST_YELLOW:
        if (ev == EV_TICK && yellow_expired(f, now_ms)) {
            enter(f, ST_RED, now_ms);
        }
        break;
    case ST_COUNT:
    default:
        enter(f, ST_RED, now_ms);      /* corrupted state: go to the safe state */
        break;
    }
    return f->state;
}

/* ---- 2) table-driven ------------------------------------------------------ */
/* Special target meaning "only on timeout" is handled by a guard column. */
typedef struct {
    light_state_t next[EV_COUNT];     /* transition per event (same state = ignore) */
    uint8_t       tick_needs_timeout; /* EV_TICK transition only if the state timed out */
} fsm_row_t;

static const fsm_row_t s_table[ST_COUNT] = {
    [ST_RED]    = { { [EV_NONE] = ST_RED,    [EV_GO] = ST_GREEN,  [EV_STOP] = ST_RED,    [EV_TICK] = ST_RED    }, 0u },
    [ST_YELLOW] = { { [EV_NONE] = ST_YELLOW, [EV_GO] = ST_YELLOW, [EV_STOP] = ST_YELLOW, [EV_TICK] = ST_RED    }, 1u },
    [ST_GREEN]  = { { [EV_NONE] = ST_GREEN,  [EV_GO] = ST_GREEN,  [EV_STOP] = ST_YELLOW, [EV_TICK] = ST_GREEN  }, 0u },
};

light_state_t fsm_table_step(light_fsm_t *f, light_event_t ev, uint32_t now_ms)
{
    const fsm_row_t *row;
    light_state_t next;

    if ((unsigned)f->state >= (unsigned)ST_COUNT) {
        enter(f, ST_RED, now_ms);
        return f->state;
    }
    if ((unsigned)ev >= (unsigned)EV_COUNT) {
        return f->state;                /* unknown event: ignore */
    }
    row = &s_table[f->state];
    next = row->next[ev];
    if (ev == EV_TICK && row->tick_needs_timeout && !yellow_expired(f, now_ms)) {
        next = f->state;
    }
    enter(f, next, now_ms);
    return f->state;
}

const char *fsm_state_name(light_state_t s)
{
    static const char *const names[ST_COUNT] = { "RED", "YELLOW", "GREEN" };
    return ((unsigned)s < (unsigned)ST_COUNT) ? names[s] : "INVALID";
}
