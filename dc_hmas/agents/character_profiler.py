"""
Character Profiler Agent
Creates comprehensive character profiles from chapter analyses.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from openai import OpenAI

from dc_hmas.memory.paths import NovelPaths, write_json, read_json
from dc_hmas.prompts.templates import get_prompt

logger = logging.getLogger(__name__)


def _aggregate_character_data(paths: NovelPaths, max_chapters: int = 50) -> dict[str, list[dict]]:
    """
    Aggregate character appearances across all analyzed chapters.
    Returns: { character_name: [chapter_data_1, chapter_data_2, ...] }
    """
    aggregated: dict[str, list[dict]] = {}
    
    for i in range(1, max_chapters + 1):
        analysis_path = paths.analysis_path(i)
        if not analysis_path.exists():
            continue
        
        try:
            analysis = read_json(analysis_path)
            characters = analysis.get("characters") or []
            
            for char in characters:
                if not isinstance(char, dict) or not char.get("name"):
                    continue
                
                name = char["name"]
                char_data = {
                    "chapter": i,
                    **char,
                }
                
                if name not in aggregated:
                    aggregated[name] = []
                aggregated[name].append(char_data)
                
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Error reading analysis for chapter {i}: {e}")
    
    return aggregated


def build_character_archive(
    client: OpenAI,
    model: str,
    paths: NovelPaths,
    title: str,
    world_summary: str,
    output_lang: str = "zh",
) -> dict[str, Any]:
    """
    Build comprehensive character archive from all chapter analyses.
    
    Args:
        client: OpenAI client
        model: Model name
        paths: Novel paths
        title: Novel title
        world_summary: World memory summary
        output_lang: Output language (zh or en)
    
    Returns:
        Character archive with detailed profiles
    """
    aggregated = _aggregate_character_data(paths)
    
    if not aggregated:
        logger.warning("No character data found in analyses")
        return {"characters": []}
    
    character_data_str = json.dumps(aggregated, ensure_ascii=False, indent=2)
    if len(character_data_str) > 15000:
        character_data_str = character_data_str[:15000] + "\n... (truncated)"
    
    system_prompt = get_prompt("character_profiler", "system", output_lang)
    user_prompt = get_prompt(
        "character_profiler", "user", output_lang,
        title=title,
        world_summary=world_summary[:3000] if world_summary else "",
        character_data=character_data_str,
    )
    
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    
    content = resp.choices[0].message.content or "{}"
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        logger.error(f"Character profiler returned invalid JSON: {content[:500]}")
        result = {"characters": []}
    
    paths.characters_dir.mkdir(parents=True, exist_ok=True)
    write_json(paths.character_archive_path, result)
    
    for char in result.get("characters", []):
        if char.get("name"):
            char_path = paths.character_profile_path(char["name"])
            write_json(char_path, char)
    
    logger.info(f"Built character archive with {len(result.get('characters', []))} profiles")
    return result


def get_character_profile(paths: NovelPaths, character_name: str) -> dict[str, Any] | None:
    """
    Get a specific character's profile.
    
    Args:
        paths: Novel paths
        character_name: Character name to look up
    
    Returns:
        Character profile dict or None if not found
    """
    char_path = paths.character_profile_path(character_name)
    if char_path.exists():
        try:
            return read_json(char_path)
        except (OSError, json.JSONDecodeError):
            pass
    
    archive_path = paths.character_archive_path
    if archive_path.exists():
        try:
            archive = read_json(archive_path)
            for char in archive.get("characters", []):
                if char.get("name") == character_name:
                    return char
        except (OSError, json.JSONDecodeError):
            pass
    
    return None


def load_character_archive(paths: NovelPaths) -> dict[str, Any]:
    """Load the full character archive."""
    if paths.character_archive_path.exists():
        try:
            return read_json(paths.character_archive_path)
        except (OSError, json.JSONDecodeError):
            pass
    return {"characters": []}
