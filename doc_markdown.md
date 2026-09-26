# Оформление отчетов и технической документации в формате Markdown

Этот модуль определяет правила разметки, стилизации, типографики и переносимости документации в формате Markdown.

Инструкция действует как постоянный системный промпт для любой нейросети при создании или форматировании отчетов по лабораторным работам, пояснительных записок, ТЗ, планов реализации и архитектурных описаний в файлах `.md`.

---

## 1. Роль и критерии качества

1. **Markdown как исходный код:** Markdown — это структурированный исходный код документации, а не просто результат рендеринга. Он должен легко читаться глазами в текстовом редакторе и давать минимальный, понятный дифф в Git.
2. **Переносимость и кроссплатформенность:** документ обязан корректно отображаться:
   - Во встроенных просмотрщиках IDE (VS Code, Antigravity IDE, Cursor);
   - В веб-интерфейсе GitHub / GitLab;
   - В Obsidian;
   - При конвертации в HTML и печати в PDF.
3. **Адаптивность тем (Dark / Light mode):** оформление документа обязано сохранять идеальную читаемость как в светлой, так и в темной теме оформления редактора.

---

## 2. Базовые технические параметры файла

| Параметр | Требование | Обоснование |
|---|---|---|
| **Кодировка** | UTF-8 **без BOM** | BOM ломает распознавание заголовков парсерами |
| **Окончания строк** | LF (`\n`) | Единый стандарт Unix/Git, фиксируется в `.gitattributes` |
| **Отступы** | Только пробелы (2 или 4) | Табуляция по-разному отображается на разных платформах |
| **Переносы строк** | Семантические переносы (одно предложение — одна строка) | Изменение одного слова не перекладывает весь абзац в Git diff |
| **Пустые строки** | Ровно одна пустая строка между блоками | Предотвращает визуальное расползание документа |
| **Имена файлов** | Говорящие имена, разделитель `_`, расширение `.md` | Мгновенная понятность назначения файла |

---

## 3. Навигация и относительные ссылки

В любых Markdown-документах репозитория:

1. **Только относительные пути от корня проекта:**
   - Правильно: `[src/root_solvers.py](src/root_solvers.py)`
   - Правильно: `[docs/lab3/stage1_tz.md](docs/lab3/stage1_tz.md)`
2. **Категорический запрет абсолютных путей и `file://`:**
   - Запрещено: `file:///C:/Users/.../src/root_solvers.py`
   - Запрещено: `C:\Users\...\src\root_solvers.py`
   - Запрещено: `/home/.../src/root_solvers.py`
3. **Преимущества:**
   - Полная независимость от конкретного компьютера и имени пользователя ОС.
   - Поддержка мгновенного перехода к коду по клику (Ctrl+Click / Cmd+Click) в среде разработки (IDE).

---

## 4. Адаптивные CSS-стили: экранный просмотр и печать по ГОСТ

### Проблема жесткой фиксации цвета
При оформлении отчетов по ГОСТ часто ошибочно внедряют `color: #000;` в глобальные селекторы. В результате в темной теме редактора черный текст накладывается на черный фон, делая документ нечитаемым.

### Принцип разделения контекстов
1. **Экранный предпросмотр (Dark / Light mode):**
   - Цвет текста не фиксируется константой, а наследуется из темы редактора (`color: inherit;`).
   - Ссылки и линии таблиц адаптируются под контраст темы.
2. **Печать и экспорт в PDF (`@media print`):**
   - Все строгие требования ГОСТ (чисто белый фон, абсолютно черный текст, сплошные черные границы таблиц, поля 20/15/20/30 мм) помещаются исключительно внутрь `@media print`.

### Эталонный блок стилей для вставки в начало `.md` отчета:

