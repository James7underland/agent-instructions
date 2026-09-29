/**
 * @file    module.c
 * @brief   Implementation of module.h.
 *
 * Template rules (delete this block in real code):
 *  - include the own header FIRST: it proves the header is self-contained
 *    and that definitions match the prototypes;
 *  - everything not in the header is static (internal linkage);
 *  - validate arguments of public functions; internal ones may assert;
 *  - no magic numbers: named constants with units;
 *  - one side effect per variable per expression, braces on every if/for/while.
 */
#include "module.h"

#include <stddef.h>

/* ---- private constants ---------------------------------------------------- */
#define MODULE_COUNTER_MAX  UINT32_MAX

/* ---- private helpers ------------------------------------------------------- */
static bool is_above(const module_t *m, uint16_t input)
{
    return input > m->cfg.threshold;
}

/* ---- public API ------------------------------------------------------------- */
module_err_t module_init(module_t *m, const module_cfg_t *cfg)
{
    if (m == NULL || cfg == NULL) {
        return MODULE_ERR_PARAM;
    }
    m->cfg = *cfg;
    m->counter = 0u;
    m->initialized = true;
    return MODULE_OK;
}

module_err_t module_process(module_t *m, uint16_t input)
{
    if (m == NULL) {
        return MODULE_ERR_PARAM;
    }
    if (!m->initialized) {
        return MODULE_ERR_STATE;
    }
    if (is_above(m, input)) {
        if (m->counter == MODULE_COUNTER_MAX) {
            return MODULE_ERR_OVERFLOW;
        }
        m->counter++;
    }
    return MODULE_OK;
}

uint32_t module_count(const module_t *m)
{
    return (m != NULL) ? m->counter : 0u;
}
