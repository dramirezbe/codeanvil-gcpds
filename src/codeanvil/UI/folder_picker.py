"""Native directory dialog helper; run in its own interpreter, never a worker Tk root."""

import json
import sys
from pathlib import Path


def main() -> int:
    try:
        import tkinter as tk
        from tkinter import filedialog

        window = tk.Tk()
        window.withdraw()
        try:
            selected = filedialog.askdirectory(
                parent=window,
                title="Choose a CodeAnvil project folder",
                initialdir=str(Path(sys.argv[1]).expanduser()) if len(sys.argv) > 1 else None,
                mustexist=True,
            )
        finally:
            window.destroy()
        print(json.dumps({"path": selected or None}))
        return 0
    except Exception:
        # Display/import errors are expected on a headless host. Do not expose
        # environment paths in the browser: it offers a manual-path fallback.
        print(json.dumps({"error": "Native folder selection is unavailable. Enter the folder path instead."}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
