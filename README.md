# OCR Screenshot Tool

Извлекает текст из изображений, скриншотов и документов.  
Работает полностью офлайн, без GPU, без LLM и тяжелых моделей.

```bash
pip install -e .
ocr-tool screenshot.png
```

---

## Установка

```bash
git clone <repo-url> && cd ocr-tool
pip install -e .
```

Дополнительные возможности:
```bash
pip install -e ".[screen]"   # захват экрана (--screen)
pip install -e ".[test]"     # запуск тестов
```

---

## Базовое использование

### 1. Распознать текст с картинки

```bash
ocr-tool screenshot.png
```
Выведет распознанный текст в консоль.

По умолчанию — русский + английский. Чтобы сменить язык:
```bash
ocr-tool receipt.jpg --langs en
ocr-tool document.jpg --langs ru+en+fr
```

### 2. Сохранить результат в файл

```bash
ocr-tool photo.jpg --output result.txt
```

### 3. Вывести в JSON (с координатами и уверенностью)

```bash
ocr-tool scan.png --output-format json
```

```json
{
  "results": [
    {
      "text": "Hello OCR",
      "confidence": 0.9983,
      "bbox": [[19, 73], [181, 73], [181, 109], [19, 109]]
    }
  ]
}
```

---

## Preprocessing (улучшение качества)

Если изображение тёмное, размытое, перекошенное или мелкий текст — добавьте цепочку预处理:

```bash
# Тёмное фото — повысить контраст и убрать шум
ocr-tool dark.jpg --preprocess clahe,denoise

# Перекошенный скан — выровнять
ocr-tool scan.jpg --preprocess deskew

# Мелкий текст — увеличить
ocr-tool small-text.png --preprocess upscale

# Всё вместе
ocr-tool bad-image.png --preprocess deskew,clahe,denoise,sharpen
```

**Все шаги preprocessing (без ML, только OpenCV):**

| Шаг | Что делает |
|-----|-----------|
| `gray` | Чёрно-белое |
| `binarize` | Адаптивная бинаризация (для неровного освещения) |
| `otsu` | Бинаризация методом Отсу |
| `deskew` | Выравнивание перекошенного текста |
| `clahe` | Повышение локального контраста |
| `denoise` | Удаление шума |
| `bilateral` | Фильтр с сохранением краёв |
| `sharpen` | Повышение резкости |
| `upscale` | Увеличение в 2 раза (Lanczos) |

Их можно комбинировать через запятую в любом порядке.

---

## Layout analysis (структура документа)

Если нужно не просто извлечь текст, а понять структуру — где заголовки, где колонки, есть ли таблицы:

```bash
ocr-tool document.png --layout --output-format json
```

В JSON добавится секция `layout`:
```json
{
  "layout": {
    "columns": 2,
    "blocks": [
      { "type": "heading", "text": "Отчёт за 2025" },
      { "type": "paragraph", "text": "В первом квартале..." },
      { "type": "paragraph", "text": "Во втором квартале..." }
    ],
    "tables": [
      { "cells": [["Показатель", "Q1", "Q2"], ["Выручка", "100", "150"]] }
    ]
  }
}
```

Флаг `--layout` работает без интернета и дополнительных моделей — только геометрия bounding box'ов.

---

## Batch-обработка

```bash
# Все картинки в папке
ocr-tool --batch ./scans/

# Рекурсивно по подпапкам
ocr-tool --batch ./documents/ --recursive

# С preprocessing и сохранением
ocr-tool --batch ./photos/ --preprocess clahe,deskew --output results.json
```

---

## Захват экрана

```bash
# Требуется: pip install -e ".[screen]"

# Скриншот всего монитора → OCR
ocr-tool --screen

# Указать монитор (если их несколько)
ocr-tool --screen --monitor 2
```

---

## Форматы вывода

| Формат | Когда использовать |
|--------|------------------|
| `plain` | Просто текст в консоль (по умолчанию) |
| `json` | Нужны координаты, уверенность, layout |
| `csv` | Импорт в Excel / Google Sheets |
| `html` | Сохранить как веб-страницу с разметкой |

---

## MCP Server для Claude Code

Проект содержит `.mcp.json` — Claude Code **автоматически** подхватывает его при открытии папки. Никакой ручной регистрации.

### Установка

```bash
git clone https://github.com/sachaek/mcp_ocr_cc.git && cd mcp_ocr_cc
pip install -e ".[all]"
```

Открой папку в Claude Code — и инструменты готовы.

### MCP-инструменты

| Инструмент | Параметры |
|-----------|-----------|
| `ocr_image` | `path` (путь к файлу), `langs` (ru+en), `preprocess` (deskew,clahe,...), `layout` (true/false), `output_format` (plain/json/csv/html) |
| `ocr_screen` | `monitor` (номер), `langs`, `preprocess`, `layout`, `output_format` |

**Работает на любой модели** — OCR запускается локально на CPU, интернет не нужен.

### Что Claude сам сделает

Благодаря `CLAUDE.md` при первом открытии Claude:
1. Проверит, установлен ли пакет
2. Если нет — предложит `pip install -e .`
3. Будет использовать `ocr_image` когда не сможет прочитать картинку напрямую

### Как это устроено

- `.mcp.json` — Claude Code авто-обнаруживает MCP-сервер
- `CLAUDE.md` — инструкции для Claude (проверка установки, fallback на OCR)
- `SETUP.md` — промт для самого первого запуска (скопируй и вставь в Claude)

---

## Как это устроено

1. **OCR** — [easyocr](https://github.com/JaidedAI/EasyOCR) (PyTorch + CPU, без GPU)
2. **Preprocessing** — OpenCV: пороговая обработка, выравнивание, шумоподавление, повышение контраста и резкости
3. **Layout** — геометрический анализ bounding box'ов: определение порядка чтения, колонок, заголовков, таблиц
4. **Никаких LLM, детектронов, трансформеров** — всё легковесное, ставится в `pip install`

## License

MIT
