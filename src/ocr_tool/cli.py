"""CLI entry point with argparse."""
from __future__ import annotations

import argparse
import logging
import sys

from . import __version__
from .formatters import FORMATTERS
from .preprocess import STEPS as PREPROCESS_STEPS


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="ocr-tool",
        description="Extract text from images and screenshots using OCR. "
                    "Supports preprocessing, layout analysis, and multiple output formats.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  ocr-tool file.png\n"
            "  ocr-tool file.png --preprocess deskew,clahe\n"
            "  ocr-tool file.png --layout --output-format json\n"
            "  ocr-tool --batch ./screenshots/ --output results.json\n"
            "  ocr-tool --screen\n"
        ),
    )

    # Input
    parser.add_argument("path", nargs="?", default=None,
                        help="Path to image file")
    parser.add_argument("--screen", action="store_true",
                        help="Capture screenshot instead of reading a file")
    parser.add_argument("--monitor", type=int, default=1,
                        help="Monitor number for screen capture (default: 1)")
    parser.add_argument("--batch", metavar="DIR", default=None,
                        help="Process all images in a directory")
    parser.add_argument("--recursive", action="store_true",
                        help="Process subdirectories when using --batch")

    # OCR
    parser.add_argument("--langs", default="ru+en",
                        help="OCR languages, separated by + (default: ru+en)")

    # Preprocessing
    all_steps = ", ".join(sorted(PREPROCESS_STEPS))
    parser.add_argument("--preprocess", default=None,
                        help=f"Preprocessing chain: comma-separated steps. Available: {all_steps}")
    parser.add_argument("--save-preprocessed", metavar="FILE", default=None,
                        help="Save preprocessed image to file (debugging)")

    # Layout
    parser.add_argument("--layout", action="store_true",
                        help="Analyze document layout (columns, headings, tables)")

    # Output
    fmt_names = ", ".join(sorted(FORMATTERS))
    parser.add_argument("--output-format", default="plain", choices=sorted(FORMATTERS),
                        help=f"Output format (default: plain). Available: {fmt_names}")
    parser.add_argument("--output", "-o", metavar="FILE", default=None,
                        help="Write output to file instead of stdout")

    # Other
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable logging")
    parser.add_argument("--version", action="store_true",
                        help="Show version and exit")

    return parser


def main() -> None:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if args.version:
        print(f"ocr-tool v{__version__}")
        sys.exit(0)

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.CRITICAL + 1
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
    )

    # Parse languages
    langs = args.langs.split("+") if args.langs else ["ru", "en"]

    # Parse preprocessing steps
    preprocess_steps = None
    if args.preprocess:
        preprocess_steps = [s.strip() for s in args.preprocess.split(",") if s.strip()]

    # Validate input source
    has_path = args.path is not None
    has_screen = args.screen
    has_batch = args.batch is not None
    sources = sum([has_path, has_screen, has_batch])

    if sources == 0:
        parser.print_help()
        print("\nError: provide an image path, --screen, or --batch", file=sys.stderr)
        sys.exit(1)
    elif sources > 1:
        print("Error: use only one of: image path, --screen, or --batch", file=sys.stderr)
        sys.exit(1)

    # Suppress easyocr/warnings noise unless verbose
    if not args.verbose:
        import warnings
        warnings.filterwarnings("ignore")

    from .pipeline import run_batch, run_single

    try:
        if has_batch:
            results = run_batch(
                args.batch,
                langs=langs,
                preprocess_steps=preprocess_steps,
                do_layout=args.layout,
                output_format=args.output_format,
                recursive=args.recursive,
            )
            output = _format_batch_output(results, args.output_format)
        else:
            output = run_single(
                args.path,
                langs=langs,
                preprocess_steps=preprocess_steps,
                do_layout=args.layout,
                output_format=args.output_format,
                save_preprocessed=args.save_preprocessed,
            )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        sys.stdout.write(output)
        if output and not output.endswith("\n"):
            sys.stdout.write("\n")


def _format_batch_output(results: dict[str, str], fmt: str) -> str:
    """Format batch results as a single block."""
    if fmt == "json":
        import json
        return json.dumps(results, ensure_ascii=False, indent=2)

    lines: list[str] = []
    for path, text in results.items():
        lines.append(f"=== {path} ===")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)
