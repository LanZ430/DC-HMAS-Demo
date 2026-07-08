"""Character status management for interactive narrative."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from openai import OpenAI

from dc_hmas.chapter_splitter import parse_json_loose
from dc_hmas.llm import chat_json
from dc_hmas.memory.paths import NovelPaths, read_json, write_json
from dc_hmas.prompts import get_prompt

logger = logging.getLogger(__name__)


def status_path(paths: NovelPaths, session_name: str) -> Path:
    """Get path for character status file."""
    d = paths.novel_root / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"status_{session_name}.json"


def load_character_status(paths: NovelPaths, session_name: str) -> dict[str, Any] | None:
    """Load character status from file."""
    sp = status_path(paths, session_name)
    if not sp.exists():
        return None
    try:
        return read_json(sp)
    except (OSError, json.JSONDecodeError):
        return None


def save_character_status(paths: NovelPaths, session_name: str, status: dict[str, Any]) -> None:
    """Save character status to file."""
    sp = status_path(paths, session_name)
    write_json(sp, status)


def initialize_character_status(
    client: OpenAI,
    model: str,
    *,
    character_name: str,
    world_memory: dict[str, Any],
    chapter_analysis: dict[str, Any],
    opening_narrative: str = "",
    output_lang: str = "zh",
) -> dict[str, Any]:
    """Initialize character status based ONLY on the opening narrative.

    The key constraint: only include attributes, items, skills that are
    **explicitly mentioned or clearly implied** in the opening narrative.
    Chapter analysis is used only for genre/tone context, never for
    future-knowledge about items or events that haven't appeared yet.
    """
    quick = world_memory.get("quick_scan", {})
    genre_tags = quick.get("genre_tags", [])

    world_summary = quick.get("premise_one_line", "")
    if world_memory.get("infinite_flow", {}).get("framing_world"):
        world_summary += f"\n{world_memory['infinite_flow']['framing_world']}"

    system = get_prompt("character_status", "system", output_lang)
    user = get_prompt(
        "character_status", "user", output_lang,
        genre_tags=genre_tags,
        world_summary=world_summary[:2000],
        character_name=character_name,
        opening_narrative=opening_narrative[:4000],
    )

    raw = chat_json(client, model, system, user, temperature=0.3, max_tokens=1500)
    try:
        status = parse_json_loose(raw)
    except Exception:
        logger.exception("character status init failed")
        status = _default_status(character_name, genre_tags)

    status.setdefault("character_name", character_name)
    return status


def update_character_status(
    client: OpenAI,
    model: str,
    *,
    current_status: dict[str, Any],
    user_action: str,
    narrative_result: str,
    memory_updates: list[str],
    output_lang: str = "zh",
) -> dict[str, Any]:
    """Update character status based on action and result."""
    system = get_prompt("character_status_update", "system", output_lang)
    user = get_prompt(
        "character_status_update", "user", output_lang,
        current_status=json.dumps(current_status, ensure_ascii=False, indent=2)[:3000],
        user_action=user_action[:500],
        narrative_result=narrative_result[:1500],
        memory_updates=json.dumps(memory_updates, ensure_ascii=False),
    )
    
    raw = chat_json(client, model, system, user, temperature=0.25, max_tokens=1000)
    try:
        updates = parse_json_loose(raw)
    except Exception:
        logger.exception("character status update failed")
        return current_status
    
    # Apply updates
    new_status = dict(current_status)
    
    # Update attributes
    if updates.get("attributes"):
        attrs = new_status.setdefault("attributes", {})
        attrs.update(updates["attributes"])
    
    # Update status effects
    if "status_effects" in updates:
        new_status["status_effects"] = updates["status_effects"]
    
    # Update inventory
    inventory = new_status.setdefault("inventory", [])
    if updates.get("inventory_add"):
        for item in updates["inventory_add"]:
            existing = next((i for i in inventory if i.get("name") == item.get("name")), None)
            if existing:
                existing["quantity"] = existing.get("quantity", 1) + item.get("quantity", 1)
            else:
                inventory.append(item)
    if updates.get("inventory_remove"):
        inventory[:] = [i for i in inventory if i.get("name") not in updates["inventory_remove"]]
    
    # Update skills
    if updates.get("skills_add"):
        skills = new_status.setdefault("skills", [])
        for skill in updates["skills_add"]:
            if skill not in skills:
                skills.append(skill)
    
    # Update relationships
    if updates.get("relationships_update"):
        rels = new_status.setdefault("relationships", [])
        for rel in updates["relationships_update"]:
            existing = next((r for r in rels if r.get("name") == rel.get("name")), None)
            if existing:
                existing["attitude"] = rel.get("attitude", existing.get("attitude"))
            else:
                rels.append(rel)
    
    # Update notes
    if updates.get("notes"):
        new_status["last_update_notes"] = updates["notes"]
    
    return new_status


def _default_status(character_name: str, genre_tags: list[str]) -> dict[str, Any]:
    """Generate default status based on genre."""
    is_infinite_flow = any("无限流" in t or "infinite" in t.lower() for t in genre_tags)
    is_cultivation = any("修仙" in t or "cultivation" in t.lower() for t in genre_tags)
    
    if is_infinite_flow:
        return {
            "character_name": character_name,
            "attributes": {
                "health": 100,
                "spirit": 100,
                "sanity": 100,
                "points": 0,
            },
            "status_effects": ["正常"],
            "inventory": [],
            "skills": [],
            "relationships": [],
            "notes": "初始状态",
        }
    elif is_cultivation:
        return {
            "character_name": character_name,
            "attributes": {
                "cultivation": "凡人",
                "qi": 0,
                "health": 100,
                "spirit_stones": 0,
            },
            "status_effects": ["正常"],
            "inventory": [],
            "skills": [],
            "relationships": [],
            "notes": "初始状态",
        }
    else:
        return {
            "character_name": character_name,
            "attributes": {
                "health": 100,
                "energy": 100,
                "money": 0,
            },
            "status_effects": ["正常"],
            "inventory": [],
            "skills": [],
            "relationships": [],
            "notes": "初始状态",
        }
