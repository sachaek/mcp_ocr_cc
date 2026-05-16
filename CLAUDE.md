# OCR Screenshot Tool

CLI-утилита для извлечения текста из изображений и скриншотов.  
Поддерживает предобработку (deskew, CLAHE, denoise, binarization), анализ структуры документа (колонки, заголовки, таблицы), батчевую обработку и несколько форматов вывода.

## Быстрый старт

```bash
pip install -e .
python -m ocr_tool <путь_к_изображению> --langs ru+en
```

Или через CLI-команду (после установки):
```bash
ocr-tool screenshot.png
```

## Возможности

- **OCR**: easyocr, CPU, языковая цепочка через `--langs`
- **Preprocessing**: `--preprocess deskew,clahe,denoise,binarize,sharpen,upscale,gray,otsu,bilateral`
- **Layout analysis**: `--layout` — чтение по порядку, колонки, заголовки, параграфы, таблицы
- **Batch**: `--batch ./dir/ --recursive`
- **Screen capture**: `--screen` (требует `pip install ocr-tool[screen]`)
- **Форматы**: plain, json, csv, html
- **Сохранение**: `--output result.json`

## Примеры

```bash
ocr-tool dark_photo.jpg --preprocess clahe,denoise,upscale
ocr-tool document.png --layout --output-format json
ocr-tool --batch scans/ --preprocess deskew --output results.json
ocr-tool --screen --output clipboard.txt
```

## Структура проекта

```
src/ocr_tool/
├── __init__.py       # версия
├── __main__.py       # python -m ocr_tool
├── cli.py            # argparse
├── ocr.py            # easyocr wrapper + кэш Reader
├── preprocess.py     # binarize, deskew, denoise, CLAHE, upscale, sharpen
├── layout.py         # reading order, columns, paragraphs, tables
├── formatters.py     # plain / json / csv / html
├── capture.py        # MSS screen capture
└── pipeline.py       # chain stages together
tests/
├── conftest.py
├── test_preprocess.py
├── test_layout.py
└── test_formatters.py
```

## Соглашения

- Python 3.9+, `pyproject.toml` (setuptools)
- Нет тестов — `pytest tests/`
- Кодировка UTF-8
- Без LLM, без тяжёлых моделей — только easyocr + OpenCV
