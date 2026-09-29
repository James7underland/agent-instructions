/**
 * @file    driver.c
 * @brief   Template implementation of driver.h.
 *
 * Flow: device raises "data ready" -> driver_isr() sets a flag and a timestamp
 * -> driver_poll() in the main loop reads the device and stores the value
 * -> application calls driver_read(). A watchdog-style timeout detects a dead device.
 */
#include "driver.h"

#if defined(ARDUINO_ARCH_ESP8266)
#   include <Arduino.h>
#   define DRV_ISR_ATTR IRAM_ATTR          /* ISR and everything it calls must be in IRAM */
#else
#   define DRV_ISR_ATTR
#endif

/* ---- state shared with the ISR (single writer each) ------------------------ */
static volatile bool     s_data_ready;       /* written by ISR (true) and poll (false) under guard */
static volatile uint32_t s_isr_count;        /* written only by ISR */

/* ---- main-context state ------------------------------------------------------ */
typedef enum { DRV_ST_OFF = 0, DRV_ST_WAIT, DRV_ST_ERROR } drv_state_t;

static driver_cfg_t s_cfg;
static drv_state_t  s_state = DRV_ST_OFF;
static uint32_t     s_wait_start_ms;
static uint16_t     s_value;
static bool         s_value_fresh;
static uint32_t     s_errors;

/* ---- device access (replace with real SPI/I2C transfers) ------------------- */
static drv_err_t device_read_sample(uint16_t *out)
{
    *out = 0u;                                /* TODO: bus transfer with its own timeout */
    return DRV_OK;
}

/* ---- public API -------------------------------------------------------------- */
drv_err_t driver_init(const driver_cfg_t *cfg)
{
    if (cfg == NULL || cfg->hal == NULL || cfg->hal->now_ms == NULL ||
        cfg->hal->read_pin == NULL || cfg->hal->write_pin == NULL || cfg->timeout_ms == 0u) {
        return DRV_ERR_PARAM;
    }
    s_cfg = *cfg;
    s_data_ready = false;
    s_value_fresh = false;
    s_errors = 0u;

    s_cfg.hal->write_pin(s_cfg.enable_pin, 1);        /* power up / enable the device */
    /* Board layer attaches driver_isr() to irq_pin AFTER this point. */
    s_wait_start_ms = s_cfg.hal->now_ms();
    s_state = DRV_ST_WAIT;
    return DRV_OK;
}

void DRV_ISR_ATTR driver_isr(void)
{
    /* Keep it short: flag + counter only. No bus transfers, no printing. */
    s_isr_count = s_isr_count + 1u;
    s_data_ready = true;
}

void driver_poll(void)
{
    uint32_t now;

    if (s_state != DRV_ST_WAIT) {
        return;
    }
    now = s_cfg.hal->now_ms();

    if (s_data_ready) {
        uint16_t v;
        s_data_ready = false;                  /* single bool store: atomic; a new ISR just sets it again */
        if (device_read_sample(&v) == DRV_OK) {
            s_value = v;
            s_value_fresh = true;
        } else {
            s_errors++;
        }
        s_wait_start_ms = now;
    } else if ((uint32_t)(now - s_wait_start_ms) >= s_cfg.timeout_ms) {
        s_errors++;                            /* device silent: recover instead of hanging */
        s_cfg.hal->write_pin(s_cfg.enable_pin, 0);
        s_cfg.hal->write_pin(s_cfg.enable_pin, 1);
        s_wait_start_ms = now;
    }
}

drv_err_t driver_read(uint16_t *value)
{
    if (value == NULL) {
        return DRV_ERR_PARAM;
    }
    if (!s_value_fresh) {
        return DRV_ERR_STATE;
    }
    *value = s_value;
    s_value_fresh = false;
    return DRV_OK;
}

uint32_t driver_error_count(void)
{
    return s_errors;
}
