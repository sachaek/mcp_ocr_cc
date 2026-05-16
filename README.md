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

## Для Claude Code Users

После установки инструменты `ocr_image` и `ocr_screen` доступны как нативные MCP-инструменты.

### Быстрый старт (1 команда)

```bash
pip install -e ".[all]" && claude mcp add --transport stdio --scope user ocr-tool python -m ocr_tool.mcp_server
```

### Как это работает

В проекте есть `.mcp.json` — Claude Code авто-обнаруживает его и подключает MCP-сервер.
После `pip install -e .` пакет импортируется из любого места, и `python -m ocr_tool.mcp_server` запускает сервер.

**Что получаете:**

| Инструмент | Что делает |
|-----------|-----------|
| `ocr_image(path, langs, preprocess, layout, output_format)` | Распознаёт текст из файла |
| `ocr_screen(monitor, langs, preprocess, layout, output_format)` | Скриншот + OCR |

Никаких подтверждений, никаких разрешений — работают как встроенные.

---

## Как это устроено

1. **OCR** — [easyocr](https://github.com/JaidedAI/EasyOCR) (PyTorch + CPU, без GPU)
2. **Preprocessing** — OpenCV: пороговая обработка, выравнивание, шумоподавление, повышение контраста и резкости
3. **Layout** — геометрический анализ bounding box'ов: определение порядка чтения, колонок, заголовков, таблиц
4. **Никаких LLM, детектронов, трансформеров** — всё легковесное, ставится в `pip install`

---

## Сравнение: было → стало

| Было (v1) | Стало (v2) |
|-----------|-----------|
| `python ocr_screenshot.py file.png` | `ocr-tool file.png` (или `python -m ocr_tool`) |
| Только plain text | `--output-format json / csv / html` |
| Нет preprocessing | `--preprocess clahe,deskew,upscale,...` |
| Нет layout | `--layout` — колонки, заголовки, таблицы |
| Одно изображение | `--batch ./dir/ --recursive` |
| Только файлы | `--screen` — захват экрана |
| Зависимости: easyocr | easyocr + опционально mss |

---

## License

MIT
