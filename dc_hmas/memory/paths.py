from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class NovelPaths:
    """On-disk layout under data_dir / novel_id."""

    novel_root: Path

    @property
    def chapters_dir(self) -> Path:
        return self.novel_root / "chapters"

    @property
    def analyses_dir(self) -> Path:
        return self.novel_root / "analyses"

    @property
    def metadata_path(self) -> Path:
        return self.novel_root / "document_info.json"

    @property
    def status_path(self) -> Path:
        return self.novel_root / "preprocessing_status.json"

    @property
    def world_memory_path(self) -> Path:
        return self.novel_root / "world_memory.json"

    @property
    def plot_memory_path(self) -> Path:
        return self.novel_root / "plot_memory.json"

    @property
    def style_memory_path(self) -> Path:
        return self.novel_root / "style_memory.json"

    @property
    def control_standard_path(self) -> Path:
        return self.novel_root / "control_standard.json"

    @property
    def characters_dir(self) -> Path:
        return self.novel_root / "characters"

    @property
    def character_archive_path(self) -> Path:
        """Main character archive file with all character profiles."""
        return self.characters_dir / "character_archive.json"

    @property
    def scripts_dir(self) -> Path:
        return self.novel_root / "scripts"
    
    def character_profile_path(self, character_name: str) -> Path:
        """Individual character profile file."""
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in character_name)
        return self.characters_dir / f"{safe_name}.json"

    def ensure_dirs(self) -> None:
        for p in (
            self.chapters_dir,
            self.analyses_dir,
            self.characters_dir,
            self.scripts_dir,
        ):
            p.mkdir(parents=True, exist_ok=True)

    def analysis_path(self, chapter_num: int) -> Path:
        return self.analyses_dir / f"chapter_{chapter_num:03d}.json"

    def script_path(self, chapter_num: int) -> Path:
        return self.scripts_dir / f"chapter_{chapter_num:03d}.json"


def new_novel_id(language: str, title_stub: str, chapter_count: int) -> str:
    slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in title_stub)[:40]
    short = uuid.uuid4().hex[:8]
    return f"{language}-{slug}_{chapter_count}_{short}"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
