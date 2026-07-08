"""Character agency, interaction necessity, and scene progression helpers."""
from __future__ import annotations

import re
from typing import Any

_PASSIVE_INPUT_KEYWORDS = (
    "sleep", "just sleep", "keep sleeping", "remain sleep", "continue sleeping",
    "rest", "wait", "do nothing", "stay asleep", "nap",
    "silence", "keep silence", "stay silent", "just keep silence", "remain silent",
    "observe", "watch", "as usual", "like usual", "do what i usually",
    "睡觉", "继续睡", "睡", "等待", "什么都不做", "继续睡觉", "接着睡",
    "沉默", "保持沉默", "继续沉默", "观察", "像往常一样", "平常", "照旧",
)

_NECESSITY_LEVEL = {"none": 0, "weak": 1, "medium": 2, "strong": 3}


def ordered_player_scenes(chapter_script: dict[str, Any]) -> list[dict[str, Any]]:
    ps = chapter_script.get("player_script") if isinstance(chapter_script, dict) else None
    if not isinstance(ps, dict):
        return []
    raw = ps.get("scenes") or []
    if not isinstance(raw, list):
        return []
    scenes = [s for s in raw if isinstance(s, dict)]
    scenes.sort(key=lambda s: int(s.get("order", 0)) or 0)
    return scenes


def scene_by_order(ordered: list[dict[str, Any]], order: int) -> dict[str, Any] | None:
    for s in ordered:
        if int(s.get("order", 0) or 0) == order:
            return s
    return None


_SYSTEM_HINT_KEYWORDS = (
    "系统", "任务", "经营", "营收", "考核", "quest", "mission", "system", "objective",
)


def _is_system_related(text: str) -> bool:
    lower = text.lower()
    return any(k in text or k in lower for k in _SYSTEM_HINT_KEYWORDS)


def _parse_chapter_span(span: str) -> tuple[int, int] | None:
    if not span or not isinstance(span, str):
        return None
    m = re.match(r"(\d+)\s*[-–—]\s*(\d+)", span.strip())
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def _current_arc_for_chapter(
    world: dict[str, Any] | None,
    chapter_num: int,
) -> dict[str, Any] | None:
    if not world:
        return None
    arcs = (world.get("infinite_flow") or {}).get("arcs") or []
    for arc in arcs:
        if not isinstance(arc, dict):
            continue
        span = _parse_chapter_span(str(arc.get("chapter_span_estimate") or ""))
        if span and span[0] <= chapter_num <= span[1]:
            return arc
    return arcs[0] if arcs and isinstance(arcs[0], dict) else None