```html
<style>
@page {
  size: A4;
  margin: 20mm 15mm 20mm 30mm; /* поля по ГОСТ: верх 20мм, право 15мм, низ 20мм, лево 30мм */
}

/* Базовые параметры текста: шрифт Times New Roman, 14 pt, 1.5 интервал */
html,
.markdown-body,
body {
  font-family: "Times New Roman", Times, serif;
  font-size: 14pt;
  line-height: 1.5;
  hyphens: none;
  max-width: 100% !important;
  overflow-x: hidden !important;
}

/* Абзацы: выравнивание по ширине, красная строка 1.25 см */
.markdown-body p,
body p {
  text-align: justify;
  text-indent: 1.25cm;
  margin: 0 0 0.4em 0;
  orphans: 2;
  widows: 2;
}

.markdown-body li,
body li {
  text-align: justify;
  text-indent: 0;
}

/* Заголовки: кегль 14 пт, полужирный, по центру, без отрыва от текста */
.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
body h1,
body h2,
body h3,
body h4 {
  font-size: 14pt !important;
  font-weight: bold !important;
  font-family: "Times New Roman", Times, serif;
  line-height: 1.3;
  text-align: center;
  text-indent: 0;
  margin-top: 1.2em;
  margin-bottom: 0.6em;
  break-after: avoid;
  page-break-after: avoid;
  break-inside: avoid;
  page-break-inside: avoid;
}

/* Разделитель страниц: тонкая линия в превью, разрыв страницы при печати */
hr {
  border: 0;
  border-top: 1px solid rgba(128, 128, 128, 0.4);
  margin: 1.5em 0;
  page-break-after: always;
  break-after: page;
}

/* Нижний колонтитул с номером страницы по ГОСТ (по центру, 14 пт, без точки) */
.page-footer {
  text-align: center !important;
  text-indent: 0 !important;
  font-family: "Times New Roman", Times, serif;
  font-size: 14pt;
  font-weight: normal !important;
  margin: 1.8em 0 0.5em 0;
  clear: both;
}

/* Подписи к таблицам */
.table-caption,
p:has(+ table) {
  text-align: left !important;
  text-indent: 0 !important;
  margin: 1em 0 0.25em 0;
  font-family: "Times New Roman", Times, serif !important;
  font-size: 14pt !important;
  break-after: avoid;
  page-break-after: avoid;
}

/* Иллюстрации и подписи к ним */
figure {
  text-align: center !important;
  margin: 1.2em auto;
  break-inside: avoid;
  page-break-inside: avoid;
}

figure img {
  display: block;
  margin: 0 auto;
  max-width: 100%;
}

figcaption,
.fig-caption {
  display: block;
  text-align: center !important;
  text-indent: 0 !important;
  margin: 0.5em 0 1.2em 0;
  font-family: "Times New Roman", Times, serif !important;
  font-size: 14pt !important;
  break-before: avoid;
  page-break-before: avoid;
}

/* Таблицы: строгая посадка по ширине страницы, центрирование и сплошной полужирный заголовок */
.markdown-body table,
body table {
  border-collapse: collapse;
  margin: 0.5em auto 1em auto;
  width: 100% !important;
  max-width: 100% !important;
  table-layout: fixed;
  font-size: 13pt; /* по ГОСТ допускается на 1-2 пт меньше основного текста */
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.markdown-body th,
.markdown-body td,
body th,
body td {
  padding: 5px 6px;
  text-align: center;
  vertical-align: middle;
  text-indent: 0 !important;
  border: 1px solid rgba(128, 128, 128, 0.4);
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: normal;
  hyphens: auto;
}

.markdown-body th,
body th,
.markdown-body th *,
body th * {
  font-weight: bold !important;
}

.markdown-body th[align="left"],
.markdown-body td[align="left"],
body th[align="left"],
body td[align="left"] {
  text-align: left !important;
}

/* Категорический запрет моноширинных серых плашек кода по ГОСТ */
code,
.markdown-body code,
body code {
  background: none !important;
  background-color: transparent !important;
  border: none !important;
  padding: 0 !important;
  font-family: inherit !important;
  font-size: inherit !important;
  color: inherit !important;
  font-weight: inherit !important;
}

/* Формулы по ГОСТ: выражение по центру, номер справа */
.eq {
  display: grid;
  grid-template-columns: 1fr 3em;
  align-items: center;
  column-gap: 0.5em;
  width: 100%;
  margin: 0.9em 0;
  text-indent: 0 !important;
}

.eq-body {
  text-align: center !important;
  text-indent: 0 !important;
  overflow: visible;
}

.katex-display {
  max-width: 100% !important;
  overflow: visible !important;
}

.eq-body p {
  text-align: center !important;
  text-indent: 0 !important;
  margin: 0;
}

.eq-num {
  text-align: right !important;
  text-indent: 0 !important;
  font-family: "Times New Roman", Times, serif;
  font-size: 14pt;
  white-space: nowrap;
}

/* Содержание по ГОСТ: нежирный шрифт, отточия к номеру страницы у правого края */
.toc-title {
  text-align: center !important;
  font-family: "Times New Roman", Times, serif;
  font-size: 14pt;
  font-weight: bold;
  text-transform: uppercase;
  margin: 1.5em 0 1.2em 0;
  text-indent: 0 !important;
}

.toc-list {
  list-style: none;
  padding-left: 0;
  margin: 0.5em 0 1.5em 0;
  font-family: "Times New Roman", Times, serif;
  font-size: 14pt;
  line-height: 1.5;
}

.toc-list li {
  margin: 0.25em 0;
  text-indent: 0 !important;
  text-align: left !important;
  font-weight: normal !important;
}

.toc-list li.toc-h2 {
  font-weight: normal !important;
}

.toc-list li.toc-h3 {
  padding-left: 1.25cm;
  font-weight: normal !important;
}

.toc-list a {
  display: block;
  text-decoration: none;
  color: inherit;
  width: 100%;
}

.toc-list a:hover {
  text-decoration: none;
}

.toc-list a:hover .toc-title-text,
.toc-list a:hover .toc-line1 {
  text-decoration: underline;
}

.toc-single,
.toc-line2 {
  display: flex;
  align-items: baseline;
  width: 100%;
}

.toc-line1 {
  display: block;
  white-space: nowrap;
}

.toc-title-text {
  flex-shrink: 0;
  white-space: nowrap;
}

.toc-leader {
  flex-grow: 1;
  overflow: hidden;
  white-space: nowrap;
  font-family: "Times New Roman", Times, serif;
  font-size: 14pt;
  line-height: 1;
  margin: 0 0.35em;
  padding: 0;
}

.toc-page {
  flex-shrink: 0;
  font-family: "Times New Roman", Times, serif;
  font-size: 14pt;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

/* Печать по ГОСТ: абсолютно белый фон, черный текст, разрыв страниц */
@media print {
  body, .markdown-body {
    background-color: #ffffff !important;
    color: #000000 !important;
  }
  .markdown-body th,
  .markdown-body td,
  body th,
  body td {
    border: 1px solid #000000 !important;
  }
  hr {
    visibility: hidden;
    margin: 0 !important;
    padding: 0 !important;
    page-break-after: always;
    break-after: page;
  }
}
</style>
```

