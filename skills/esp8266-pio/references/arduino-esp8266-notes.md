# Arduino-ядро ESP8266 и PlatformIO: что важно для кода на C/C++

## Как устроено: где «прячется» C
- Скетч компилируется как **C++** (`src/main.cpp`), ядро Arduino — это C/C++ поверх Espressif NONOS SDK.
  Твои модули можно писать на C (`*.c` + `.h`). При подключении C-заголовка в C++ нужны
  `extern "C"` в самом заголовке (`#ifdef __cplusplus extern "C" { #endif`).
- Скрытый `main` ядра: инициализация → `setup()` → бесконечно `loop()`, а **между вызовами `loop()`
  обслуживаются Wi-Fi, TCP/IP, таймеры**. Это кооперативная многозадачность: всё держится на том, что
  `loop()` быстро возвращает управление.
- `setup()` и `loop()` выполняются в «контексте CONT» со своим стеком ≈ 4 КБ. Большие локальные массивы → `static`.
- API Arduino (`pinMode`, `digitalWrite`, `millis`, `Serial`) — это HAL. Логику держи в своих модулях,
  которые не зависят от `Arduino.h`: их можно тестировать на ПК (`pio test -e native`).

## Время
- `millis()` — `uint32_t` мс от старта, переполнение через ≈ 49,7 суток. `micros()` — через ≈ 71,6 минуты.
- **Всегда** `if (millis() - t0 >= PERIOD)` на `uint32_t`, никогда `if (millis() >= t0 + PERIOD)`.
- `delay(ms)` внутри вызывает `yield()` (Wi-Fi работает), но блокирует твою логику. В `loop()` используй
  неблокирующий шаблон. `delayMicroseconds()` — активное ожидание, только для коротких задержек.

## Watchdog и yield
- **Программный WDT ≈ 3,2 с** (ядро), **аппаратный ≈ 8 с**. Если `loop()` не возвращается или код не вызывает
  `yield()`/`delay()`, будет сброс: «Soft WDT reset» или `rst cause: 4`.
- Долгие циклы (обработка массива, ожидание устройства) → внутри `yield()` плюс таймаут.
  `yield()` нельзя вызывать из ISR и из callback-функций `Ticker`.
- Цикл больше ≈ 20–50 мс без `yield()` уже вредит Wi-Fi.
- `ESP.wdtFeed()` не лечит блокирующий код. `ESP.wdtDisable()` выключает только программный WDT.

## Прерывания
- `attachInterrupt(digitalPinToInterrupt(pin), isr, RISING|FALLING|CHANGE)`. GPIO16 (D0) не умеет.
- ISR и всё, что он вызывает: `void IRAM_ATTR isr()`. Без этого — падение («ISR not in IRAM!»),
  особенно при записи во flash или работе Wi-Fi.
- В ISR нельзя: `delay`, `yield`, `Serial`, `String`, `new/malloc`, `millis()` можно (быстрая), `micros()` можно.
- Общие переменные — `volatile`. Составные операции в `loop()` — между `noInterrupts()` и `interrupts()`
  (очень коротко) или `uint32_t ps = xt_rsil(15); ... xt_wsr_ps(ps);`.
- Таймеры: `Ticker` (callback-функции в системном контексте, короткие), `timer1_*` (аппаратный, ISR в IRAM,
  конфликтует с `analogWrite`/`tone`/Servo). `timer0` занят Wi-Fi.

## Serial (UART0)
- `Serial.begin(115200)`. В `platformio.ini` `monitor_speed = 115200`. Первые строки мусора — лог ROM
  на 74880 бод, это нормально.
- `Serial.print` блокирует, когда аппаратный FIFO TX (128 байт) полон. Длинный вывод в цикле тормозит систему,
  лог в ISR запрещён.
