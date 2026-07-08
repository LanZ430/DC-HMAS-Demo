from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from dc_hmas.memory.paths import NovelPaths, write_json

DEFAULT_SESSION_SETTINGS: dict[str, Any] = {
    "enable_image": False,
    "goal_mode": False,
    "guidance_level": "medium",
    "auto_mode_switch": True,
}

_GUIDANCE_LEVELS = frozenset({"weak", "medium", "strong"})


def normalize_session_settings(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Merge persisted session settings with defaults."""
    out = dict(DEFAULT_SESSION_SETTINGS)
    if not isinstance(raw, dict):
        return out
    if isinstance(raw.get("enable_image"), bool):
        out["enable_image"] = raw["enable_image"]
    if isinstance(raw.get("goal_mode"), bool):
        out["goal_mode"] = raw["goal_mode"]
    level = raw.get("guidance_level")
    if isinstance(level, str) and level in _GUIDANCE_LEVELS:
        out["guidance_level"] = level
    if isinstance(raw.get("auto_mode_switch"), bool):
        out["auto_mode_switch"] = raw["auto_mode_switch"]
    return out


def get_session_settings(novel_paths: NovelPaths, session_name: str = "default") -> dict[str, Any]:
    data = load_play_session(session_path(novel_paths, session_name))
    return normalize_session_settings(data.get("session_settings"))


def update_session_settings(
    novel_paths: NovelPaths,
    session_name: str,
    *,
    enable_image: bool | None = None,
    goal_mode: bool | None = None,
    guidance_level: str | None = None,
    auto_mode_switch: bool | None = None,
) -> dict[str, Any]:
    path = session_path(novel_paths, session_name)
    data = load_play_session(path)
    settings = normalize_session_settings(data.get("session_settings"))
    if enable_image is not None:
        settings["enable_image"] = enable_image
    if goal_mode is not None:
        settings["goal_mode"] = goal_mode
    if guidance_level is not None and guidance_level in _GUIDANCE_LEVELS:
        settings["guidance_level"] = guidance_level
    if auto_mode_switch is not None:
        settings["auto_mode_switch"] = auto_mode_switch
    data["session_settings"] = settings
    save_play_session(path, data)
    return settings


def session_dir(novel_paths: NovelPaths) -> Path:
    d = novel_paths.novel_root / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def session_path(novel_paths: NovelPaths, name: str = "default") -> Path:
    return session_dir(novel_paths) / f"play_{name}.json"


def list_sessions(novel_paths: NovelPaths) -> list[dict[str, Any]]:
    """List all play sessions for a novel with metadata."""
    d = session_dir(novel_paths)
    sessions: list[dict[str, Any]] = []
    for f in d.glob("play_*.json"):
        name = f.stem.replace("play_", "")
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            turns = data.get("turns") or []
            sessions.append({
                "name": name,
                "path": str(f),
                "turn_count": len(turns),
                "modified": f.stat().st_mtime,
                "chapter": data.get("chapter"),
                "character": data.get("character"),
            })
        except (OSError, json.JSONDecodeError):
            continue
    sessions.sort(key=lambda x: x.get("modified", 0), reverse=True)
    return sessions


def load_play_session(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"turns": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_play_session(path: Path, data: dict[str, Any]) -> None:
    write_json(path, data)


def create_new_session(novel_paths: NovelPaths, chapter: int, character: str) -> str:
    """Create a new session with timestamp-based name."""
    ts = time.strftime("%Y%m%d_%H%M%S")
    name = f"ch{chapter}_{ts}"
    path = session_path(novel_paths, name)
    data = {
        "turns": [],
        "chapter": chapter,
        "character": character,
        "created_at": time.time(),
        "current_scene_order": 1,  # Track which scene we're on
        "completed_scenes": [],    # List of completed scene_ids
        "session_settings": dict(DEFAULT_SESSION_SETTINGS),
    }
    save_play_session(path, data)
    return name


def advance_scene(novel_paths: NovelPaths, session_name: str, completed_scene_id: str) -> int:
    """Mark a scene as completed and advance to next. Returns new scene order."""
    path = session_path(novel_paths, session_name)
    data = load_play_session(path)
    
    completed = data.setdefault("completed_scenes", [])
    if completed_scene_id not in completed:
        completed.append(completed_scene_id)
    
    current = data.get("current_scene_order", 1)
    data["current_scene_order"] = current + 1
    
    save_play_session(path, data)
    return data["current_scene_order"]


def get_scene_progress(novel_paths: NovelPaths, session_name: str) -> tuple[int, list[str]]:
    """Get current scene order and list of completed scene_ids."""
    path = session_path(novel_paths, session_name)
    data = load_play_session(path)
    return (
        data.get("current_scene_order", 1),
        data.get("completed_scenes", []),
    )


def clear_session(novel_paths: NovelPaths, name: str) -> bool:
    """Clear/reset a session."""
    path = session_path(novel_paths, name)
    if path.exists():
        data = load_play_session(path)
        data["turns"] = []
        data["cleared_at"] = time.time()
        save_play_session(path, data)
        return True
    return False


def delete_session(novel_paths: NovelPaths, name: str) -> bool:
    """Delete a session file."""
    path = session_path(novel_paths, name)
    if path.exists():
        path.unlink()
        return True
    return False


def append_turn(
    novel_paths: NovelPaths,
    *,
    role: str,
    content: str,
    meta: dict[str, Any] | None = None,
    session_name: str = "default",
) -> None:
    path = session_path(novel_paths, session_name)
    data = load_play_session(path)
    turns = data.setdefault("turns", [])
    turn: dict[str, Any] = {"role": role, "content": content, "ts": time.time()}
    if meta:
        turn["meta"] = meta
    turns.append(turn)
    save_play_session(path, data)