---

## 5. Постраничная эквивалентность (1 страница .md = 1 печатная страница Word/PDF)

1. **Принцип соответствия физической странице:**
   - Каждая страница в `.md` документе должна соответствовать ровно одной печатной странице формата А4 в MS Word или PDF.
   - Это гарантирует корректную пагинацию, предсказуемое оглавление и исключает смещение иллюстраций и таблиц при конвертации.
2. **Разделители страниц `---`:**
   - Линии `---` используются **исключительно** как границы печатных страниц (`break-after: page;`).
   - Категорически запрещено использовать `---` внутри страницы для декоративного или тематического разделения абзацев.
3. **Нижний колонтитул с номером страницы:**
   - На каждой странице (начиная со страницы 2) в самом низу перед разделителем `---` размещается центрированный номер страницы:
     ```html
     <div class="page-footer">2</div>

     ---
     ```
   - Шрифт колонтитула — Times New Roman, 14 pt, обычный, без точки после цифры по ГОСТ.
4. **Титульный лист (страница 1):**
   - Номер страницы не проставляется (но страница входит в общую сквозную нумерацию).
   - Внизу страницы 1 располагается блок с городом и годом (`<div class="title-city"><p>Москва, 2026</p></div>`).
   - Перед стилями `<style>` или титульным листом запрещено ставить служебный заголовок `# Отчёт...` — документ сразу открывается титульной структурой.

---

## 6. Оформление глав, содержания и структурных элементов

### 1. Заголовки глав и структурных элементов
- **Формат заголовка главы:** номер главы и ее название разделяются переносом строки без точки после номера главы:
  ```markdown
  ## <a id="глава-1"></a>ГЛАВА 1<br/>КРАТКИЕ ТЕОРЕТИЧЕСКИЕ СВЕДЕНИЯ
  ```
- **Структурные разделы без номеров:** Заголовки разделов «ЦЕЛЬ РАБОТЫ», «ВВЕДЕНИЕ», «ЗАКЛЮЧЕНИЕ», «ВЫВОДЫ», «СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ» являются названиями глав того же ранга (`##`) и обязательно оформляются **ТОЛЬКО ЗАГЛАВНЫМИ БУКВАМИ**:
  ```markdown
  ## <a id="цель-работы"></a>ЦЕЛЬ РАБОТЫ
  ## <a id="выводы"></a>ВЫВОДЫ
  ## <a id="список-использованных-источников"></a>СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ
  ```
- **Кегль заголовков:** все заголовки глав (`##`) и подглав (`###`) оформляются строго **кеглем 14 pt полужирным шрифтом**.
- **Смысловые мостики по ГОСТ (запрет висячих заголовков):**
  - Между заголовком главы и первым подразделом обязательно размещается краткий обзорный текст (2–3 содержательных предложения о том, чему посвящена глава).
  - Запрещено сразу за заголовком главы давать заголовок подраздела `1.1`.

