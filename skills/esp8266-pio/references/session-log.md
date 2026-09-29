# Журнал работы со скиллом esp8266-pio

| Дата | Что сделано |
|---|---|
| 2026-09-27 | Создан скилл: SKILL.md, распиновка D1 mini, заметки по ядру Arduino ESP8266 и командам pio, шаблон platformio.ini + неблокирующий main.cpp, примеры blink_nonblocking / button_irq_debounce / uart_commands. API сверены с исходниками ядра 3.1.2 (PlatformIO 6.2.0, espressif8266 4.2.1). |
| 2026-09-27 | Этап 5: шаблон и 3 примера собраны `pio run` (d1_mini, 0 предупреждений); пробная задача work/button-driver: сборка d1_mini + 6 тестов Unity `pio test -e native` пройдены. Исправлен порядок pinMode/digitalWrite в шаблоне и примерах, добавлены заметки про lib/library.json, конфликты имён с SDK, PATH для native-тестов. |
| 2026-09-27 | Первая программа пользователя: `C:\Projects\Microprocessors\blink` — мигание LED_BUILTIN 1 Гц на millis() (упрощённый blink_nonblocking, русские комментарии). pio run SUCCESS, 0 предупреждений с -Wall -Wextra; на железе не проверено. Настроен VS Code: unicodeHighlight для кириллицы, Error Lens, Better Comments, cSpell en+ru (Material Icon Theme удалён по просьбе пользователя). |