def _dedupe_objectives(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        key = (item.get("title") or "") + "|" + (item.get("description") or "")
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def resolve_goal_panel_items(
    *,
    scene: dict[str, Any] | None,
    guidance_level: str = "medium",
    output_lang: str = "zh",
    char_status: dict[str, Any] | None = None,
    world: dict[str, Any] | None = None,
    chapter_num: int = 1,
) -> list[dict[str, Any]]:
    """Build read-only goal panel items: system quests + scene orientation."""
    if guidance_level == "weak":
        return []

    items: list[dict[str, Any]] = []

    if char_status:
        for i, effect in enumerate(char_status.get("status_effects") or []):
            label = str(effect).strip()
            if not label or not _is_system_related(label):
                continue
            items.append({
                "id": f"sys_status_{i}",
                "type": "quest",
                "title": label,
                "description": "",
                "status": "active",
                "visibility": "player",
                "source": "system_status",
                "spoiler_level": "none",
            })
        for j, quest in enumerate(char_status.get("quests") or []):
            if not isinstance(quest, dict):
                continue
            name = quest.get("name") or quest.get("title") or ""
            if not name:
                continue
            items.append({
                "id": f"char_quest_{j}",
                "type": "quest",
                "title": name,
                "description": (quest.get("description") or quest.get("detail") or "").strip(),
                "status": quest.get("status", "active"),
                "visibility": "player",
                "source": "character_quest",
                "spoiler_level": "none",
            })

    tags = ((world or {}).get("quick_scan") or {}).get("genre_tags") or []
    profile = (world or {}).get("interaction_profile") or {}
    has_system = (
        "系统" in tags
        or profile.get("has_explicit_system")
        or profile.get("primary_mode") == "task_oriented"
    )
    if has_system and world:
        arc = _current_arc_for_chapter(world, chapter_num)
        if arc:
            arc_title = arc.get("title") or ""
            premise = (arc.get("premise") or "").strip()
            if arc_title:
                items.append({
                    "id": f"arc_{arc.get('arc_id', chapter_num)}",
                    "type": "quest",
                    "title": arc_title if output_lang == "zh" else arc_title,
                    "description": premise,
                    "status": "active",
                    "visibility": "player",
                    "source": "story_arc",
                    "spoiler_level": "low",
                })
            for k, sig in enumerate(arc.get("entry_signals") or []):
                sig_text = str(sig).strip()
                if not sig_text or not _is_system_related(sig_text):
                    continue
                items.append({
                    "id": f"arc_sig_{chapter_num}_{k}",
                    "type": "quest",
                    "title": sig_text,
                    "description": "",
                    "status": "active",
                    "visibility": "player",
                    "source": "arc_signal",
                    "spoiler_level": "none",
                })

    items.extend(resolve_scene_objectives(scene, guidance_level=guidance_level, output_lang=output_lang))
    return _dedupe_objectives(items)


def resolve_scene_objectives(
    scene: dict[str, Any] | None,
    *,
    guidance_level: str = "medium",
    output_lang: str = "zh",
) -> list[dict[str, Any]]:
    """Build read-only objectives for the goal panel (display only, not action menu)."""
    if guidance_level == "weak":
        return []

    if not scene:
        return []

    raw = scene.get("objectives")
    if isinstance(raw, list) and raw:
        visible: list[dict[str, Any]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            if item.get("visibility") == "dm_only":
                continue
            status = item.get("status", "active")
            if status not in ("active", "completed", "failed", "locked"):
                status = "active"
            visible.append({**item, "status": status})
        return visible

    hooks = (scene.get("interaction_hooks") or "").strip()
    decision = (scene.get("decision_prompt") or "").strip()
    description = decision or hooks
    if not description:
        return []

    node_type = scene.get("node_type", "plot")
    if output_lang == "en":
        if node_type == "decision":
            title = "Decision point"
        elif node_type == "passive":
            title = "Observe"
        else:
            title = "Story beat"
        fallback_type = "beat" if node_type == "plot" else "guidance"
    else:
        if node_type == "decision":
            title = "抉择时刻"
        elif node_type == "passive":
            title = "观察"
        else:
            title = "情节点"
        fallback_type = "beat" if node_type == "plot" else "guidance"

    return [
        {
            "id": f"{scene.get('scene_id', 'scene')}_orientation",
            "type": fallback_type,
            "title": title,
            "description": description,
            "status": "active",
            "visibility": "player",
            "source": "interaction_hooks",
            "spoiler_level": "none",
        }
    ]


def is_passive_user_input(user_input: str) -> bool:
    t = user_input.lower().strip()
    return any(k in t for k in _PASSIVE_INPUT_KEYWORDS)


def resolve_interaction_necessity(scene: dict[str, Any] | None) -> str:
    """Return strong | medium | weak | none for how much player input a scene needs."""
    if not scene:
        return "medium"

    inn = scene.get("interaction_necessity")
    if isinstance(inn, str) and inn in _NECESSITY_LEVEL:
        return inn

    nt = scene.get("node_type", "plot")
    if nt == "passive":
        return "none"
    if nt == "decision":
        prompt = f"{scene.get('decision_prompt', '')} {scene.get('interaction_hooks', '')}".lower()
        observational = (
            "observe", "watch", "remain", "wait", "listen", "stay", "alert",
            "gauge", "note the", "prepare to note", "no direct action",
            "观察", "等待", "保持", "留意", "无需", "不需要",
        )
        if any(w in prompt for w in observational):
            return "weak"
        return "strong"
    return "medium"


def character_mentioned_in_scene(scene: dict[str, Any], character: str) -> bool:
    text = (scene.get("player_facing_text") or "").lower()
    name = character.lower().strip()
    if not name:
        return False
    if name in text:
        return True
    parts = name.split()
    if parts and parts[-1] in text:
        return True
    return False


def resolve_character_agency(
    scene: dict[str, Any] | None,
    character: str,
    adaptation: dict[str, Any] | None,
) -> str:
    """Return none | low | full for the player character in a scene."""
    if not scene:
        return "full"

    scene_id = str(scene.get("scene_id", ""))
    for sa in (adaptation or {}).get("scene_adaptations") or []:
        if isinstance(sa, dict) and sa.get("scene_id") == scene_id and sa.get("agency"):
            return str(sa["agency"])

    agency_map = scene.get("character_agency") or {}
    if isinstance(agency_map, dict) and character in agency_map:
        return str(agency_map[character])

    if scene.get("node_type") == "passive":
        return "none"

    present = scene.get("characters_present") or []
    if isinstance(present, list) and present:
        if character not in present:
            return "none"
        return "full"

    text = (scene.get("player_facing_text") or "").lower()
    if character_mentioned_in_scene(scene, character):
        return "full"

    infant_cues = (
        "cradles", "bundle", "blankets", "in his arms", "in her arms",
        "sleeping infant", "swaddled", "wrapped in",
    )
    if any(cue in text for cue in infant_cues):
        return "low"

    return "none"


def first_agency_scene_order(
    ordered: list[dict[str, Any]],
    character: str,
    adaptation: dict[str, Any] | None,
) -> int:
    if adaptation and adaptation.get("first_agency_scene_order"):
        try:
            return int(adaptation["first_agency_scene_order"])
        except (TypeError, ValueError):
            pass

    for s in ordered:
        agency = resolve_character_agency(s, character, adaptation)
        if agency in ("low", "full"):
            return int(s.get("order", 1) or 1)

    return int(ordered[-1].get("order", 1) or 1) if ordered else 1


def first_strong_interaction_scene_order(ordered: list[dict[str, Any]]) -> int:
    """First scene where interaction_necessity is strong."""
    for s in ordered:
        if resolve_interaction_necessity(s) == "strong":
            return int(s.get("order", 1) or 1)
    return int(ordered[-1].get("order", 1) or 1) if ordered else 1


def next_pause_scene_order(
    ordered: list[dict[str, Any]],
    after_order: int,
    min_necessity: str = "medium",
) -> int:
    """First scene at or after which Host should pause for meaningful interaction."""
    min_level = _NECESSITY_LEVEL.get(min_necessity, 2)
    max_order = max(int(s.get("order", 1) or 1) for s in ordered) if ordered else after_order

    for s in ordered:
        order = int(s.get("order", 0) or 0)
        if order <= after_order:
            continue
        if _NECESSITY_LEVEL.get(resolve_interaction_necessity(s), 2) >= min_level:
            return order

    return max_order


def compute_scene_advance_target(
    *,
    current_order: int,
    ordered_scenes: list[dict[str, Any]],
    character: str,
    adaptation: dict[str, Any] | None,
    user_input: str,
    model_advanced_to: int | None,
) -> int:
    """Resolve scene order after a turn; fast-forward through low-necessity segments."""
    if not ordered_scenes:
        return current_order

    max_order = max(int(s.get("order", 1) or 1) for s in ordered_scenes)
    target = current_order
    if isinstance(model_advanced_to, int) and model_advanced_to > current_order:
        target = model_advanced_to

    current = scene_by_order(ordered_scenes, current_order)
    agency = resolve_character_agency(current, character, adaptation)
    necessity = resolve_interaction_necessity(current)
    passive_input = is_passive_user_input(user_input)

    # Interaction necessity drives pacing
    if necessity == "none":
        target = max(target, next_pause_scene_order(ordered_scenes, current_order, "weak"))
    elif necessity == "weak":
        target = max(target, current_order + 1)
        # One turn in weak scenes is enough — skip to next medium/strong beat
        target = max(target, next_pause_scene_order(ordered_scenes, current_order, "medium"))
    elif necessity == "medium":
        target = max(target, current_order + 1)
    # strong: respect model target; don't force multi-scene skip

    # Character agency still applies
    if agency == "none":
        target = max(target, current_order + 1)
        first_agency = first_agency_scene_order(ordered_scenes, character, adaptation)
        target = max(target, first_agency if first_agency > current_order else current_order + 1)
    elif agency == "low" and passive_input:
        target = max(target, current_order + 1)
        target = max(target, next_pause_scene_order(ordered_scenes, current_order, "medium"))

    return min(max(target, 1), max_order)