### 2. Содержание (СОДЕРЖАНИЕ)
- Пункты глав и подглав в содержании **не выделяются полужирным шрифтом** (обычное начертание `font-weight: normal`).
- В названиях глав **точка после номера главы не ставится**: `ГЛАВА X НАЗВАНИЕ ГЛАВЫ` (не `ГЛАВА X. НАЗВАНИЕ ГЛАВЫ`).
- Структурные разделы («ЦЕЛЬ РАБОТЫ», «ВЫВОДЫ», «СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ») в содержании также пишутся заглавными буквами.
- **Размер и начертание точек:** Отточия выполняются текстовыми символами точки `.` шрифта Times New Roman кегля **14 pt** (как основной текст). Использование микроскопических CSS-бордеров (`1px dotted`) **запрещено**.
- **Отступы отточий:** Между названием раздела и началом ряда точек, а также между концом ряда точек и номером страницы задается небольшой полупробельный зазор (`margin: 0 0.35em`).
- **Двухстрочные заголовки глав:** Если название главы длинное и не умещается на одной строке вместе с отточиями и номером страницы, оно разбивается на две строки:
  - 1-я строка (`.toc-line1`): начальная смысловая часть названия главы;
  - 2-я строка (`.toc-line2`): окончание названия, за которым следуют отточия (`.toc-leader`) и номер страницы (`.toc-page`).
  Это предотвращает вытеснение точек и прилипание номера страницы к тексту заголовка при узких контейнерах или печати.
- **Пример разметки содержания:**
  ```html
  <ul class="toc-list">
    <!-- Однострочный пункт главы -->
    <li class="toc-h2"><a href="#глава-1"><span class="toc-single"><span class="toc-title-text">ГЛАВА 1 КРАТКИЕ ТЕОРЕТИЧЕСКИЕ СВЕДЕНИЯ</span><span class="toc-leader">....................................................................................................</span><span class="toc-page">3</span></span></a></li>
    
    <!-- Подраздел с отступом 1,25 см -->
    <li class="toc-h3"><a href="#11-назначение-и-методы-контроля-качества-в-нефтепереработке"><span class="toc-single"><span class="toc-title-text">1.1. Назначение и методы контроля качества в нефтепереработке</span><span class="toc-leader">....................................................................................................</span><span class="toc-page">3</span></span></a></li>
    
    <!-- Двухстрочный пункт длинной главы -->
    <li class="toc-h2">
      <a href="#глава-4">
        <span class="toc-line1">ГЛАВА 4 ПОСТРОЕНИЕ МОДЕЛИ МНК</span>
        <span class="toc-line2">
          <span class="toc-title-text">С ОГРАНИЧЕНИЕМ ПРОХОЖДЕНИЯ ЧЕРЕЗ ТОЧКУ</span>
          <span class="toc-leader">....................................................................................................</span>
          <span class="toc-page">11</span>
        </span>
      </a>
    </li>

    <!-- Структурный раздел заглавными буквами -->
    <li class="toc-h2"><a href="#выводы"><span class="toc-single"><span class="toc-title-text">ВЫВОДЫ</span><span class="toc-leader">....................................................................................................</span><span class="toc-page">15</span></span></a></li>
  </ul>
  ```
- Подразделы в содержании оформляются с отступом 1,25 см (`padding-left: 1.25cm;`).
- Номера страниц в содержании обязаны строго совпадать с фактической страницей начала соответствующего раздела.

### 3. Формулы
- Все математические выражения оформляются в синтаксисе $\LaTeX$:
  - Внутри текста: `$x_i \in [a, b]$`.
  - Выключные формулы: `$$f(x) = 0$$`. Разделители `$$` обязательно размещаются на собственных отдельных строках с пустыми строками до и после — это предотвращает экранирование переносов строк `\\` Markdown-парсерами.
- Если формула нумеруется по ГОСТ (номер справа в круглых скобках):
  ```html
  <div class="eq">
    <div class="eq-body">

    $$
    Q = \mu \cdot S \cdot \sqrt{\frac{2\Delta P}{\rho}}
    $$

    </div>
    <div class="eq-num">(1)</div>
  </div>
  ```
