from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dc_hmas.memory.paths import NovelPaths


def discover_novels(data_dir: Path) -> list[dict[str, Any]]:
    """Folders under data_dir that contain document_info.json."""
    if not data_dir.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for child in data_dir.iterdir():
        if not child.is_dir():
            continue
        meta = child / "document_info.json"
        if not meta.exists():
            continue
        try:
            doc = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        doc["_path"] = str(child)
        doc["_novel_id"] = doc.get("document_id", child.name)
        doc["_root"] = str(child.resolve())
        rows.append(doc)
    rows.sort(key=lambda r: r.get("_path", ""))
    return rows


def load_novel_paths(data_dir: Path, novel_id: str) -> NovelPaths | None:
    p = data_dir / novel_id
    if not (p / "document_info.json").exists():
        return None
    return NovelPaths(p)


def novel_paths_from_row(row: dict[str, Any]) -> NovelPaths | None:
    root = row.get("_root")
    if not root:
        return None
    p = Path(root)
    if not (p / "document_info.json").exists():
        return None
    return NovelPaths(p)
