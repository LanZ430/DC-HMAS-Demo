from __future__ import annotations

import json
import logging
import time
from typing import Any

from openai import OpenAI

from dc_hmas.agents import writer
from dc_hmas.memory.paths import NovelPaths, read_json, write_json

logger = logging.getLogger(__name__)


def update_plot_scripts_index(paths: NovelPaths, chapter_num: int) -> None:
    """Merge scripts/chapter_XXX into plot_memory.scripts_index."""
    plot_path = paths.plot_memory_path
    try:
        plot = read_json(plot_path) if plot_path.exists() else {}
    except (OSError, json.JSONDecodeError):
        plot = {}
    if not isinstance(plot, dict):
        plot = {}
    idx: list[dict[str, Any]] = list(plot.get("scripts_index") or [])
    rel = f"scripts/chapter_{chapter_num:03d}.json"
    found = False
    for item in idx:
        if item.get("chapter") == chapter_num:
            item["path"] = rel
            item["status"] = "draft"
            found = True
            break
    if not found:
        idx.append({"chapter": chapter_num, "path": rel, "status": "draft"})
    plot["scripts_index"] = sorted(idx, key=lambda x: int(x.get("chapter", 0)))
    write_json(plot_path, plot)


def write_chapter_dual_script_file(
    paths: NovelPaths,
    *,
    chapter_num: int,
    total_chapters: int,
    chapter_text: str,
    analysis: dict[str, Any],
    world_memory: dict[str, Any],
    style_memory: dict[str, Any],
    cumulative_book_context: str,
    title: str,
    client: OpenAI,
    model: str,
    output_lang: str = "zh",
) -> dict[str, Any]:
    script = writer.generate_chapter_dual_script(
        client,
        model,
        title=title,
        chapter_num=chapter_num,
        total_chapters=total_chapters,
        chapter_text=chapter_text,
        analysis=analysis,
        world_memory=world_memory,
        style_memory=style_memory,
        cumulative_book_context=cumulative_book_context,
        output_lang=output_lang,
    )
    script["written_at"] = time.time()
    sp = paths.script_path(chapter_num)
    write_json(sp, script)
    update_plot_scripts_index(paths, chapter_num)
    return script


def generate_scripts_for_chapter_list(
    paths: NovelPaths,
    chapters: list[str],
    chapter_numbers: list[int],
    *,
    title: str,
    cumulative_book_context: str,
    world_memory: dict[str, Any],
    style_memory: dict[str, Any],
    client: OpenAI,
    model: str,
    deadline_monotonic: float | None,
    output_lang: str = "zh",
) -> int:
    """Write DM/player scripts for each chapter in chapter_numbers. Returns count written."""
    total = len(chapters)
    done = 0
    for n in chapter_numbers:
        if deadline_monotonic is not None and time.monotonic() > deadline_monotonic:
            logger.info("Script phase stopped at deadline before chapter %s", n)
            break
        ap = paths.analysis_path(n)
        if not ap.exists():
            continue
        try:
            analysis = read_json(ap)
            if not isinstance(analysis, dict):
                continue
        except (OSError, json.JSONDecodeError):
            continue
        ch_text = chapters[n - 1] if 0 < n <= len(chapters) else ""
        try:
            write_chapter_dual_script_file(
                paths,
                chapter_num=n,
                total_chapters=total,
                chapter_text=ch_text,
                analysis=analysis,
                world_memory=world_memory,
                style_memory=style_memory,
                cumulative_book_context=cumulative_book_context,
                title=title,
                client=client,
                model=model,
                output_lang=output_lang,
            )
            done += 1
        except Exception:
            logger.exception("script generation failed chapter %s", n)
    return done