- **Категорический запрет горизонтального скролла в формулах и распирания страницы:**
  - Формулы никогда не должны вызывать появление полосы прокрутки внутри блока `.eq-body` или по ширине всей страницы.
  - В стилях `.katex-display` обязательно задается `overflow: visible !important;` (правило `overflow-x: auto` запрещено, так как провоцирует появление полос прокрутки под формулами при малейшем касании границ блока).
  - Контейнер формулы `.eq` использует двухколоночную сетку `grid-template-columns: 1fr 3em; column-gap: 0.5em;`, поэтому полезная ширина `.eq-body` на листе A4 составляет около 550–580 px.
  - Длинные аналитические выражения, громоздкие матрицы и цепочки численных подстановок обязаны разбиваться на строки через окружение `\begin{aligned}...\end{aligned}`:
    - Арифметические выражения с несколькими слагаемыми и десятичными дробями (от 3–4 слагаемых с множителями) **обязательно разбиваются на 3 и более строк**:
      1. Левая часть и первые 1–2 слагаемых с замыкающим знаком операции и пустыми скобками (`- {} \\`);
      2. Оставшиеся слагаемые с отступом `&\quad` и знаком операции в начале строки;
      3. Итоговый результат вычисления на отдельной строке (`&= <значение>`).
    - Попытка уместить длинную цепочку вычислений в 2 строки приводит к превышению ширины 580 px и горизонтальному скроллу.
    ```markdown
    <div class="eq">
    <div class="eq-body">

    $$
    \begin{aligned}
    \beta_0 &= 14{,}00 - 55{,}00 \cdot 1{,}2921 - {} \\
    &\quad - 24{,}00 \cdot 0{,}0587 - 43{,}00 \cdot (-0{,}1067) = \\
    &= -53{,}8845
    \end{aligned}
    $$

    </div>
    <div class="eq-num">(18)</div>
    </div>
    ```
  - Системы нормальных матричных уравнений не выстраиваются в одну длинную горизонтальную строку (например, матрица Грама $X^T X$ и вектор $X^T Y$), а располагаются друг под другом вертикально.
  - В глобальных стилях обязательно действует `html, body, .markdown-body { max-width: 100% !important; overflow-x: hidden !important; }`, гарантирующий отсутствие горизонтальной полосы прокрутки страницы.

### 4. Таблицы
- **Подпись таблицы:** размещается **слева над таблицей** шрифтом 14 pt без абзацного отступа:
  ```markdown
  <p class="table-caption">Таблица 1 – Сравнение сходимости численных методов</p>
  ```
- **Запрет формульных разделителей `$` внутри подписей таблиц и рисунков:**
  - Подписи таблиц (`<p class="table-caption">`) и рисунков (`<figcaption>`) оформляются в сырых HTML-тегах. Markdown-парсеры внутри HTML-тегов **не обрабатывают** LaTeX-разделители `$...$`, в результате чего `$k$` отображается как сырой текст с символами доллара.
  - Внутри любых HTML-тегов для переменных, греческих букв и индексов обязательно используются стандартные типографские HTML-теги: `<i>k</i>`, `<i>x</i><sub>1</sub>`, `<b>...</b>`.
- **Строгая посадка по ширине листа:**
  - Таблица обязана подстраиваться под страницу, а не страница растягиваться под таблицу.
  - В стилях задаются `table-layout: fixed; width: 100% !important; max-width: 100% !important; font-size: 13pt;` и перенос слов `word-wrap: break-word;`.
  - При длинных текстовых заголовках в столбцах используются принудительные переносы `<br/>`.
- **Сплошное полужирное начертание шапки:**
  - Если шапка таблицы выделяется полужирным шрифтом, она обязана быть **целиком и равномерно полужирной**.
  - Недопустимо, когда часть текста в заголовке жирная, а часть (например, формульные фрагменты `$N = 108$` или `$R^2$`) рендерится тонким математическим шрифтом KaTeX.
  - В ячейках `<th>` используется обычный текст: `Вся выборка (N = 108)`, `R²`, а в стилях закреплено:
    ```css
    .markdown-body th, body th,
    .markdown-body th *, body th * {
      font-weight: bold !important;
    }
    ```
- **Категорический запрет серого фона и бэктиков (инлайн-кода) по ГОСТ:**
  - В тексте отчетов, ячейках таблиц и списках категорически запрещено использовать Markdown-обратные кавычки (`` `...` ``), так как они рендерятся в серые плашки со скруглением и моноширинным шрифтом, что недопустимо по ГОСТ.
  - Разрешены только полужирный шрифт, курсив и обычный текст.
  - В CSS обязателен сброс свойств `code` (`background: none !important; border: none !important; font-family: inherit !important;`).

### 5. Рисунки, иллюстрации и стандарт построения графиков по ГОСТ

#### 1. Разметка иллюстраций в Markdown
- Рисунок и подпись к нему оформляются строго через контейнер `<figure>`:
  ```html
  <figure align="center">
    <img src="figures/fig2_time_series.png" alt="Динамика переходного процесса">
    <figcaption>Рисунок 1 – Динамика фактических замеров и прогноза модели</figcaption>
  </figure>
  ```
