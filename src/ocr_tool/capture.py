"""Screen capture support (optional, requires mss)."""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np


def capture_screen(monitor: int = 1) -> "np.ndarray":
    """Capture a monitor and return as RGB numpy array.

    Args:
        monitor: Monitor number (1-based). Use 0 for full virtual screen.
    """
    try:
        import mss
        import numpy as np
    except ImportError:
        print("Error: --screen requires mss. Install with: pip install ocr-tool[screen]",
              file=sys.stderr)
        sys.exit(1)

    with mss.mss() as sct:
        mon = sct.monitors[monitor]
        sct_img = sct.grab(mon)
        img = np.array(sct_img)
        return img[:, :, :3]  # BGRA → RGB


def list_monitors() -> list[dict]:
    """Return info about available monitors."""
    try:
        import mss
    except ImportError:
        return []
    with mss.mss() as sct:
        return [
            {"num": i, "width": m["width"], "height": m["height"]}
            for i, m in enumerate(sct.monitors)
        ]
