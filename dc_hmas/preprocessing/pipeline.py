from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from openai import OpenAI

from dc_hmas import chapter_splitter
from dc_hmas.text_encoding import validate_text_for_language
from dc_hmas.agents import writer
from dc_hmas.agents import character_profiler
from dc_hmas.config import Settings
from dc_hmas.llm import get_client
from dc_hmas.memory.paths import NovelPaths, new_novel_id, read_json, write_json

from dc_hmas.preprocessing import scripts as script_writer
from dc_hmas.telemetry import span

logger = logging.getLogger(__name__)


@dataclass
class ForegroundResult:
    novel_id: str
    novel_root: Path
    chapters_total: int
    analyzed_foreground: int
    finished_in_time: bool
    scripts_written: int
    message: str


def phase_a_segment_only(
    *,
    data_dir: Path,
    raw_text: str,
    language: str,
    title_stub: str,
    source_encoding: str | None = None,
) -> tuple[str, NovelPaths, list[str]]:
    ok, msg = validate_text_for_language(raw_text, language)
    if not ok:
        raise ValueError(f"Text encoding validation failed: {msg}")

    chapters = chapter_splitter.split_into_chapters(raw_text, language)
    novel_id = new_novel_id(language, title_stub, len(chapters))
    paths = NovelPaths(data_dir / novel_id)
    paths.ensure_dirs()
    chapter_splitter.save_chapters(paths.chapters_dir, chapters)

    doc = {
        "document_id": novel_id,
        "title": title_stub,
        "language": language,
        "total_chapters": len(chapters),
        "approx_chars": len(raw_text),
        "phase": "segmented",
    }
    if source_encoding:
        doc["source_encoding"] = source_encoding
    write_json(paths.metadata_path, doc)
    _write_status(paths, {"phase": "a_done", "chapters_total": len(chapters)})
    return novel_id, paths, chapters


