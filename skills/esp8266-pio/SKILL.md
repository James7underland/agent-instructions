---
name: esp8266-pio
description: Wemos (LOLIN) D1 mini на ESP8266 с PlatformIO и фреймворком Arduino (курс «Микропроцессоры»): создание проекта, platformio.ini (env d1_mini, monitor_speed 115200), команды pio run / pio run -t upload / pio device monitor, распиновка D0–D8 ↔ GPIO и опасные при загрузке пины (GPIO0/2/15), Arduino API и где он прячет C, прерывания с IRAM_ATTR, watchdog и yield(), неблокирующий код на millis() вместо delay(), Serial/UART и командный протокол, кнопки с антидребезгом, ШИМ, память (String, F(), PROGMEM), Wi-Fi кратко, расшифровка Exception и перезагрузок. Шаблон проекта и собранные примеры. Используй ВСЕГДА, когда речь о D1 mini, Wemos, ESP8266, NodeMCU, ESP-12, PlatformIO/pio, лабах по микропроцессорам на Arduino-ESP: «помигай светодиодом», «кнопка», «прерывание», «датчик на D1 mini», «перезагружается / Soft WDT reset / Exception», «не прошивается», «какой пин можно», «монитор порта». Правила C и прошивок берутся из скиллов c-core и embedded-c.
---

# esp8266-pio — Wemos D1 mini (ESP8266) + PlatformIO + Arduino

Каталог скилла — папка с этим `SKILL.md`. Общие правила C — **c-core**, архитектура, ISR, автоматы, буферы и
чек-лист ревью — **embedded-c**. Здесь только специфика ESP8266 и PlatformIO. Проверено на
PlatformIO Core 6.2.0, platform espressif8266 4.2.1, Arduino core 3.1.2.

## Создание проекта
1. Папка проекта → скопировать `templates/platformio.ini` и `templates/src/main.cpp` (или `pio project init -b d1_mini`
   и заменить файлы).
2. Структура: `platformio.ini`, `src/main.cpp` (только `setup/loop` и вызовы модулей), `src/*.cpp|*.c` и
   `include/*.h` — модули, `lib/<модуль>/` — переиспользуемые модули без `Arduino.h` (их можно тестировать
   на ПК через `pio test -e native`, нужен `gcc` в PATH), `test/` — тесты Unity. Образец такого модуля с тестами —
   драйвер кнопки из пробной задачи (`Язык C/work/button-driver`).
3. Сборка и прошивка:
   ```
   pio run                      # сборка
   pio run -t upload            # прошивка (порт сам; иначе upload_port = COMx)
   pio device monitor           # монитор 115200, выход Ctrl+C
   pio run -t upload -t monitor
   ```
   Если `pio` не в PATH: `%USERPROFILE%\.platformio\penv\Scripts\pio.exe`.
4. При старте прошивка печатает версию, версию ядра и причину сброса (так сделано в шаблоне).

## Порядок работы над задачей
1. Выбрать пины по `references/pinout-d1mini.md`: для кнопок D1/D2/D5–D7, **не** D3/D4/D8 и не D0 для
   прерываний. Светодиод D4 горит при LOW.
2. Разбить на модули (embedded-c: слои, `init()` + неблокирующий `poll(now)`). В `loop()` — только вызовы `poll`.
3. Время — `millis()` и `if (now - last >= PERIOD)` на `uint32_t`. Никаких `delay()` в логике.
4. Прерывание — только если нужно (короткие импульсы, пробуждение): `IRAM_ATTR`, `volatile`-флаг,
   работа в `loop()`. Кнопки — опрос по тику и антидребезг.
5. Сборка без предупреждений в своём коде (`build_src_flags = -Wall -Wextra` для `src/` и `library.json` с флагами для каждой `lib/<модуль>/`), проверка по
   `embedded-c/references/review-checklist.md` и разделу «Частые ошибки» ниже.
6. Прошить, проверить в мониторе. При сбое — расшифровка Exception (фильтр `esp8266_exception_decoder`).

## Правила кода под ESP8266
- **`loop()` возвращается быстро.** Между вызовами ядро обслуживает Wi-Fi. Долгий цикл → `yield()` внутри
  и таймаут, иначе watchdog (Soft WDT ≈ 3 с, hardware ≈ 8 с).
- **ISR:** `void IRAM_ATTR isr()`, только флаг, счётчик или байт в буфер. Нельзя `delay/yield/Serial/String/new`.
  Всё, что вызывается из ISR, тоже `IRAM_ATTR`. `attachInterrupt(digitalPinToInterrupt(pin), isr, FALLING)`.
