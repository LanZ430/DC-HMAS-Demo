"""Sync dc_hmas + smoke tests from sibling DC-HMAS dev tree into this demo folder."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT.parent / "DC-HMAS"
SRC_PKG = SRC_ROOT / "dc_hmas"
DST_PKG = ROOT / "dc_hmas"
SRC_TESTS = SRC_ROOT / "tests"
DST_TESTS = ROOT / "tests"

TEST_FILES = [
    "conftest.py",
    "test_catalog.py",
    "test_text_encoding.py",
    "test_scene_engine.py",
    "test_goal_panel.py",
    "test_sprint1_session.py",
]


def main() -> None:
    if not SRC_PKG.is_dir():
        raise SystemExit(f"Missing dev package: {SRC_PKG}")
    if DST_PKG.exists():
        shutil.rmtree(DST_PKG)
    shutil.copytree(
        SRC_PKG,
        DST_PKG,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    DST_TESTS.mkdir(exist_ok=True)
    for name in TEST_FILES:
        src = SRC_TESTS / name
        if src.exists():
            shutil.copy2(src, DST_TESTS / name)
    print(f"Synced {SRC_PKG} -> {DST_PKG}")
    print("Re-apply demo patches: config.demo_mode, streamlit_app agent panel gate")


if __name__ == "__main__":
    main()