def run_foreground_preprocessing(
    *,
    paths: NovelPaths,
    chapters: list[str],
    title: str,
    settings: Settings,
    client: OpenAI | None = None,
    first_chapters: int = 3,
    deadline_monotonic: float | None = None,
) -> ForegroundResult:
    """Analyze first K chapters + arcs + style + control within time budget."""
    cl = client or get_client(settings)
    model = settings.llm_model
    total = len(chapters)
    k = min(first_chapters, total)
    t0 = time.monotonic()
    budget = settings.foreground_budget_sec
    deadline = deadline_monotonic if deadline_monotonic is not None else t0 + budget

    # Read language from metadata
    meta = read_json(paths.metadata_path)
    output_lang = str(meta.get("language", "zh")) if isinstance(meta, dict) else "zh"

    with span("scanner"):
        quick = writer.quick_scan_novel(
            cl, model, title=title, sample_text=chapters[0][:12000],
            output_lang=output_lang,
        )

    analyses: list[dict[str, Any]] = []
    cumulative = ""

    for i in range(1, k + 1):
        if time.monotonic() > deadline:
            logger.info("Foreground budget exceeded at chapter %s", i)
            break
        ch_text = chapters[i - 1]
        with span("analyzer", f"ch{i}"):
            analysis = writer.analyze_chapter(
                cl,
                model,
                chapter_num=i,
                total_chapters=total,
                chapter_text=ch_text,
                cumulative_context=cumulative,
                output_lang=output_lang,
            )
        write_json(paths.analysis_path(i), analysis)
        analyses.append(analysis)
        cumulative = writer.cumulative_summary_from_analyses(analyses)
        _write_status(
            paths,
            {
                "phase": "b_analyzing",
                "analyzed_through": i,
                "chapters_total": total,
                "deadline_sec": budget,
            },
        )

    arcs: dict[str, Any] = {"infinite_flow": False, "arcs": [], "framing_world": ""}
    if analyses:
        try:
            with span("arc_planner"):
                arcs = writer.infer_arcs_infinite_flow(
                    cl,
                    model,
                    title=title,
                    quick=quick,
                    chapter_analyses=analyses,
                    total_chapters=total,
                    output_lang=output_lang,
                )
        except Exception:
            logger.exception("infer_arcs failed")

    world_mem = {
        "title": title,
        "quick_scan": quick,
        "infinite_flow": arcs,
        "early_chapter_summaries": [a.get("summary", "") for a in analyses],
    }
    write_json(paths.world_memory_path, world_mem)

    plot_mem = {
        "novel_id": paths.novel_root.name,
        "total_chapters": total,
        "infinite_flow": arcs,
        "chapter_analyses_index": [
            {
                "chapter": int(a.get("chapter_num", 0)),
                "path": f"analyses/chapter_{int(a.get('chapter_num', 0)):03d}.json",
            }
            for a in analyses
        ],
        "scripts_index": [],
    }
    write_json(paths.plot_memory_path, plot_mem)

    style_mem: dict[str, Any] = {}
    if chapters and analyses:
        try:
            with span("stylist"):
                style_mem = writer.build_style_memory(
                    cl,
                    model,
                    title=title,
                    quick=quick,
                    sample_chapter=chapters[0],
                    output_lang=output_lang,
                )
        except Exception:
            logger.exception("style memory failed")
    write_json(paths.style_memory_path, style_mem)

    ctrl: dict[str, Any] = {}
    if analyses:
        world_blob = cumulative + "\n" + str(quick)
        try:
            with span("field_controller"):
                ctrl = writer.draft_control_standard(
                    cl,
                    model,
                    world_summary=world_blob,
                    genre_tags=list(quick.get("genre_tags") or []),
                    output_lang=output_lang,
                )
        except Exception:
            logger.exception("control standard failed")
    write_json(paths.control_standard_path, ctrl)

    # --- DM / 玩家本：独立于「分析截止时间」，优先保证已分析章节有可玩剧本 ---
    analyzed_nums = sorted({int(a.get("chapter_num", 0)) for a in analyses if a.get("chapter_num")})
    t_script_start = time.monotonic()
    script_cap = settings.script_phase_budget_sec
    script_deadline = (
        None
        if script_cap <= 0
        else (t_script_start + script_cap)
    )
    world_snap = read_json(paths.world_memory_path)
    if not isinstance(world_snap, dict):
        world_snap = world_mem
    style_snap = read_json(paths.style_memory_path)
    if not isinstance(style_snap, dict):
        style_snap = style_mem
    book_ctx = writer.cumulative_summary_from_analyses(analyses)
    with span("script_writer"):
        scripts_written = script_writer.generate_scripts_for_chapter_list(
            paths,
            chapters,
            analyzed_nums,
            title=title,
            cumulative_book_context=book_ctx,
            world_memory=world_snap,
            style_memory=style_snap,
            client=cl,
            model=model,
            deadline_monotonic=script_deadline,
            output_lang=output_lang,
        )

    in_time = time.monotonic() <= deadline
    _write_status(
        paths,
        {
            "phase": "foreground_done" if in_time else "foreground_partial",
            "foreground_analyzed": len(analyses),
            "chapters_total": total,
            "scripts_written_foreground": scripts_written,
            "scripts_pending_chapters": [
                n for n in analyzed_nums if not paths.script_path(n).exists()
            ],
            "interaction_ready": len(analyses) > 0,
            "elapsed_sec": round(time.monotonic() - t0, 2),
            "script_phase_cap_sec": script_cap,
        },
    )

    msg = (
        f"前台：已分析 {len(analyses)} / {total} 章；"
        f"已为其中 {scripts_written} 章生成 DM本/玩家本草案。"
        + (" 分析在预算内完成。" if in_time else " 分析已达时间上限，余章在后台继续；剧本会随分析增量补齐。")
    )
    return ForegroundResult(
        novel_id=paths.novel_root.name,
        novel_root=paths.novel_root,
        chapters_total=total,
        analyzed_foreground=len(analyses),
        finished_in_time=in_time,
        scripts_written=scripts_written,
        message=msg,
    )