- **Общие с ISR данные** `volatile`. Составное — в `noInterrupts()/interrupts()` (микросекунды)
  или `xt_rsil(15)/xt_wsr_ps(ps)`.
- **Память:** RAM ≈ 80 КБ, свободно ≈ 40–50 КБ, стек `loop()` 4 КБ. Большие массивы `static`, без `String` и
  `malloc` в долгоживущем коде, `F("...")` для строк в `Serial.print`, `PROGMEM` + `pgm_read_*` для таблиц.
- **Числа:** FPU нет — целые в мелких единицах или fixed-point. `analogRead(A0)` 0…1023 ≈ 0…3,2 В.
- **ШИМ:** `analogWrite` программный, 0…255 (core 3.x), 1 кГц, не на D0.
- **Serial:** 115200, буфер приёма 256 байт. Строки собирать в `char[]` с контролем длины, не
  `readStringUntil`. `Serial.print` блокирует, когда FIFO TX (128 байт) полон.
- **Wi-Fi:** неблокирующее подключение (автомат плюс `WiFi.status()`), пароли не в репозитории, питание
  выдерживает пики ≈ 300 мА.
- **EEPROM** — эмуляция во flash: `commit()` только при изменении (износ). Файлы — LittleFS.

## Частые ошибки (симптом → причина)
| Симптом | Причина и решение |
|---|---|
| `Soft WDT reset`, `rst cause: 4` | блокирующий цикл или `delay` в ISR/callback. Неблокирующий код, `yield()` в долгих циклах |
| `ISR not in IRAM!`, Exception (0) при прерывании | нет `IRAM_ATTR` у ISR или у вызываемой из него функции |
| Exception (28)/(29) | чтение или запись по NULL или мусорному указателю |
| Exception (9) | невыровненный доступ (`*(uint32_t*)(buf+1)`) |
| Exception (3) | байтовое чтение `PROGMEM` без `pgm_read_*` |
| Не стартует или уходит в прошивку при включении | на D3/D4 тянут к GND, на D8 тянут к 3V3 (пины загрузки) |
| Прерывание на D0 не работает | GPIO16 не поддерживает прерывания |
| Кнопка срабатывает несколько раз | дребезг: опрос плюс N стабильных отсчётов |
| Случайные перезагрузки при Wi-Fi или моторе | просадка питания (brownout), слабый USB или общий провод с мотором |
| Мусор в мониторе при старте | лог ROM на 74880 бод — это нормально. Дальше мусор — не та скорость |
| Постепенно кончается память, падения через часы | `String`/`new` → фрагментация кучи. Смотри `ESP.getMaxFreeBlockSize()` |
| `millis()`-таймер ломается через 49 дней | `now >= t0 + P` вместо `now - t0 >= P` |
| Не прошивается | порт занят монитором, нет драйвера CH340, плохой кабель (только питание). Снизь `upload_speed` |
| Светодиод или реле дёргается при старте | `pinMode(OUTPUT)` до записи уровня: сначала `digitalWrite`, потом `pinMode` |
| Предупреждений нет, а в `lib/` есть ошибки | `build_src_flags` не действуют на `lib/`, нужен `library.json` с `"build": {"flags": [...]}` |
| `"BIT" redefined`, `"REG_SET_BIT" redefined` | имя уже занято Espressif SDK (`c_types.h`), нужен префикс модуля |

## Справочник и файлы
| Файл | Что |
|---|---|
| `references/pinout-d1mini.md` | **таблица пинов**, режимы загрузки, электрические ограничения |
| `references/arduino-esp8266-notes.md` | ядро Arduino изнутри: время, WDT, прерывания, Serial, память, ШИМ, Wi-Fi, команды pio |
| `references/known-issues.md` | найденные проблемы (пополняется) |
| `references/session-log.md` | журнал |
| `templates/platformio.ini` | env `d1_mini` (+ `native` для тестов), монитор 115200 с декодером исключений |
| `templates/src/main.cpp` | неблокирующий каркас: heartbeat, кнопка с антидребезгом, командная строка, статус |
| `examples/blink_nonblocking/main.cpp` | два светодиода без `delay`, без дрейфа, устойчиво к переполнению |
| `examples/button_irq_debounce/main.cpp` | прерывание (IRAM) плюс подтверждение антидребезгом в `loop()` |
| `examples/uart_commands/main.cpp` | текстовый протокол команд: таблица, ограниченный буфер, `OK`/`ERR` |

Пример переносится так: скопировать `main.cpp` примера в `src/` проекта из шаблона, `pio run -t upload -t monitor`.

Перед работой прочитай references/known-issues.md; после задачи допиши находки в references/ и строку в references/session-log.md.
