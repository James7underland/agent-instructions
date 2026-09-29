/*
 * debounce.c - see debounce.h.
 */
#include "debounce.h"

void debounce_init(debounce_t *d, uint8_t active_level,
                   uint8_t press_samples, uint8_t release_samples, uint8_t initial_level)
{
    d->active_level    = (uint8_t)(active_level != 0u);
    d->press_samples   = (press_samples   == 0u) ? 1u : press_samples;
    d->release_samples = (release_samples == 0u) ? 1u : release_samples;
    d->stable          = (uint8_t)(initial_level != 0u);
    d->count           = 0u;
}

debounce_event_t debounce_update(debounce_t *d, uint8_t raw_level)
{
    uint8_t raw = (uint8_t)(raw_level != 0u);
    uint8_t needed;

    if (raw == d->stable) {
        d->count = 0u;                 /* glitch ended: start counting again */
        return DEBOUNCE_NONE;
    }

    needed = (raw == d->active_level) ? d->press_samples : d->release_samples;
    if (d->count < UINT8_MAX) {
        d->count++;
    }
    if (d->count < needed) {
        return DEBOUNCE_NONE;
    }

    d->stable = raw;
    d->count  = 0u;
    return (raw == d->active_level) ? DEBOUNCE_PRESSED : DEBOUNCE_RELEASED;
}

int debounce_is_pressed(const debounce_t *d)
{
    return d->stable == d->active_level;
}
