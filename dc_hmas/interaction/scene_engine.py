from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from openai import OpenAI

from dc_hmas.chapter_splitter import load_chapter, parse_json_loose, truncate_chapter_for_llm
from dc_hmas.llm import chat_json
from dc_hmas.memory.paths import NovelPaths, read_json
from dc_hmas.prompts import get_prompt
from dc_hmas.agents.character_profiler import get_character_profile, load_character_archive
from dc_hmas.memory.paths import write_json
from dc_hmas.interaction import agency as scene_agency

logger = logging.getLogger(__name__)


def generate_perspective_adaptation(
    client: OpenAI,
    model: str,
    paths: NovelPaths,
    chapter_num: int,
    character_name: str,
    output_lang: str = "zh",
) -> dict[str, Any]:
    """
    Generate a perspective adaptation layer for a specific character.
    This helps the Host transform third-person scripts into first-person narrative.
    
    Returns the adaptation dict and saves it to disk.
    """
    # Load character profile
    char_profile = get_character_profile(paths, character_name)
    if not char_profile:
        # Fall back to basic info from chapter analysis
        analysis = _safe_read_json(paths.analysis_path(chapter_num))
        for c in analysis.get("characters") or []:
            if isinstance(c, dict) and c.get("name") == character_name:
                char_profile = c
                break
    
    # Load chapter script
    chapter_script = _safe_read_json(paths.script_path(chapter_num))
    
    if not chapter_script:
        logger.warning(f"No script found for chapter {chapter_num}")
        return {}
    
    # Generate adaptation layer
    system_prompt = get_prompt("perspective_adapter", "system", output_lang)
    user_prompt = get_prompt(
        "perspective_adapter", "user", output_lang,
        character_name=character_name,
        character_profile=json.dumps(char_profile, ensure_ascii=False)[:3000] if char_profile else "{}",
        chapter_script=json.dumps(chapter_script, ensure_ascii=False)[:8000],
    )
    
    raw = chat_json(client, model, system_prompt, user_prompt, temperature=0.4, max_tokens=2000)
    
    try:
        adaptation = parse_json_loose(raw)
    except Exception:
        logger.exception("Failed to parse perspective adaptation")
        adaptation = {
            "character_name": character_name,
            "first_agency_scene_order": 1,
            "pov_notes": "",
            "scene_adaptations": [],
            "voice_guidelines": {},
        }
    
    # Save to disk for reuse
    adaptation_path = paths.characters_dir / f"adaptation_{character_name}_ch{chapter_num:03d}.json"
    paths.characters_dir.mkdir(parents=True, exist_ok=True)
    write_json(adaptation_path, adaptation)
    
    return adaptation


def load_perspective_adaptation(
    paths: NovelPaths,
    chapter_num: int,
    character_name: str,
) -> dict[str, Any] | None:
    """Load a previously generated perspective adaptation if it exists."""
    adaptation_path = paths.characters_dir / f"adaptation_{character_name}_ch{chapter_num:03d}.json"
    if adaptation_path.exists():
        try:
            return read_json(adaptation_path)
        except (OSError, json.JSONDecodeError):
            pass
    return None


def _safe_read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = read_json(path)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError, TypeError):
        return {}