- **Запрет `$...$` в `<figcaption>`:** внутри HTML-тегов подписей рисунков Markdown-парсеры не транслируют LaTeX-разделители. Для переменных и индексов используются исключительно HTML-теги: `<i>k</i>`, `<i>x</i><sub>1</sub>`, `<b>...</b>`.
- **Относительные пути:** изображения помещаются в папку `figures/` и адресуются относительными путями от корня проекта (`figures/fig1_...png`).

#### 2. Академический стандарт графиков в Python (Matplotlib + ГОСТ)
Все научные и инженерные графики для отчетов генерируются на Python через библиотеку Matplotlib в строгом соответствии с полиграфическим стандартом:

1. **Глобальные параметры стиля (`rcParams`):**
   - **Гарнитура шрифта:** `font.family: "Times New Roman"`, математический набор STIX (`mathtext.fontset: "stix"`, `mathtext.default: "regular"`).
   - **Размеры кеглей:**
     - Подписи осей: **18 pt**;
     - Числовые засечки осей: **15 pt**;
     - Текст легенды: **13 pt**;
     - Базовый размер шрифта: **16 pt**.
   - **Толщина и ориентация осей:**
     - Толщина осевых линий: `axes.linewidth = 1.4`;
     - Засечки (тики) направлены **строго внутрь графика**: `xtick.direction: "in"`, `ytick.direction: "in"`;
     - Толщина засечек: `1.2 pt`;
     - Минорные засечки отключены (`minorticks_off()`).
   - **Скрытие лишних рамок:** верхняя (`top`) и правая (`right`) рамки графика скрываются (`spines["top"].set_visible(False)`, `spines["right"].set_visible(False)`).
   - **Параметры сохранения:** `savefig.dpi = 200`, `savefig.bbox: "tight"`, `savefig.pad_inches: 0.12`.

2. **Сетка (Grid):**
   - Контрастная сплошная линия (`ls="-"`), цвет `#6a6a6a`, толщина `1.15 pt`.
   - Слой сетки располагается строго под графиками: `zorder=0`, `ax.set_axisbelow(True)`.

3. **Стрелки на концах осей и динамическое удлинение:**
   - На концах осей вычерчиваются аккуратные черные полигоны `Polygon` фиксированного размера в типографских пунктах (длина 10 pt, полуширина 4 pt, внутренняя выемка 1.5 pt, `clip_on=False`, `zorder=10`).
   - Ось X завершается стрелкой вправо на уровне базовой линии; ось Y — стрелкой вверх.
   - Осевые линии динамически удлиняются на `pad_pt = 12...14 pt` сверх диапазона отображаемых данных, чтобы острие стрелки не наползало на крайний тик данных. Засечки осей фиксируются через `set_xticks`/`set_yticks` до удлинения диапазона.

4. **Расположение подписей осей:**
   - Подпись оси X располагается **справа от стрелки X** (`ha="left"`, `va="center"`, смещение вправо на 4–5 pt).
   - Подпись оси Y располагается **сверху над стрелкой Y** (`ha="center"`, `va="bottom"`, смещение вверх на 4–5 pt).
   - Центрированные подписи осей под графиком или слева от оси **запрещены**.

5. **Отображение чисел на осях и предотвращение коллизий:**
   - Все числа форматируются с **русской запятой** через `FuncFormatter`.
   - **Устранение наложения в углу при ненулевом начале координат:** если нижняя граница графика не равна нулю ($y_{\min} \neq 0$ или $x_{\min} \neq 0$), первая метка по оси X подавляется (`suppress_origin_x=True`). В результате в левом нижнем углу выводится только засечка оси Y, а деления по оси X начинаются со следующего шага.
   - **Пересечение в нуле $(0, 0)$:** если оси пересекаются в начале координат, ноль выводится один раз смещенным в левый нижний угол от перекрестия (`ha="right"`, `va="top"`, смещение `x=-5 pt, y=-3 pt`).
   - **Запрет паразитных пробелов в формулах:** внутри математического режима `$...$` десятичные дроби оформляются либо с экранированием запятой (`$14{,}00$`), либо выносятся в текстовый режим (`$Y^* =$ 14,00 % масс.`), чтобы избежать появления широкого математического пробела после запятой.

6. **Чистота координатного полотна:**
   - **Категорический запрет заголовков `ax.set_title()`:** название графика по ГОСТ помещается исключительно под иллюстрацией в тексте отчета (`<figcaption>`).
   - **Запрет текстовых плашек поверх данных:** надписи типа «ОБУЧЕНИЕ (75%)» или «ТЕСТ (25%)» не наносятся поверх графиков; разбиение выборки задается тонкой вертикальной штриховой линией и дифференциацией стилей линий в легенде.
   - **Легенда:** размещается в свободном углу графика с полупрозрачной подложкой (`framealpha=0.92`) и тонкой темной рамкой (`edgecolor="#444444"`).

