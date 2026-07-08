from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI

from dc_hmas.chapter_splitter import parse_json_loose, truncate_chapter_for_llm
from dc_hmas.llm import chat_json
from dc_hmas.prompts.templates import get_prompt

logger = logging.getLogger(__name__)


def quick_scan_novel(
    client: OpenAI,
    model: str,
    *,
    title: str,
    sample_text: str,
    output_lang: str = "zh",
) -> dict[str, Any]:
    system = get_prompt("scanner", "system", output_lang)
    user = get_prompt("scanner", "user", output_lang, title=title, sample_text=sample_text[:8000])
    raw = chat_json(client, model, system, user, temperature=0.2, max_tokens=600)
    try:
        return parse_json_loose(raw)
    except Exception:
        logger.exception("quick_scan parse failed, falling back")
        return {
            "genre_tags": [],
            "likely_infinite_flow": False,
            "premise_one_line": "",
            "estimated_tone": "",
            "language": output_lang,
        }


def analyze_chapter(
    client: OpenAI,
    model: str,
    *,
    chapter_num: int,
    total_chapters: int,
    chapter_text: str,
    cumulative_context: str,
    output_lang: str = "zh",
) -> dict[str, Any]:
    truncated = truncate_chapter_for_llm(chapter_text)
    system = get_prompt("analyzer", "system", output_lang)
    user = get_prompt(
        "analyzer", "user", output_lang,
        total_chapters=total_chapters,
        chapter_num=chapter_num,
        cumulative_context=cumulative_context or ("（无）" if output_lang == "zh" else "(None)"),
        chapter_text=truncated,
    )
    raw = chat_json(client, model, system, user, temperature=0.25, max_tokens=2800)
    try:
        data = parse_json_loose(raw)
    except Exception:
        logger.exception("analyze_chapter parse failed ch=%s, using fallback", chapter_num)
        data = {
            "summary": raw[:800] if raw else "",
            "key_events": [],
            "characters": [],
            "settings": [],
            "infinite_flow_cues": [],
            "tags": [],
            "parse_error": True,
        }
    data["chapter_num"] = chapter_num
    return data


def infer_arcs_infinite_flow(
    client: OpenAI,
    model: str,
    *,
    title: str,
    quick: dict[str, Any],
    chapter_analyses: list[dict[str, Any]],
    total_chapters: int,
    output_lang: str = "zh",
) -> dict[str, Any]:
    buf_lines: list[str] = []
    for a in chapter_analyses:
        n = a.get("chapter_num")
        buf_lines.append(f"=== Chapter outline {n} ===")
        buf_lines.append(str(a.get("summary", "")))
        cues = a.get("infinite_flow_cues") or []
        if cues:
            cue_label = "副本/系统线索" if output_lang == "zh" else "Dungeon/system cues"
            buf_lines.append(f"{cue_label}: " + "; ".join(cues))
    blob = "\n".join(buf_lines)

    system = get_prompt("arc_planner", "system", output_lang)
    user = get_prompt(
        "arc_planner", "user", output_lang,
        title=title,
        total_chapters=total_chapters,
        quick=quick,
        blob=blob,
    )
    raw = chat_json(client, model, system, user, temperature=0.2, max_tokens=1200)
    return parse_json_loose(raw)


def build_style_memory(
    client: OpenAI,
    model: str,
    *,
    title: str,
    quick: dict[str, Any],
    sample_chapter: str,
    output_lang: str = "zh",
) -> dict[str, Any]:
    truncated = truncate_chapter_for_llm(sample_chapter, head=3500, tail=800)
    system = get_prompt("stylist", "system", output_lang)
    user = get_prompt(
        "stylist", "user", output_lang,
        title=title,
        quick=quick,
        sample_chapter=truncated,
    )
    raw = chat_json(client, model, system, user, temperature=0.2, max_tokens=900)
    return parse_json_loose(raw)


