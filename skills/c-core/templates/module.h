/**
 * @file    module.h
 * @brief   <One line: what this module does.>
 *
 * <Short description: responsibility, what it hides, who uses it.>
 *
 * Usage:
 *   module_t m;
 *   module_init(&m, &cfg);
 *   module_process(&m, input);
 *
 * Thread/ISR safety: <e.g. not reentrant; do not call from interrupts>.
 *
 * Template rules (delete this block in real code):
 *  - rename MODULE / module_ everywhere; guard name = FILE NAME + _H;
 *  - the header includes everything it needs and nothing more;
 *  - only public API here: types the caller needs, prototypes, constants;
 *  - every function: purpose, parameters, return value, limits;
 *  - no variable definitions in a header (extern only, and avoid globals).
 */
#ifndef MODULE_H
#define MODULE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/** Error codes returned by the module (0 is always success). */
typedef enum {
    MODULE_OK = 0,
    MODULE_ERR_PARAM,        /**< invalid argument (NULL, out of range) */
    MODULE_ERR_STATE,        /**< called in the wrong state (e.g. before init) */
    MODULE_ERR_OVERFLOW      /**< result or buffer would overflow */
} module_err_t;

/** Configuration passed to module_init(); copied, caller may reuse it. */
typedef struct {
    uint16_t threshold;      /**< <meaning, unit, valid range> */
} module_cfg_t;

/**
 * Instance state. Fields are private: access them only through the functions below.
 * (Declared here so the caller can allocate instances statically, no malloc.)
 */
typedef struct {
    module_cfg_t cfg;
    uint32_t     counter;
    bool         initialized;
} module_t;

/**
 * @brief  Initializes an instance. Safe to call again to reset it.
 * @param  m    instance, must not be NULL
 * @param  cfg  configuration, must not be NULL
 * @return MODULE_OK or MODULE_ERR_PARAM
 */
module_err_t module_init(module_t *m, const module_cfg_t *cfg);

/**
 * @brief  Processes one input value.
 * @param  m      initialized instance
 * @param  input  <meaning, unit, range>
 * @return MODULE_OK, MODULE_ERR_STATE if not initialized, MODULE_ERR_OVERFLOW
 */
module_err_t module_process(module_t *m, uint16_t input);

/** @brief Number of inputs above the threshold since init. */
uint32_t module_count(const module_t *m);

#ifdef __cplusplus
}
#endif

#endif /* MODULE_H */