#### 3. Эталонный программный шаблон Matplotlib (Python)

```python
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.ticker import FuncFormatter, MultipleLocator
from matplotlib.transforms import Affine2D, ScaledTranslation, offset_copy

plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.size": 16,
    "axes.labelsize": 18,
    "xtick.labelsize": 15,
    "ytick.labelsize": 15,
    "legend.fontsize": 13,
    "axes.unicode_minus": False,
    "mathtext.fontset": "stix",
    "mathtext.default": "regular",
    "axes.linewidth": 1.4,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.top": False,
    "ytick.right": False,
    "xtick.major.width": 1.2,
    "ytick.major.width": 1.2,
    "legend.frameon": True,
    "legend.framealpha": 0.92,
    "legend.edgecolor": "#444444",
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.12,
    "lines.solid_capstyle": "butt",
})

def comma_tick(x, _pos=None):
    if abs(float(x)) < 1e-12:
        return ""
    s = f"{x:g}"
    return s.replace(".", ",")

def setup_gost_axis(ax, xlabel, ylabel, xlim, ylim, x_step, y_step, suppress_origin_x=False):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    y0 = ymin

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_position(("data", y0))
    ax.spines["left"].set_position(("data", xmin))
    ax.tick_params(top=False, right=False)
    ax.xaxis.set_major_locator(MultipleLocator(x_step))
    ax.yaxis.set_major_locator(MultipleLocator(y_step))

    def x_formatter(val, _pos=None):
        if suppress_origin_x and abs(val - xmin) < 1e-6:
            return ""
        if abs(val) < 1e-12 and abs(y0) < 1e-12:
            return ""
        return f"{val:g}".replace(".", ",")

    def y_formatter(val, _pos=None):
        if abs(val) < 1e-12 and abs(y0) < 1e-12:
            return ""
        return f"{val:g}".replace(".", ",")

    ax.xaxis.set_major_formatter(FuncFormatter(x_formatter))
    ax.yaxis.set_major_formatter(FuncFormatter(y_formatter))
    ax.minorticks_off()
    ax.grid(True, which="major", color="#6a6a6a", lw=1.15, ls="-", zorder=0)
    ax.set_axisbelow(True)
    ax.set_autoscale_on(False)

    ax._axis_arrow = {
        "xlabel": xlabel,
        "ylabel": ylabel,
        "y0": y0,
        "suppress_corner": (abs(y0) < 1e-12 and abs(xmin) < 1e-12),
    }

def draw_axis_arrows(ax):
    meta = getattr(ax, "_axis_arrow", None)
    if not meta:
        return
    fig = ax.figure
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    xticks = [t for t in ax.get_xticks() if xmin - 1e-12 <= t <= xmax + 1e-12]
    yticks = [t for t in ax.get_yticks() if ymin - 1e-12 <= t <= ymax + 1e-12]
    bbox = ax.get_position()
    fig_w, fig_h = fig.get_size_inches()
    pad_pt = 14.0
    dx = (xmax - xmin) * (pad_pt / 72.0) / (bbox.width * fig_w)
    dy = (ymax - ymin) * (pad_pt / 72.0) / (bbox.height * fig_h)
    ax.set_xlim(xmin, xmax + dx)
    ax.set_ylim(ymin, ymax + dy)
    ax.set_xticks(xticks)
    ax.set_yticks(yticks)

    xmin, xmax = ax.get_xlim()
    _, ymax = ax.get_ylim()
    y0 = meta["y0"]
    length_pt, half_pt, inset_pt = 10.0, 4.0, 1.5
    pt_to_px = Affine2D().scale(1.0 / 72.0) + fig.dpi_scale_trans

    def arrow_at(origin, verts):
        tr = pt_to_px + ScaledTranslation(origin[0], origin[1], ax.transData)
        poly = Polygon(verts, closed=True, facecolor="black", edgecolor="black", lw=0, clip_on=False, zorder=10)
        poly.set_transform(tr)
        ax.add_patch(poly)

    arrow_at((xmax, y0), [(length_pt, 0.0), (-inset_pt, half_pt), (-inset_pt, -half_pt)])
    arrow_at((xmin, ymax), [(0.0, length_pt), (-half_pt, -inset_pt), (half_pt, -inset_pt)])

    if meta.get("suppress_corner", False):
        ax.text(0.0, 0.0, "0", transform=offset_copy(ax.transData, fig=fig, x=-5.0, y=-3.0, units="points"),
                ha="right", va="top", fontsize=15, clip_on=False, zorder=10)

    ax.text(xmax, y0, meta["xlabel"], transform=offset_copy(ax.transData, fig=fig, x=length_pt + 5.0, y=0.0, units="points"),
            ha="left", va="center", fontsize=18, clip_on=False, zorder=10)
    ax.text(xmin, ymax, meta["ylabel"], transform=offset_copy(ax.transData, fig=fig, x=0.0, y=length_pt + 5.0, units="points"),
            ha="center", va="bottom", fontsize=18, clip_on=False, zorder=10)

def save_plot(fig, out_path):
    for ax in fig.axes:
        draw_axis_arrows(ax)
    fig.savefig(out_path)
    plt.close(fig)
```

