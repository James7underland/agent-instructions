# Журнал работы со скиллом embedded-c

| Дата | Что сделано |
|---|---|
| 2026-09-27 | Создан скилл: прочитана «Making Embedded Systems» 2-е изд. (428 с., гл. 1–14), 23 конспекта в references/ (в т. ч. isr-rules, review-checklist), примеры ring_buffer/debounce/state_machine/fixed_point/register_access/isr_events + demo_main (gcc 16.1 -std=c99 -Wall -Wextra -Werror -pedantic, demo OK), шаблоны driver.h/.c и main_superloop.c. |
| 2026-09-27 | Этап 5: тесты ring_buffer и fixed_point (assert, -O0/-O2, UBSan trap) пройдены; port.h исправлен для ESP8266 (c_types.h, core_esp8266_features.h), модули собраны под d1_mini, rb_put в IRAM; REG_* → RA_* (конфликт с SDK). Пробная задача «драйвер кнопки» → 3 находки в known-issues, 3 пункта в review-checklist. |
