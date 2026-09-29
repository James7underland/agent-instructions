# Известные проблемы (esp8266-pio)

Формат: симптом → причина → решение. Пополняется после каждой задачи.

## Окружение (Windows, PlatformIO)
- PlatformIO ставился в отдельное окружение `%USERPROFILE%\.platformio\penv` командой
  `python -m venv` + `pip install platformio`. Первая попытка упала: файлы в `site-packages` пропадали
  или были «заняты другим процессом» (вероятно, антивирус). Помогла повторная установка с
  `--force-reinstall pip platformio`. Если `pio` ведёт себя странно, переустанови так же.
- При сборке `elf2bin.py` из ядра печатает `SyntaxWarning: "\s" is an invalid escape sequence` (Python 3.12+).
  Это предупреждение внутри инструмента ядра, на прошивку не влияет, и исправлять его не нужно.
- Первая `pio run` скачивает framework-arduinoespressif8266 (≈ 1 мин), дальше сборка быстрая.
- `build_flags` применяются и к ядру: `-Werror` там сломает сборку из-за чужих предупреждений.
  Для своих файлов есть `build_src_flags`.

## Проверено по исходникам ядра 3.1.2 (framework-arduinoespressif8266 3.30102.0)
- `IRAM_ATTR` определён в `tools/sdk/include/c_types.h`. `ICACHE_RAM_ATTR` устарел (deprecated).
- `attachInterrupt` для функции не из IRAM печатает «ISR not in IRAM!» и падает (`core_esp8266_wiring_digital.cpp`).
- Прерывания только для `pin < 16`: GPIO16 (D0) не поддерживается.
- `analogWrite`: `analogScale = 255` по умолчанию (в 2.x было 1023). Старые примеры с 1023 дают «всегда 100 %».
- `Serial`: буфер приёма 256 байт (`_rx_size(256)`), FIFO передачи 128 байт (`UART_TX_FIFO_SIZE 0x80`).
- Стек `loop()` (`CONT_STACKSIZE`) = 4096 байт.
- `esp8266::InterruptLock` есть в `cores/esp8266/interrupts.h`. `xt_rsil()` — в `core_esp8266_features.h`.
- Макросы пинов варианта `d1_mini`: `D0 = 16` … `D8 = 15`, `LED_BUILTIN = 2`.
- Пустой скетч занимает ≈ 28 КБ RAM из 80 КБ и ≈ 265 КБ flash.

## Найдено на проверке (этап 5, 2026-09-27)
- **Порядок настройки выхода.** `pinMode(pin, OUTPUT)` до записи уровня даёт короткий импульс со значением
  регистра выхода по умолчанию: светодиод D4 мигает при старте, реле может щёлкнуть. В ядре `digitalWrite`
  пишет в `GPOS/GPOC` в любом режиме ножки, поэтому правильно **сначала `digitalWrite(pin, level)`, потом
  `pinMode(pin, OUTPUT)`**. Исправлено в шаблоне и во всех примерах.
- **`build_src_flags` не действует на `lib/<name>/`.** Свои библиотеки в `lib/` собирались без `-Wall -Wextra`.
  Решение: у каждой своей библиотеки файл `lib/<name>/library.json` с `"build": {"flags": ["-Wall", "-Wextra"]}`.
  Проверка: `pio run -v | grep <file>.c` должен содержать `-Wextra`.
- **Имена макросов пересекаются с Espressif SDK.** В `tools/sdk/include/c_types.h` уже определены `BIT(nr)` и
  `REG_SET_BIT` и др., а с ними в .c-файлах появляется «redefined». Давай макросам модульный префикс
  (`BIT_U32`, `RA_SET_BIT`).
- **C-файл без `Arduino.h` не видит `IRAM_ATTR` и `xt_rsil`.** Подключай `<c_types.h>` (IRAM_ATTR) и
  `<core_esp8266_features.h>` (xt_rsil/xt_wsr_ps), так сделано в `embedded-c/examples/port.h`.
- **`pio test -e native` на Windows** требует `gcc` в PATH процесса. PATH из Git Bash до `pio.exe` не доходит,
  нужен запуск из PowerShell с `$env:PATH = "<...\mingw64\bin>;" + $env:PATH`. Unity ставится сам при первом запуске.

## VS Code (найдено 2026-09-27, первая программа blink)
- **Русские комментарии в рамках.** В недоверенной папке (Restricted Mode) VS Code подсвечивает все не-ASCII символы
  (`editor.unicodeHighlight.nonBasicASCII` = `inUntrustedWorkspace`). Решение: доверить папку (лучше родительскую
  `C:\Projects\Microprocessors`) и/или в user settings `nonBasicASCII: false`, `allowedLocales: {"ru": true}`,
  `includeComments: false`. `ambiguousCharacters` не выключать — ловит русскую «с»/«о» в идентификаторах.
- **Проверка `-Wall -Wextra` без правки ini:** `$env:PLATFORMIO_BUILD_SRC_FLAGS = "-Wall -Wextra"` перед `pio run`
  (проверено: флаг попадает в команду компиляции `src/main.cpp`).