---

## 7. Обязательные предварительные уточнения у пользователя

Перед генерацией или оформлением отчета нейросеть **обязана задать пользователю два обязательных вопроса**:

1. **Введение и Заключение:**
   > *«Оформлять ли в документе полноформатные структурные разделы "Введение" и "Заключение" по ГОСТ или ограничиться "Целью работы" и "Выводами"?»*
   *(В ряде учебных и экспресс-отчетов допускается упрощенная структура, поэтому требование всегда согласуется с автором).*
2. **Перечень сокращений и обозначений:**
   > *«Требуется ли включать в начало отчета раздел "Перечень сокращений и обозначений" с таблицей расшифровки терминов или можно обойтись без него?»*
   *(Если в тексте используются аббревиатуры, технические сокращения или иноязычные термины, по ГОСТ они сводятся в таблицу с колонками «Сокращение» и «Расшифровка» сразу после содержания/введения).*

---

## 8. Чек-лист проверки готового `.md` файла

- [ ] Кодировка файла — UTF-8 без BOM, окончания строк — LF (`\n`).
- [ ] Нет лишней строки `# Отчет...` перед блоком стилей.
- [ ] Документ разбит на печатные страницы: 1 страница `.md` = 1 страница А4.
- [ ] Разделители `---` стоят только между страницами.
- [ ] Каждая страница с номерами 2...N заканчивается колонтитулом `<div class="page-footer">N</div>` (14 pt, по центру, без точки).
- [ ] Титульный лист (стр. 1) не имеет номера страницы и оканчивается блоком `Москва, YYYY`.
- [ ] Заголовки нумерованных глав имеют формат `ГЛАВА X<br/>НАЗВАНИЕ ГЛАВЫ` (без точки после номера).
- [ ] Структурные разделы без номеров (ЦЕЛЬ РАБОТЫ, ВВЕДЕНИЕ, ЗАКЛЮЧЕНИЕ, ВЫВОДЫ, СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ) написаны ЗАГЛАВНЫМИ БУКВАМИ.
- [ ] Все заголовки глав и подглав имеют кегль 14 pt полужирный (`font-size: 14pt !important;`).
- [ ] Между заголовком главы и первым подразделом есть краткий вводный обзор (нет висячих заголовков).
- [ ] В содержании пункты не полужирные, без точки после номера главы, отточия выполнены текстовыми точками 14 pt с зазором `margin: 0 0.35em`, а длинные названия глав разбиты на две строки (`.toc-line1` и `.toc-line2`).
- [ ] Номера страниц в содержании строго совпадают с реальными страницами разделов.
- [ ] Все ссылки на файлы внутри репозитория относительные.
- [ ] Все шапки таблиц целиком и монолитно выделены полужирным шрифтом без светлых математических фрагментов.
- [ ] В документе отсутствуют обратные кавычки (`` ` ``) и моноширинные серые плашки инлайн-кода.
- [ ] В подписях к таблицам (`<p class="table-caption">`) и рисункам (`<figcaption>`) переменные оформлены HTML-тегами (`<i>k</i>`), а не знаками доллара (`$k$`).
- [ ] Длинные формулы перенесены на несколько строк через `\begin{aligned}`, в формулах нет горизонтальных полос прокрутки.
- [ ] Страница защищена от горизонтального расползания (`overflow-x: hidden`), таблицы и формулы строго вписаны в ширину листа.
- [ ] Все рисунки оформлены в `<figure>` и имеют подписи вида `<figcaption>Рисунок N – ...</figcaption>` по центру под изображением.
- [ ] Все графики построены по стандарту: шрифт Times New Roman, засечки внутрь, сплошная сетка `#6a6a6a`, стрелки на осях с подписями осей у острий стрелок.
- [ ] На полотне графиков отсутствуют `ax.set_title()` и текстовые плашки; на осях и в легендах используются русские десятичные запятые, угловые коллизии меток устранены.
- [ ] Все таблицы имеют подписи вида `Таблица N – ...` слева над таблицей.
- [ ] Формулы оформлены через $\LaTeX$ без сломанных символов.