def start_background_chapter_analysis(
    *,
    paths: NovelPaths,
    chapters: list[str],
    start_from: int,
    settings: Settings,
    on_done: Callable[[], None] | None = None,
) -> None:
    """Continue chapter analysis from start_from+1 to end in a daemon thread."""

    def job() -> None:
        try:
            cl = get_client(settings)
            model = settings.llm_model
            total = len(chapters)
            analyses: list[dict[str, Any]] = []
            for i in range(1, start_from + 1):
                ap = paths.analysis_path(i)
                if ap.exists():
                    analyses.append(read_json(ap))
            cumulative = writer.cumulative_summary_from_analyses(analyses)

            meta = read_json(paths.metadata_path)
            title = str(meta.get("title", paths.novel_root.name))
            output_lang = str(meta.get("language", "zh")) if isinstance(meta, dict) else "zh"

            def _sync_script(ch_num: int, ch_text: str, an: dict[str, Any], cum: str) -> None:
                w = read_json(paths.world_memory_path)
                st = read_json(paths.style_memory_path)
                if not isinstance(w, dict) or not isinstance(st, dict):
                    return
                script_writer.write_chapter_dual_script_file(
                    paths,
                    chapter_num=ch_num,
                    total_chapters=total,
                    chapter_text=ch_text,
                    analysis=an,
                    world_memory=w,
                    style_memory=st,
                    cumulative_book_context=cum,
                    title=title,
                    client=cl,
                    model=model,
                    output_lang=output_lang,
                )

            for i in range(1, start_from + 1):
                if paths.analysis_path(i).exists() and not paths.script_path(i).exists():
                    try:
                        an = read_json(paths.analysis_path(i))
                        _sync_script(i, chapters[i - 1], an, cumulative)
                    except Exception:
                        logger.exception("background catch-up script %s", i)
            for i in range(start_from + 1, total + 1):
                ch_text = chapters[i - 1]
                try:
                    analysis = writer.analyze_chapter(
                        cl,
                        model,
                        chapter_num=i,
                        total_chapters=total,
                        chapter_text=ch_text,
                        cumulative_context=cumulative,
                        output_lang=output_lang,
                    )
                except Exception:
                    logger.exception("background chapter analysis failed %s", i)
                    continue
                write_json(paths.analysis_path(i), analysis)
                analyses.append(analysis)
                cumulative = writer.cumulative_summary_from_analyses(analyses)
                try:
                    w = read_json(paths.world_memory_path)
                    st = read_json(paths.style_memory_path)
                    if isinstance(w, dict) and isinstance(st, dict):
                        script_writer.write_chapter_dual_script_file(
                            paths,
                            chapter_num=i,
                            total_chapters=total,
                            chapter_text=ch_text,
                            analysis=analysis,
                            world_memory=w,
                            style_memory=st,
                            cumulative_book_context=cumulative,
                            title=title,
                            client=cl,
                            model=model,
                            output_lang=output_lang,
                        )
                except Exception:
                    logger.exception("background chapter script failed %s", i)
                _write_status(
                    paths,
                    {
                        "phase": "background_analyzing",
                        "analyzed_through": i,
                        "chapters_total": total,
                    },
                )
            w = read_json(paths.world_memory_path)
            w["full_cumulative_summary"] = cumulative[:20000]
            write_json(paths.world_memory_path, w)
            
            # Build character archive after all analyses are complete
            _write_status(
                paths,
                {"phase": "building_character_archive", "analyzed_through": total, "chapters_total": total},
            )
            try:
                with span("character_profiler", "build_archive"):
                    world_summary = json.dumps(w, ensure_ascii=False)[:3000]
                    character_profiler.build_character_archive(
                        client=cl,
                        model=model,
                        paths=paths,
                        title=title,
                        world_summary=world_summary,
                        output_lang=output_lang,
                    )
                logger.info("Character archive built successfully")
            except Exception:
                logger.exception("Failed to build character archive")
            
            _write_status(
                paths,
                {"phase": "complete", "analyzed_through": total, "chapters_total": total},
            )
        except Exception:
            logger.exception("background preprocessing failed")
        finally:
            if on_done:
                on_done()

    threading.Thread(target=job, daemon=True).start()


def _write_status(paths: NovelPaths, patch: dict[str, Any]) -> None:
    cur: dict[str, Any] = {}
    if paths.status_path.exists():
        cur = json.loads(paths.status_path.read_text(encoding="utf-8"))
    cur.update(patch)
    cur["updated_at"] = time.time()
    write_json(paths.status_path, cur)