- Приём: `Serial.available()`, `Serial.read()` (кольцевой буфер ядра, по умолчанию 256 байт,
  `Serial.setRxBufferSize()` до `begin`). Строки собирай сам в `char buf[N]` с контролем длины, не через `String`
  и не через `readStringUntil` (блокирует до таймаута).
- `Serial1` — только TX на GPIO2 (D4).

## Память
- Куча ≈ 50 КБ свободно без Wi-Fi, ≈ 40 КБ с Wi-Fi. `ESP.getFreeHeap()`, `ESP.getMaxFreeBlockSize()`,
  `ESP.getHeapFragmentation()`.
- `String` фрагментирует кучу. Для долгоживущих систем — `char[]` + `snprintf`.
- Литералы в `Serial.print(F("text"))` лежат во flash, а не в RAM. Таблицы — `static const ... PROGMEM` и
  `pgm_read_byte/word/dword()`. Обращение к flash-данным **не 32-битным выровненным** чтением даёт
  `Exception (3)`.
- `EEPROM` — эмуляция в секторе flash (`begin(size)`, `put/get`, `commit()` стирает сектор, не вызывай его часто).
  Файлы — `LittleFS`.

## Числа
Нет FPU. `float`/`double` эмулируются, `%f` в `printf` работает, но дорого. Используй целые в мелких
единицах (мВ, 0,01 °C) или fixed-point. `analogRead(A0)` → 0…1023 (0…3,2 В на D1 mini).

## ШИМ
`analogWrite(pin, duty)` — программный ШИМ. Диапазон 0…255 (core 3.x) — настраивается `analogWriteRange()`,
частота 1 кГц — `analogWriteFreq()`. Не на GPIO16.

## Wi-Fi (кратко)
```cpp
WiFi.mode(WIFI_STA);
WiFi.begin(ssid, pass);            // non-blocking: check WiFi.status() in loop()
// if (WiFi.status() == WL_CONNECTED) { ... }
```
- Не жди подключения в `while` без таймаута и `yield()`. Автомат: «подключаюсь → подключён → переподключение».
- Пароли не хранить в репозитории: `secrets.h` в `.gitignore` или `build_flags = -DWIFI_SSID=...` из
  переменных окружения.
- Пики тока ≈ 300 мА: нужно нормальное питание, иначе brownout-сбросы.
- OTA: `ArduinoOTA` или `ESP8266httpUpdate` (см. `embedded-c/references/19-connected-ota.md`).

## Причина сброса и диагностика
- При старте печатай: версию, `ESP.getResetReason()`, `ESP.getFreeHeap()`, `ESP.getChipId()`,
  `ESP.getCoreVersion()`.
- Аварии печатают `Exception (N)` и стек. `monitor_filters = esp8266_exception_decoder` расшифрует адреса
  (нужен ELF этой же сборки). Коды — в `embedded-c/references/18-debugging-faults.md`.

## PlatformIO — команды
| Команда | Что делает |
|---|---|
| `pio project init -b d1_mini` | создать проект в текущей папке |
| `pio run` | собрать (окружение по умолчанию) |
| `pio run -e d1_mini` | собрать конкретное окружение |
| `pio run -t upload` | собрать и прошить (порт выбирается сам или `upload_port = COM5`) |
| `pio device list` | список COM-портов |
| `pio device monitor` | монитор порта (скорость из `monitor_speed`), выход Ctrl+C |
| `pio run -t upload -t monitor` | прошить и открыть монитор |
| `pio run -t clean` | очистить сборку |
| `pio run -v` | подробная сборка (размеры RAM и flash) |
| `pio test -e native` | тесты на ПК (нужен gcc в PATH) |
| `pio pkg update` | обновить платформу и библиотеки |

Если `pio` нет в PATH: `%USERPROFILE%\.platformio\penv\Scripts\pio.exe`.
Структура проекта: `platformio.ini`, `src/` (main.cpp и модули), `include/` (общие .h), `lib/<name>/`
(свои библиотеки, по модулю на папку), `test/` (тесты Unity).