def load_play_context(
    paths: NovelPaths,
    chapter_num: int,
    player_character: str,
    player_char_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    world = _safe_read_json(paths.world_memory_path)
    style = _safe_read_json(paths.style_memory_path)
    ctrl = _safe_read_json(paths.control_standard_path)
    analysis = _safe_read_json(paths.analysis_path(chapter_num))
    chapter_script = _safe_read_json(paths.script_path(chapter_num))
    ch_text = ""
    try:
        ch_text = load_chapter(paths.chapters_dir, chapter_num)
    except OSError:
        pass
    
    # Load detailed character profile from archive if available
    char_profile = get_character_profile(paths, player_character)
    
    # Extract character info from analysis if not provided
    char_info = player_char_info or {}
    if not char_info and analysis:
        chars = analysis.get("characters") or []
        for c in chars:
            if isinstance(c, dict) and c.get("name") == player_character:
                char_info = c
                break
    
    # Merge profile and chapter-specific info (profile has more detail)
    if char_profile:
        merged_char_info = {**char_info}
        # Add profile details that chapter analysis might not have
        if char_profile.get("personality"):
            merged_char_info["personality_hints"] = char_profile["personality"].get("core_traits", [])
            merged_char_info["motivations"] = char_profile["personality"].get("motivations", [])
            merged_char_info["fears"] = char_profile["personality"].get("fears", [])
        if char_profile.get("speaking_style"):
            ss = char_profile["speaking_style"]
            merged_char_info["speaking_style"] = ss.get("tone", "")
            merged_char_info["speaking_quirks"] = ss.get("quirks", [])
            merged_char_info["example_lines"] = ss.get("example_lines", [])
        if char_profile.get("roleplay_tips"):
            merged_char_info["roleplay_tips"] = char_profile["roleplay_tips"]
        char_info = merged_char_info
    
    # Get other NPCs in this chapter (excluding player character), enriched with archive data
    npcs = []
    character_archive = load_character_archive(paths)
    archive_by_name = {c.get("name"): c for c in character_archive.get("characters", []) if c.get("name")}
    
    if analysis:
        for c in analysis.get("characters") or []:
            if isinstance(c, dict) and c.get("name") != player_character:
                npc_data = {**c}
                # Enrich with archive data if available
                if c.get("name") in archive_by_name:
                    archived = archive_by_name[c["name"]]
                    if archived.get("personality"):
                        npc_data["personality_hints"] = archived["personality"].get("core_traits", [])
                    if archived.get("speaking_style"):
                        npc_data["speaking_style"] = archived["speaking_style"].get("tone", "")
                npcs.append(npc_data)
    
    # Load perspective adaptation if exists
    perspective_adaptation = load_perspective_adaptation(paths, chapter_num, player_character)
    
    return {
        "world": world,
        "style": style,
        "control": ctrl,
        "analysis": analysis,
        "chapter_script": chapter_script,
        "chapter_excerpt": truncate_chapter_for_llm(ch_text),
        "chapter_num": chapter_num,
        "player_character": player_character,
        "player_char_info": char_info,
        "player_char_profile": char_profile,  # Full profile for reference
        "chapter_npcs": npcs,
        "perspective_adaptation": perspective_adaptation,  # Character POV adaptation layer
    }


def _ordered_player_scenes(chapter_script: dict[str, Any]) -> list[dict[str, Any]]:
    return scene_agency.ordered_player_scenes(chapter_script)


def _format_agency_guidance(
    *,
    ordered: list[dict[str, Any]],
    current_scene_order: int,
    character: str,
    adaptation: dict[str, Any] | None,
    user_input: str = "",
    output_lang: str = "zh",
) -> str:
    current = scene_agency.scene_by_order(ordered, current_scene_order)
    agency = scene_agency.resolve_character_agency(current, character, adaptation)
    necessity = scene_agency.resolve_interaction_necessity(current)
    first_agency = scene_agency.first_agency_scene_order(ordered, character, adaptation)
    next_pause = scene_agency.next_pause_scene_order(ordered, current_scene_order, "medium")
    passive_input = scene_agency.is_passive_user_input(user_input)

    lines: list[str] = []
    if output_lang == "en":
        lines.append(f"【INTERACTION NECESSITY: {necessity.upper()} (scene {current_scene_order})】")
        if current and current.get("interaction_rationale"):
            lines.append(f"Rationale: {current['interaction_rationale'][:200]}")
        if necessity == "none":
            lines.append(
                "⚠️ NO interaction needed. Write a time-skip montage and advance to the next story beat. "
                "Do NOT ask what the player wants to do."
            )
        elif necessity == "weak":
            lines.append(
                "⚠️ WEAK interaction — routine/observational only. "
                "One short paragraph, then advance to the next medium/strong beat. "
                "Do NOT offer multiple choice prompts or linger on details."
            )
        elif necessity == "medium":
            lines.append(
                "Medium interaction — player may react briefly, but plot advances regardless. "
                "One turn then move on."
            )
        else:
            lines.append(
                "STRONG interaction — pause here. Build tension and offer a real decision."
            )

        lines.append(f"【CHARACTER AGENCY: {agency.upper()}】")
        if agency == "none":
            lines.append(
                f"⚠️ {character} CANNOT act. Compress and advance toward scene {first_agency}+."
            )
            if passive_input:
                lines.append("Player chose passive/wait — FAST-FORWARD.")
        elif agency == "low":
            lines.append(f"{character} has LIMITED agency — sensory only, no fake action choices.")
            if passive_input:
                lines.append("Player chose wait — advance toward scene " + str(next_pause) + ".")
        if necessity in ("none", "weak") and passive_input:
            lines.append(f"Target after this turn: scene {next_pause} or later.")
    else:
        lines.append(f"【交互必要性：{necessity}（第 {current_scene_order} 场景）】")
        if current and current.get("interaction_rationale"):
            lines.append(f"原因：{current['interaction_rationale'][:200]}")
        if necessity == "none":
            lines.append(
                "⚠️ 无需交互。写时间流转蒙太奇并推进至下一情节点。"
                "不要询问玩家想做什么。"
            )
        elif necessity == "weak":
            lines.append(
                "⚠️ 弱交互 — 日常/旁观段落。"
                "一段简短叙述后必须推进至下一个中/强交互情节点。"
                "不要提供多项选择或停留细节。"
            )
        elif necessity == "medium":
            lines.append("中等交互 — 玩家可简短反应，但剧情无论如何都会推进。一轮后前进。")
        else:
            lines.append("强交互 — 在此暂停，营造张力并提供真实抉择。")

        lines.append(f"【角色行动力：{agency}】")
        if agency == "none":
            lines.append(f"⚠️ {character} 无法行动。压缩叙述，推进至第 {first_agency} 场景或之后。")
            if passive_input:
                lines.append("玩家选择等待 — 必须快进。")
        elif agency == "low":
            lines.append(f"{character} 行动力有限 — 仅感知，不要伪造行动选项。")
            if passive_input:
                lines.append(f"玩家选择等待 — 推进至第 {next_pause} 场景或之后。")
        if necessity in ("none", "weak") and passive_input:
            lines.append(f"本回合结束后目标场景：第 {next_pause} 场景或更后。")

    if current and current.get("node_type") == "passive":
        label = "Current node is PASSIVE" if output_lang == "en" else "当前节点为 passive"
        lines.append(label + (" — transit/time-skip." if output_lang == "en" else " — 过渡/时间流转。"))

    # Per-scene skip guidance from adaptation
    if current and adaptation:
        scene_id = current.get("scene_id")
        for sa in adaptation.get("scene_adaptations") or []:
            if isinstance(sa, dict) and sa.get("scene_id") == scene_id and sa.get("skip_guidance"):
                label = "Skip guidance" if output_lang == "en" else "快进指引"
                lines.append(f"{label}: {sa['skip_guidance']}")
                break

    return "\n".join(lines)


def _format_guidance_level_guidance(guidance_level: str, output_lang: str) -> str:
    level = guidance_level if guidance_level in ("weak", "medium", "strong") else "medium"
    if output_lang == "en":
        if level == "weak":
            return (
                "【GUIDANCE LEVEL: WEAK】\n"
                "Keep interaction_hint minimal or empty. Do not spell out objectives. "
                "Let the player discover freely."
            )
        if level == "strong":
            return (
                "【GUIDANCE LEVEL: STRONG】\n"
                "Provide a clear interaction_hint with explicit orientation, e.g. "
                "'You may…' / 'Consider…'. Help the player see what matters without forcing a choice."
            )
        return (
            "【GUIDANCE LEVEL: MEDIUM】\n"
            "Provide a concise interaction_hint from scene hooks — open-ended, not a menu."
        )
    if level == "weak":
        return (
            "【引导强度：弱】\n"
            "interaction_hint 尽量简短或留空，不要明确列出目标，让玩家自由探索。"
        )
    if level == "strong":
        return (
            "【引导强度：强】\n"
            "interaction_hint 应清晰给出探索导向，例如「你可以…」「留意…」，"
            "帮助玩家理解当前可关注什么，但不要变成选项菜单。"
        )
    return (
        "【引导强度：中】\n"
        "interaction_hint 基于场景 hooks 给出简洁、开放式的引导。"
    )


def _opening_script_payload_for_character(
    chapter_script: dict[str, Any],
    character: str,
    adaptation: dict[str, Any] | None,
    output_lang: str = "zh",
) -> tuple[dict[str, Any], int, str]:
    """Build opening script slice and starting scene order for the chosen character."""
    ordered = _ordered_player_scenes(chapter_script)
    if not ordered:
        return {}, 1, ""

    first_agency = scene_agency.first_agency_scene_order(ordered, character, adaptation)
    first_pause = scene_agency.next_pause_scene_order(ordered, 0, "medium")
    start_order = 1
    scene_one = scene_agency.scene_by_order(ordered, 1)
    agency_at_one = scene_agency.resolve_character_agency(scene_one, character, adaptation)
    necessity_at_one = scene_agency.resolve_interaction_necessity(scene_one)
    stop_at = max(first_agency, first_pause)

    if (agency_at_one == "none" or necessity_at_one in ("none", "weak")) and stop_at > 1:
        montage_scenes = [s for s in ordered if int(s.get("order", 0) or 0) <= stop_at]
        rule = (
            f"Opening montage: compress scenes 1–{stop_at} (skip weak/none interaction beats). "
            f"Stop at first medium/strong story beat where {character} can participate."
            if output_lang == "en"
            else f"开场蒙太奇：压缩第1–{stop_at}场景（跳过弱/无交互段落），"
            f"在 {character} 可参与的第一个中/强情节点处停下。"
        )
        return {
            "opening_mode": "montage",
            "scenes_to_cover": montage_scenes,
            "stop_at_scene_order": stop_at,
            "rule": rule,
        }, stop_at, rule

    first = ordered[0]
    rule = (
        "Cover only scene 1; do not perform later scenes yet."
        if output_lang == "en"
        else "仅覆盖第1场景；不要演出后续场景。"
    )
    return {
        "opening_mode": "single",
        "scene": first,
        "rule": rule,
    }, start_order, rule


def _opening_player_script_payload(
    chapter_script: dict[str, Any], output_lang: str = "zh"
) -> dict[str, Any]:
    """只取玩家本第一幕给「开场」用，避免模型把整章合成一段。"""
    ordered = _ordered_player_scenes(chapter_script)
    if not ordered:
        return {}
    first = ordered[0]
    rule_text = (
        "叙事只覆盖 scene 这一段；禁止预判或演出后续场景；后续留到玩家回合再推进。"
        if output_lang == "zh"
        else "Narrative covers only this scene; do not anticipate or perform subsequent scenes; leave the rest for the player's turn."
    )
    return {
        "use_for_opening_only": True,
        "scene": first,
        "total_scenes_in_chapter": len(ordered),
        "rule": rule_text,
    }


def _scene_system_intro(output_lang: str = "zh") -> str:
    return get_prompt("host", "system", output_lang)


def _format_adaptation_context(
    adaptation: dict[str, Any] | None,
    current_scene_order: int,
    output_lang: str = "zh",
) -> str:
    """Format perspective adaptation for inclusion in prompt."""
    if not adaptation:
        return ""
    
    lines = []
    
    if output_lang == "en":
        lines.append("【CHARACTER PERSPECTIVE ADAPTATION LAYER】")
        if adaptation.get("pov_notes"):
            lines.append(f"POV Notes: {adaptation['pov_notes']}")
        
        # Find adaptation for current scene
        scene_adapt = None
        for sa in adaptation.get("scene_adaptations") or []:
            if sa.get("scene_id", "").endswith(f"_sc{current_scene_order:02d}"):
                scene_adapt = sa
                break
        
        if scene_adapt:
            lines.append(f"\nFor current scene ({scene_adapt.get('scene_id', '')}):")
            if scene_adapt.get("character_role_here"):
                lines.append(f"  Your position: {scene_adapt['character_role_here']}")
            if scene_adapt.get("sensory_focus"):
                lines.append(f"  Focus on: {', '.join(scene_adapt['sensory_focus'][:4])}")
            if scene_adapt.get("inner_thoughts"):
                lines.append(f"  Inner thoughts: {scene_adapt['inner_thoughts'][:200]}")
        
        vg = adaptation.get("voice_guidelines") or {}
        if vg:
            lines.append("\nVoice guidelines:")
            if vg.get("first_person_markers"):
                lines.append(f"  Typical phrases: {', '.join(vg['first_person_markers'][:5])}")
            if vg.get("things_character_would_notice"):
                lines.append(f"  Would notice: {', '.join(vg['things_character_would_notice'][:4])}")
    else:
        lines.append("【角色视角适配层】")
        if adaptation.get("pov_notes"):
            lines.append(f"视角要点：{adaptation['pov_notes']}")
        
        # Find adaptation for current scene
        scene_adapt = None
        for sa in adaptation.get("scene_adaptations") or []:
            if sa.get("scene_id", "").endswith(f"_sc{current_scene_order:02d}"):
                scene_adapt = sa
                break
        
        if scene_adapt:
            lines.append(f"\n当前场景 ({scene_adapt.get('scene_id', '')}) 适配：")
            if scene_adapt.get("character_role_here"):
                lines.append(f"  你的位置：{scene_adapt['character_role_here']}")
            if scene_adapt.get("sensory_focus"):
                lines.append(f"  关注的感官：{'、'.join(scene_adapt['sensory_focus'][:4])}")
            if scene_adapt.get("inner_thoughts"):
                lines.append(f"  内心独白：{scene_adapt['inner_thoughts'][:200]}")
        
        vg = adaptation.get("voice_guidelines") or {}
        if vg:
            lines.append("\n语言风格指南：")
            if vg.get("first_person_markers"):
                lines.append(f"  典型用词：{'、'.join(vg['first_person_markers'][:5])}")
            if vg.get("things_character_would_notice"):
                lines.append(f"  会注意的事物：{'、'.join(vg['things_character_would_notice'][:4])}")
    
    return "\n".join(lines)


def _format_character_context(
    player_char: str,
    char_info: dict[str, Any],
    npcs: list[dict[str, Any]],
    output_lang: str = "zh",
) -> str:
    """Format character info for inclusion in prompt."""
    lines = []
    
    # Player character info
    if output_lang == "en":
        lines.append(f"【YOUR CHARACTER: {player_char}】")
        if char_info.get("role_in_chapter"):
            lines.append(f"Role in this chapter: {char_info['role_in_chapter']}")
        if char_info.get("personality_hints"):
            lines.append(f"Personality: {', '.join(char_info['personality_hints'])}")
        if char_info.get("motivations"):
            lines.append(f"Motivations: {', '.join(char_info['motivations'])}")
        if char_info.get("speaking_style"):
            lines.append(f"Speaking style: {char_info['speaking_style']}")
        if char_info.get("speaking_quirks"):
            lines.append(f"Speaking quirks: {', '.join(char_info['speaking_quirks'])}")
        if char_info.get("example_lines"):
            lines.append("Example dialogue lines:")
            for ex in char_info["example_lines"][:3]:
                lines.append(f'  - "{ex}"')
        if char_info.get("roleplay_tips"):
            lines.append("Roleplay tips:")
            for tip in char_info["roleplay_tips"][:4]:
                lines.append(f"  - {tip}")
        lines.append("")
        lines.append("IMPORTANT: You MUST write from this character's perspective, matching their personality and voice exactly.")
        lines.append("")
        
        # NPCs
        if npcs:
            lines.append("【OTHER CHARACTERS IN THIS CHAPTER】")
            for npc in npcs[:6]:
                npc_line = f"- {npc.get('name', 'Unknown')}"
                if npc.get("role_in_chapter"):
                    npc_line += f": {npc['role_in_chapter'][:60]}"
                if npc.get("personality_hints"):
                    npc_line += f" (traits: {', '.join(npc['personality_hints'][:3])})"
                lines.append(npc_line)
    else:
        lines.append(f"【你扮演的角色：{player_char}】")
        if char_info.get("role_in_chapter"):
            lines.append(f"本章角色定位：{char_info['role_in_chapter']}")
        if char_info.get("personality_hints"):
            lines.append(f"性格特点：{'、'.join(char_info['personality_hints'])}")
        if char_info.get("motivations"):
            lines.append(f"行为动机：{'、'.join(char_info['motivations'])}")
        if char_info.get("speaking_style"):
            lines.append(f"说话风格：{char_info['speaking_style']}")
        if char_info.get("speaking_quirks"):
            lines.append(f"说话习惯：{'、'.join(char_info['speaking_quirks'])}")
        if char_info.get("example_lines"):
            lines.append("典型台词示例：")
            for ex in char_info["example_lines"][:3]:
                lines.append(f'  - 「{ex}」')
        if char_info.get("roleplay_tips"):
            lines.append("扮演建议：")
            for tip in char_info["roleplay_tips"][:4]:
                lines.append(f"  - {tip}")
        lines.append("")
        lines.append("重要：你必须以该角色的视角来写作，严格贴合其性格和语言风格。")
        lines.append("")
        
        # NPCs
        if npcs:
            lines.append("【本章其他角色】")
            for npc in npcs[:6]:
                npc_line = f"- {npc.get('name', '未知')}"
                if npc.get("role_in_chapter"):
                    npc_line += f"：{npc['role_in_chapter'][:60]}"
                if npc.get("personality_hints"):
                    npc_line += f"（特点：{'、'.join(npc['personality_hints'][:3])}）"
                lines.append(npc_line)
    
    return "\n".join(lines)


def generate_opening_scene(
    client: OpenAI,
    model: str,
    ctx: dict[str, Any],
    output_lang: str = "zh",
    guidance_level: str = "medium",
) -> dict[str, Any]:
    sys_p = _scene_system_intro(output_lang)
    script = ctx.get("chapter_script") or {}
    ordered = _ordered_player_scenes(script if isinstance(script, dict) else {})
    adaptation = ctx.get("perspective_adaptation")

    opening_payload, start_scene_order, opening_rule = _opening_script_payload_for_character(
        script if isinstance(script, dict) else {},
        ctx["player_character"],
        adaptation,
        output_lang,
    )
    if opening_payload:
        script_for_model = json.dumps(opening_payload, ensure_ascii=False)[:7000]
    else:
        script_for_model = json.dumps(script, ensure_ascii=False)[:8000]

    agency_guidance = _format_agency_guidance(
        ordered=ordered,
        current_scene_order=start_scene_order,
        character=ctx["player_character"],
        adaptation=adaptation,
        output_lang=output_lang,
    )
    guidance_block = _format_guidance_level_guidance(guidance_level, output_lang)

    # Build character context
    char_context = _format_character_context(
        ctx["player_character"],
        ctx.get("player_char_info") or {},
        ctx.get("chapter_npcs") or [],
        output_lang,
    )
    
    # Build adaptation context (if available)
    adaptation_context = _format_adaptation_context(
        adaptation,
        start_scene_order,
        output_lang,
    )

    if output_lang == "en":
        user_p = f"""{char_context}

{adaptation_context}

{agency_guidance}

{guidance_block}

Current chapter: Chapter {ctx["chapter_num"]}
Opening rule: {opening_rule}

World setting and arcs (JSON summary):
{json.dumps(ctx["world"], ensure_ascii=False)[:6000]}

Chapter analysis:
{json.dumps(ctx["analysis"], ensure_ascii=False)[:4000]}

Player script for opening (THIRD-PERSON — convert to first-person from {ctx["player_character"]}'s POV):
{script_for_model}

Style anchors:
{json.dumps(ctx["style"], ensure_ascii=False)[:1500]}

Field control summary:
{json.dumps(ctx["control"], ensure_ascii=False)[:1500]}

Task: Write the opening narrative.
- If opening_mode=montage: compress passive/none-agency scenes into 2-3 short paragraphs, then stop at first_agency scene
- If opening_mode=single: cover only the first scene
- Convert THIRD-PERSON script to FIRST-PERSON from "{ctx["player_character"]}"'s perspective
- Do NOT offer choices the character cannot perform (agency=none/low)
Output JSON fields:
- narrative: string (English, first-person)
- interaction_hint: string (English; if agency=none/low, suggest waiting/sensing only, not fake actions)
- image_prompt_zh: string
- image_prompt_en: string
- field: object with safety: pass|warn, deviation_level: 0-5, note: string
- memory_updates: string[]
- scene_advanced_to: int (scene order reached; montage openings should set to first_agency scene order)

IMPORTANT: All narrative and interaction_hint must be in English. Write AS the character.
"""
    else:
        user_p = f"""{char_context}

{adaptation_context}

{agency_guidance}

{guidance_block}

当前章节: 第 {ctx["chapter_num"]} 章
开场规则: {opening_rule}

世界观与弧（JSON 摘要）:
{json.dumps(ctx["world"], ensure_ascii=False)[:6000]}

章节分析:
{json.dumps(ctx["analysis"], ensure_ascii=False)[:4000]}

本章开场剧本（第三人称，需转换为「{ctx["player_character"]}」的第一人称视角）:
{script_for_model}

风格锚点:
{json.dumps(ctx["style"], ensure_ascii=False)[:1500]}

场控摘要:
{json.dumps(ctx["control"], ensure_ascii=False)[:1500]}

任务: 写开场叙事。
- 若 opening_mode=montage：将无行动力的场景压缩为2-3段感官蒙太奇，在 first_agency 场景处停下
- 若 opening_mode=single：仅覆盖第一场景
- 将第三人称剧本转换为「{ctx["player_character"]}」的第一人称
- agency=none/low 时不要提供无法完成的行动选项
输出 JSON 字段:
- narrative: string（中文，第一人称）
- interaction_hint: string（中文；agency=none/low 时仅建议等待/感知，不要伪造行动）
- image_prompt_zh: string
- image_prompt_en: string
- field: object safety: pass|warn , deviation_level: 0-5 , note: string
- memory_updates: string[]
- scene_advanced_to: int（到达的场景序号；蒙太奇开场应设为 first_agency 场景）

【重要】所有 narrative 和 interaction_hint 必须使用中文。以角色身份来写。
"""
    raw = chat_json(client, model, sys_p, user_p, temperature=0.65, max_tokens=1800)
    try:
        return parse_json_loose(raw)
    except Exception:
        logger.exception("opening scene JSON parse failed")
        default_hint = "What would you like to do next?" if output_lang == "en" else "你接下来最想做什么？"
        return {
            "narrative": raw[:1500],
            "interaction_hint": default_hint,
            "image_prompt_zh": "",
            "image_prompt_en": "",
            "field": {"safety": "pass", "deviation_level": 0, "note": ""},
            "memory_updates": [],
        }


def _format_scene_progress(
    ordered_scenes: list[dict[str, Any]],
    current_scene_order: int,
    output_lang: str = "zh",
) -> str:
    """Format scene progress info for prompt."""
    if not ordered_scenes:
        return ""
    
    lines = []
    current_scene = None
    next_scene = None
    
    for s in ordered_scenes:
        if s.get("order") == current_scene_order:
            current_scene = s
        elif s.get("order") == current_scene_order + 1:
            next_scene = s
    
    if output_lang == "en":
        lines.append(f"【SCENE PROGRESS: Currently at scene {current_scene_order} of {len(ordered_scenes)}】")
        if current_scene:
            nec = scene_agency.resolve_interaction_necessity(current_scene)
            lines.append(f"CURRENT SCENE ({current_scene.get('scene_id')}):")
            lines.append(f"  Type: {current_scene.get('node_type', 'plot')} | Interaction: {nec}")
            lines.append(f"  Content: {(current_scene.get('player_facing_text') or '')[:300]}...")
        if next_scene:
            nn = scene_agency.resolve_interaction_necessity(next_scene)
            lines.append(f"\nNEXT SCENE ({next_scene.get('scene_id')}) - Advance to this after player completes current:")
            lines.append(f"  Type: {next_scene.get('node_type', 'plot')} | Interaction: {nn}")
            lines.append(f"  Preview: {(next_scene.get('player_facing_text') or '')[:200]}...")
        next_pause = scene_agency.next_pause_scene_order(ordered_scenes, current_scene_order, "medium")
        lines.append(f"\n⚠️ Advance plot! If current interaction is weak/none, jump to scene {next_pause}+ in ONE turn.")
    else:
        lines.append(f"【场景进度：当前第 {current_scene_order} 场景，共 {len(ordered_scenes)} 场景】")
        if current_scene:
            nec = scene_agency.resolve_interaction_necessity(current_scene)
            lines.append(f"当前场景 ({current_scene.get('scene_id')}):")
            lines.append(f"  类型: {current_scene.get('node_type', 'plot')} | 交互必要性: {nec}")
            lines.append(f"  内容: {(current_scene.get('player_facing_text') or '')[:300]}...")
        if next_scene:
            nn = scene_agency.resolve_interaction_necessity(next_scene)
            lines.append(f"\n下一场景 ({next_scene.get('scene_id')}) - 完成后推进至此:")
            lines.append(f"  类型: {next_scene.get('node_type', 'plot')} | 交互必要性: {nn}")
            lines.append(f"  预览: {(next_scene.get('player_facing_text') or '')[:200]}...")
        next_pause = scene_agency.next_pause_scene_order(ordered_scenes, current_scene_order, "medium")
        lines.append(f"\n⚠️ 必须推进剧情！若当前为弱/无交互，一段叙事内跳至第 {next_pause} 场景或更后。")
    
    return "\n".join(lines)


def generate_continue_scene(
    client: OpenAI,
    model: str,
    ctx: dict[str, Any],
    last_narrative: str,
    user_input: str,
    recent_summary: str,
    output_lang: str = "zh",
    current_scene_order: int = 1,
    guidance_level: str = "medium",
) -> dict[str, Any]:
    sys_p = _scene_system_intro(output_lang)
    ordered = _ordered_player_scenes(ctx.get("chapter_script") or {})
    
    # Build scene progress info
    scene_progress = _format_scene_progress(ordered, current_scene_order, output_lang)
    agency_guidance = _format_agency_guidance(
        ordered=ordered,
        current_scene_order=current_scene_order,
        character=ctx["player_character"],
        adaptation=ctx.get("perspective_adaptation"),
        user_input=user_input,
        output_lang=output_lang,
    )
    guidance_block = _format_guidance_level_guidance(guidance_level, output_lang)
    
    # Legacy beat outline for context
    beat_outline = ""
    if len(ordered) > 1:
        if output_lang == "en":
            beat_outline = "Full chapter scene list (for reference):\n" + "\n".join(
                f"- [{s.get('order')}] {s.get('node_type', 'plot')}: "
                f"{(s.get('player_facing_text') or '')[:80].replace(chr(10), ' ')}…"
                for s in ordered[:12]
            )
        else:
            beat_outline = "本章场景列表（参考用）:\n" + "\n".join(
                f"- [{s.get('order')}] {s.get('node_type', 'plot')}: "
                f"{(s.get('player_facing_text') or '')[:80].replace(chr(10), ' ')}…"
                for s in ordered[:12]
            )

    # Build character context
    char_context = _format_character_context(
        ctx["player_character"],
        ctx.get("player_char_info") or {},
        ctx.get("chapter_npcs") or [],
        output_lang,
    )
    
    # Build adaptation context (if available)
    adaptation_context = _format_adaptation_context(
        ctx.get("perspective_adaptation"),
        current_scene_order,
        output_lang,
    )

    if output_lang == "en":
        user_p = f"""{char_context}

{adaptation_context}

{agency_guidance}

{guidance_block}

Current chapter: Chapter {ctx["chapter_num"]}

{scene_progress}

World setting and arcs summary:
{json.dumps(ctx["world"], ensure_ascii=False)[:3000]}

Chapter analysis:
{json.dumps(ctx["analysis"], ensure_ascii=False)[:2500]}

{beat_outline}

DM/Player script (THIRD-PERSON - convert to first-person from {ctx["player_character"]}'s POV):
{json.dumps(ctx.get("chapter_script") or {}, ensure_ascii=False)[:4500]}

Style anchors:
{json.dumps(ctx["style"], ensure_ascii=False)[:1200]}

Previous narrative:
{last_narrative[:1800]}

Player action/dialogue:
{user_input}

Recent turns summary:
{recent_summary[:1200]}

Task: Continue from player input and ADVANCE the story.
- Convert THIRD-PERSON script to FIRST-PERSON from "{ctx["player_character"]}"'s perspective
- If agency=none or player chose passive/wait: FAST-FORWARD through multiple scenes in one narrative; scene_advanced_to MUST increase
- Do NOT repeat the same sleeping/sensing loop — show NEW events from the script
- If agency=low: limited perception only; still advance plot when player waits
- If agency=full: normal pacing to next scene

Output JSON fields:
- narrative: string (English, move story forward)
- interaction_hint: string (English; match agency level)
- image_prompt_zh: string
- image_prompt_en: string
- field: object with safety: pass|warn, deviation_level: 0-5, note: string
- memory_updates: string[]
- scene_advanced_to: int (MUST be > {current_scene_order} if agency=none or passive wait)

CRITICAL: Advance the plot! No repetitive loops!
"""
    else:
        user_p = f"""{char_context}

{adaptation_context}

{agency_guidance}

{guidance_block}

当前章节: 第 {ctx["chapter_num"]} 章

{scene_progress}

世界观与弧摘要:
{json.dumps(ctx["world"], ensure_ascii=False)[:4000]}

章节分析:
{json.dumps(ctx["analysis"], ensure_ascii=False)[:3000]}

{beat_outline}

本章 DM本/玩家本草案（不得向玩家直述 hidden_facts；决策点处留白给玩家）:
{json.dumps(ctx.get("chapter_script") or {}, ensure_ascii=False)[:5000]}

风格锚点:
{json.dumps(ctx["style"], ensure_ascii=False)[:1500]}

上一轮叙事:
{last_narrative[:2000]}

玩家行动/台词:
{user_input}

近期回合摘要:
{recent_summary[:1500]}

任务: 承接玩家输入，推进剧情。
- 将第三人称剧本转换为「{ctx["player_character"]}」的第一人称
- 若 agency=none 或玩家选择等待/睡觉：一段叙事内快进多个场景，scene_advanced_to 必须增加
- 禁止重复相同的睡觉/感知循环 — 必须呈现剧本中的新事件
- agency=low 时仅有限感知；玩家等待时仍应推进剧情
- agency=full 时正常推进至下一场景

输出 JSON 字段:
- narrative: string（中文，推进故事）
- interaction_hint: string（匹配行动力等级，中文）
- image_prompt_zh: string
- image_prompt_en: string
- field: object（safety: pass|warn, deviation_level: 0-5, note: string）
- memory_updates: string[]
- scene_advanced_to: int（agency=none 或被动等待时 MUST > {current_scene_order}）

【关键】必须推进剧情！禁止重复循环！
"""
    raw = chat_json(client, model, sys_p, user_p, temperature=0.7, max_tokens=2000)
    try:
        return parse_json_loose(raw)
    except Exception:
        logger.exception("continue scene JSON parse failed")
        if output_lang == "en":
            return {
                "narrative": f"(Parse failed, raw excerpt) {raw[:1200]}",
                "interaction_hint": "Continue your action.",
                "image_prompt_zh": "",
                "image_prompt_en": "",
                "field": {"safety": "pass", "deviation_level": 0, "note": ""},
                "memory_updates": [],
            }
        return {
            "narrative": f"（解析失败，模型原文片段）{raw[:1200]}",
            "interaction_hint": "继续你的行动。",
            "image_prompt_zh": "",
            "image_prompt_en": "",
            "field": {"safety": "pass", "deviation_level": 0, "note": ""},
            "memory_updates": [],
        }
