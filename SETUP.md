# ocr-tool — Bootstrap for Claude Code

Скопируй и вставь **весь текст ниже** в Claude Code из папки этого проекта.
Claude сам выполнит установку и настройку.

---

```
Я только что склонировал проект ocr-tool. Сделай следующее по порядку:

1. Установи пакет со всеми опциональными зависимостями:
   pip install -e ".[all]"

2. Зарегистрируй MCP-сервер глобально (чтобы работал из любой папки):
   claude mcp add --transport stdio --scope user ocr-tool python -m ocr_tool.mcp_server

3. Проверь что MCP-сервер отвечает:
   Запусти `python -m ocr_tool.mcp_server` и отправь ему запрос tools/list через echo/printf

4. Запусти тесты:
   python -m pytest tests/ -v

5. Сделай тестовый OCR на любом изображении в папке (если есть) или создай тестовое:
   python -c "import cv2, numpy as np; img = np.ones((200,200,3), dtype=np.uint8)*255; cv2.putText(img, 'Hello OCR', (20,100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2); cv2.imwrite('test.png', img)"
   ocr-tool test.png
```

После этого в Claude Code появятся инструменты:
- `ocr_image` — распознать текст из файла
- `ocr_screen` — скриншот + OCR (требует mss)

## Ручная установка

```bash
git clone <repo-url> && cd ocr-tool
pip install -e ".[all]"
claude mcp add --transport stdio --scope user ocr-tool python -m ocr_tool.mcp_server
```
