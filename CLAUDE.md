# ocr-tool

OCR tool with image preprocessing, document layout analysis, and MCP server.

## First-time setup

When you open this project, check if ocr-tool is installed:

```bash
python -c "from ocr_tool import __version__; print(__version__)"
```

If not installed, ask the user for permission and run:

```bash
pip install -e ".[all]"
```

After installation, the MCP server defined in `.mcp.json` will start automatically.

## MCP tools

This project provides MCP tools via `.mcp.json` (auto-discovered by Claude Code):

| Tool | Description |
|------|-------------|
| `ocr_image(path, langs, preprocess, layout, output_format)` | Extract text from an image file |
| `ocr_screen(monitor, langs, preprocess, layout, output_format)` | Capture screenshot and run OCR |

Parameters:
- `langs` — language codes separated by `+` (default: `ru+en`)
- `preprocess` — comma-separated steps: `deskew`, `clahe`, `denoise`, `binarize`, `sharpen`, `upscale`, `gray`, `otsu`, `bilateral`
- `layout` — analyze document structure (columns, headings, tables)
- `output_format` — `plain`, `json`, `csv`, or `html`

## Critical rule

If you fail to read an image (model doesn't support vision, file read error, or any other reason), **use the `ocr_image` MCP tool** instead. These tools work with any model since they run OCR locally.

## Project structure

```
src/ocr_tool/
├── __init__.py       # version
├── __main__.py       # python -m ocr_tool
├── cli.py            # argparse CLI
├── mcp_server.py     # MCP server (ocr_image, ocr_screen)
├── ocr.py            # easyocr wrapper
├── preprocess.py     # image preprocessing (OpenCV)
├── layout.py         # document layout analysis
├── formatters.py     # output formatters
├── capture.py        # screen capture (optional)
└── pipeline.py       # pipeline orchestrator
tests/
├── test_preprocess.py
├── test_layout.py
└── test_formatters.py
```

## Dependencies

- Required: `easyocr` (installed via `pip install -e .`)
- Optional: `mss` for screen capture (`pip install -e ".[screen]"`)
- All dependencies are free, open-source, no GPU required.
