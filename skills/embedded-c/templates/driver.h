/**
 * @file    driver.h
 * @brief   <Device> driver - template for an interrupt-driven peripheral driver.
 *
 * Layering: application -> THIS DRIVER -> hal (GPIO/SPI/UART/timer) -> registers.
 * The driver does not know the board: pins and bus come in driver_cfg_t.
 *
 * Contract:
 *  - driver_init()  : once at start-up (or again to recover), main context only;
 *  - driver_poll()  : every main-loop pass, never blocks, handles events from the ISR;
 *  - driver_isr()   : called from the interrupt vector, short, IRAM on ESP8266;
 *  - driver_read()  : main context, returns data collected by the ISR.
 *
 * Template rules (delete this block): rename driver/DRIVER; keep the ISR short;
 * every shared variable volatile with a single writer; all waits have timeouts.
 */
#ifndef DRIVER_H
#define DRIVER_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    DRV_OK = 0,
    DRV_ERR_PARAM,
    DRV_ERR_STATE,
    DRV_ERR_TIMEOUT,
    DRV_ERR_HW,
    DRV_ERR_OVERFLOW
} drv_err_t;

/** Hardware access injected by the board layer (makes the driver testable on a PC). */
typedef struct {
    uint32_t (*now_ms)(void);                  /**< monotonic ms tick */
    int      (*read_pin)(uint8_t pin);         /**< returns 0/1 */
    void     (*write_pin)(uint8_t pin, int level);
} drv_hal_t;

typedef struct {
    const drv_hal_t *hal;
    uint8_t          irq_pin;                   /**< "data ready" input */
    uint8_t          enable_pin;                /**< device enable output */
    uint32_t         timeout_ms;                /**< max time to wait for data ready */
} driver_cfg_t;

drv_err_t driver_init(const driver_cfg_t *cfg);
void      driver_poll(void);
void      driver_isr(void);                     /**< put in IRAM on ESP8266 (see driver.c) */
drv_err_t driver_read(uint16_t *value);         /**< DRV_OK with a fresh value, DRV_ERR_STATE if none */
uint32_t  driver_error_count(void);

#ifdef __cplusplus
}
#endif

#endif /* DRIVER_H */