def draft_control_standard(
    client: OpenAI,
    model: str,
    *,
    world_summary: str,
    genre_tags: list[str],
    output_lang: str = "zh",
) -> dict[str, Any]:
    system = get_prompt("field_controller", "system", output_lang)
    user = get_prompt(
        "field_controller", "user", output_lang,
        genre_tags=genre_tags,
        world_summary=world_summary[:6000],
    )
    raw = chat_json(client, model, system, user, temperature=0.2, max_tokens=800)
    try:
        return parse_json_loose(raw)
    except Exception:
        return {
            "content_rating": "general",
            "hard_limits": [],
            "world_rules": [],
            "deviation_thresholds": {"soft_hint_at": 3, "npc_at": 4, "pullback_at": 5},
            "notes": "fallback",
        }


def cumulative_summary_from_analyses(analyses: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for a in sorted(analyses, key=lambda x: int(x.get("chapter_num", 0))):
        parts.append(f"第{a.get('chapter_num')}章: {a.get('summary', '')}")
    return "\n".join(parts)[:12000]


def generate_chapter_dual_script(
    client: OpenAI,
    model: str,
    *,
    title: str,
    chapter_num: int,
    total_chapters: int,
    chapter_text: str,
    analysis: dict[str, Any],
    world_memory: dict[str, Any],
    style_memory: dict[str, Any],
    cumulative_book_context: str,
    output_lang: str = "zh",
) -> dict[str, Any]:
    """Produce DM-facing truth plus player-facing segmented script for one chapter."""
    excerpt = truncate_chapter_for_llm(chapter_text, head=6000, tail=2000)
    system = get_prompt("script_writer", "system", output_lang)
    user = get_prompt(
        "script_writer", "user", output_lang,
        title=title,
        chapter_num=chapter_num,
        total_chapters=total_chapters,
        cumulative_book_context=cumulative_book_context[:8000],
        world_memory=json.dumps(world_memory, ensure_ascii=False)[:6000],
        style_memory=json.dumps(style_memory, ensure_ascii=False)[:2500],
        analysis=json.dumps(analysis, ensure_ascii=False)[:6000],
        excerpt=excerpt,
        chapter_num_padded=f"{chapter_num:03d}",
    )
    raw = chat_json(client, model, system, user, temperature=0.35, max_tokens=5200)
    try:
        data = parse_json_loose(raw)
    except Exception:
        logger.exception("dual script parse failed")
        return {
            "chapter_num": chapter_num,
            "status": "draft",
            "dm_script": {
                "chapter_beat_summary": "",
                "hidden_facts": [],
                "rules_and_constraints": [],
                "npc_behaviors": {},
                "branch_ideas": [],
                "checkpoints": [],
            },
            "player_script": {"scenes": []},
            "notes": "parse_error",
            "_raw_fragment": raw[:2000],
        }
    data.setdefault("chapter_num", chapter_num)
    data.setdefault("status", "draft")
    data.setdefault("dm_script", {})
    ps = data.setdefault("player_script", {"scenes": []})
    scenes = ps.get("scenes") if isinstance(ps, dict) else None
    if isinstance(scenes, list):
        for i, sc in enumerate(scenes):
            if not isinstance(sc, dict):
                continue
            nt = sc.get("node_type", "plot")
            if nt not in ("plot", "decision", "passive"):
                sc["node_type"] = "plot"
            sc.setdefault("character_agency", {})
            sc.setdefault("characters_present", [])
            sc.setdefault("interaction_rationale", "")
            if "interaction_necessity" not in sc:
                if nt == "passive":
                    sc["interaction_necessity"] = "none"
                elif nt == "decision":
                    sc["interaction_necessity"] = "strong"
                else:
                    sc["interaction_necessity"] = "medium"
            elif sc.get("interaction_necessity") not in ("strong", "medium", "weak", "none"):
                sc["interaction_necessity"] = "medium"
            sc.setdefault("decision_prompt", "")
            sc.setdefault("suggested_choice_angles", [])
            if not isinstance(sc.get("suggested_choice_angles"), list):
                sc["suggested_choice_angles"] = []
            sc.setdefault("order", i + 1)
    return data
