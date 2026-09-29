/*
 * state_machine.h - traffic light controller implemented two ways:
 *   1) state-centric switch  (fsm_switch_step)
 *   2) table-driven engine   (fsm_table_step)
 * Both have identical behaviour so they can be tested against each other.
 *
 * Behaviour: RED --go--> GREEN --stop--> YELLOW --(YELLOW_TIME_MS)--> RED.
 * "go" in YELLOW is ignored (yellow always ends in red). Invalid events are
 * ignored; a corrupted state recovers to RED (safe state).
 * Time is passed in, so the logic runs on a PC without a real clock.
 */
#ifndef STATE_MACHINE_H
#define STATE_MACHINE_H

#include <stdint.h>

#define YELLOW_TIME_MS 3000u

typedef enum { ST_RED = 0, ST_YELLOW, ST_GREEN, ST_COUNT } light_state_t;
typedef enum { EV_NONE = 0, EV_GO, EV_STOP, EV_TICK, EV_COUNT } light_event_t;

typedef struct {
    light_state_t state;
    uint32_t      entered_ms;     /* time of entering the current state */
    uint32_t      transitions;    /* statistics / test hook */
} light_fsm_t;

void          fsm_init(light_fsm_t *f, uint32_t now_ms);
light_state_t fsm_switch_step(light_fsm_t *f, light_event_t ev, uint32_t now_ms);
light_state_t fsm_table_step(light_fsm_t *f, light_event_t ev, uint32_t now_ms);
const char   *fsm_state_name(light_state_t s);

#endif /* STATE_MACHINE_H */
