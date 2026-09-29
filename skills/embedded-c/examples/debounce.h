/*
 * debounce.h - counter-based button debouncer.
 *
 * Call debounce_update() from a periodic tick (e.g. every 5-10 ms) with the raw
 * pin level. The stable level changes only after the raw level differs from it
 * for N consecutive samples; press and release thresholds may differ.
 * The module does not touch hardware: the caller reads the pin, so the logic
 * can be unit tested on a PC.
 */
#ifndef DEBOUNCE_H
#define DEBOUNCE_H

#include <stdint.h>

typedef enum {
    DEBOUNCE_NONE = 0,
    DEBOUNCE_PRESSED,     /* stable level changed to the active level */
    DEBOUNCE_RELEASED     /* stable level changed to the inactive level */
} debounce_event_t;

typedef struct {
    uint8_t active_level;     /* raw level that means "pressed": 0 for a button to GND with pull-up */
    uint8_t press_samples;    /* consecutive samples needed to accept a press */
    uint8_t release_samples;  /* consecutive samples needed to accept a release */
    uint8_t stable;           /* current debounced raw level (0/1) */
    uint8_t count;            /* consecutive samples that differ from stable */
} debounce_t;

/* initial_level: raw level read at start-up, so no false event is produced. */
void debounce_init(debounce_t *d, uint8_t active_level,
                   uint8_t press_samples, uint8_t release_samples, uint8_t initial_level);

/* raw_level: 0 or non-zero. Returns an event when the debounced state changes. */
debounce_event_t debounce_update(debounce_t *d, uint8_t raw_level);

/* 1 if the debounced state is "pressed". */
int debounce_is_pressed(const debounce_t *d);

#endif /* DEBOUNCE_H */
