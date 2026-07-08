#!/usr/bin/env python
"""Launch the DC-HMAS demo UI."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent
    app = root / "dc_hmas" / "ui" / "streamlit_app.py"
    if not app.exists():
        raise SystemExit(f"Missing app: {app}")
    print("Starting DC-HMAS Demo...")
    print("Open http://localhost:8501 in your browser")
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app)],
        cwd=str(root),
        check=False,
    )


if __name__ == "__main__":
    main()
