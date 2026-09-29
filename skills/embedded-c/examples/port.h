/*
 * port.h - tiny portability layer used by the examples.
 *
 * Critical sections: on a real MCU they disable interrupts and restore the
 * previous state (safe to nest). On a PC build they are no-ops so that the
 * examples compile and run under gcc for unit testing.
 *
 * Select the target with a compiler define:
 *   -DPORT_ESP8266   Arduino core for ESP8266 (xt_rsil / xt_wsr_ps)
 *   -DPORT_CORTEX_M  CMSIS (__get_PRIMASK / __disable_irq / __set_PRIMASK)
 *   (none)           host PC, no real interrupts
 */
#ifndef PORT_H
#define PORT_H

#include <stdint.h>

#if defined(PORT_ESP8266)
    /* ESP8266 Arduino core: xt_rsil/xt_wsr_ps and IRAM_ATTR. Both headers are
       plain C, so this works from .c files that do not include Arduino.h. */
#   include <c_types.h>                   /* IRAM_ATTR */
#   include <core_esp8266_features.h>     /* xt_rsil(), xt_wsr_ps() */
    typedef uint32_t port_irq_state_t;
#   define PORT_IRQ_SAVE_DISABLE()     xt_rsil(15)
#   define PORT_IRQ_RESTORE(state)     xt_wsr_ps(state)
#   define PORT_ISR_ATTR               IRAM_ATTR
#elif defined(PORT_CORTEX_M)
    typedef uint32_t port_irq_state_t;
    static inline port_irq_state_t port_irq_save_disable(void)
    {
        port_irq_state_t s = __get_PRIMASK();
        __disable_irq();
        return s;
    }
#   define PORT_IRQ_SAVE_DISABLE()     port_irq_save_disable()
#   define PORT_IRQ_RESTORE(state)     __set_PRIMASK(state)
#   define PORT_ISR_ATTR
#else
    typedef uint32_t port_irq_state_t;
#   define PORT_IRQ_SAVE_DISABLE()     (0u)
#   define PORT_IRQ_RESTORE(state)     ((void)(state))
#   define PORT_ISR_ATTR
#endif

/* Compiler barrier: stops GCC/Clang from moving memory accesses across it. */
#if defined(__GNUC__)
#   define PORT_COMPILER_BARRIER()     __asm__ __volatile__("" ::: "memory")
#else
#   define PORT_COMPILER_BARRIER()     ((void)0)
#endif

/* C99 compile-time assertion (C11 has _Static_assert). */
#define PORT_STATIC_ASSERT(cond, name) typedef char static_assert_##name[(cond) ? 1 : -1]

#endif /* PORT_H */
