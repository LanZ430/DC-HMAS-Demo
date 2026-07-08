from __future__ import annotations

import sys
from pathlib import Path

# Allow `streamlit run dc_hmas/ui/streamlit_app.py` without editable install
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import json

import streamlit as st
from dotenv import load_dotenv

from dc_hmas.config import Settings
from dc_hmas.text_encoding import (
    cjk_ratio,
    decode_text_bytes,
    detect_content_language,
    latin_alpha_ratio,
    validate_text_for_language,
    validation_message_for_mismatch,
)
from dc_hmas.preprocessing.pipeline import (
    phase_a_segment_only,
    run_foreground_preprocessing,
    start_background_chapter_analysis,
)
from dc_hmas.telemetry import span
from dc_hmas.ui.agent_panel import render_agent_sidebar_panel
from dc_hmas.ui.play_tab import render_play_tab
from dc_hmas.ui.i18n import t, get_lang

load_dotenv(_ROOT / ".env")


DEFAULT_CSS = """
/* Default styling - will be overridden by theme */
html, body, [class*="css"] {
    font-family: 'Segoe UI', Inter, system-ui, sans-serif;
}

/* Hide Streamlit's default header/toolbar */
[data-testid="stHeader"] {
    display: none !important;
    height: 0 !important;
}
div[data-testid="stToolbar"] { 
    visibility: hidden !important; 
    height: 0 !important; 
}
header[data-testid="stHeader"] {
    display: none !important;
}

/* Full-width layout in play / preprocess */
.block-container { 
    padding-top: 1rem; 
    max-width: min(96vw, 1920px); 
}

/* Ensure selectbox dropdown appears above other elements */
[data-baseweb="popover"] {
    z-index: 9999 !important;
}
[data-baseweb="select"] [data-baseweb="popover"] {
    z-index: 9999 !important;
}
"""


def _inject_css() -> None:
    st.markdown(f"<style>{DEFAULT_CSS}</style>", unsafe_allow_html=True)
    # If a theme is active, inject its CSS
    theme_id = st.session_state.get("_current_theme_id")
    if theme_id:
        from dc_hmas.ui.themes import get_theme_css
        theme_css = get_theme_css(theme_id)
        if theme_css:
            st.markdown(f"<style>{theme_css}</style>", unsafe_allow_html=True)


def _render_preprocess(settings: Settings) -> None:
    lang = get_lang()
    st.subheader(t("prep_title"))
    st.session_state.setdefault("last_paths", None)
    st.session_state.setdefault("last_chapters", None)
    st.session_state.setdefault("_bg_processing_queue", [])

    # 显示当前后台处理状态
    bg_queue = st.session_state.get("_bg_processing_queue", [])
    if bg_queue:
        st.info(t("prep_bg_processing", count=len(bg_queue), names=", ".join(bg_queue)))

    novel_lang = st.selectbox(t("prep_lang"), ["zh", "en"], index=0, key="prep_lang")
    title = st.text_input(
        t("prep_book_title"), value="infinite_flow_novel", key="prep_title"
    )

    uploaded = st.file_uploader(t("prep_upload"), type=["txt"], key="prep_upload")

    if uploaded is None:
        st.info(t("prep_info"))
        paths = st.session_state.get("last_paths")
        if paths and paths.status_path.exists():
            st.caption(t("prep_last_progress"))
            st.json(json.loads(paths.status_path.read_text(encoding="utf-8")))
        return

    raw_bytes = uploaded.getvalue()
    expect_chinese = novel_lang == "zh"
    raw, detected_encoding = decode_text_bytes(raw_bytes, expect_chinese=expect_chinese)
    content_lang = detect_content_language(raw)
    text_ok, text_msg = validate_text_for_language(raw, novel_lang)
    mismatch = validation_message_for_mismatch(raw, novel_lang, ui_lang=lang)

    enc_label = "编码" if lang == "zh" else "Encoding"
    st.caption(f"{enc_label}: {detected_encoding} · {len(raw):,} {'字' if lang == 'zh' else 'chars'}")
    if novel_lang == "zh":
        sample_ratio = cjk_ratio(raw[:8000])
        st.caption(f"{'中文占比（样本）' if lang == 'zh' else 'CJK ratio (sample)'}: {sample_ratio:.1%}")
    else:
        alpha_ratio = latin_alpha_ratio(raw[:8000])
        st.caption(f"{'英文占比（样本）' if lang == 'zh' else 'Latin alpha (sample)'}: {alpha_ratio:.1%}")

    if mismatch:
        st.warning(mismatch)

    if text_ok:
        ok_label = "文本编码检测通过" if lang == "zh" else "Text encoding looks OK"
        st.success(ok_label)
    else:
        err_label = "文本编码异常" if lang == "zh" else "Text encoding problem"
        st.error(f"{err_label}: {text_msg}")
        hint = (
            "常见原因：文件为 GBK/GB18030 却被当作 UTF-8 读取（旧版使用 errors=ignore 会静默损坏）。"
            "请重新上传；系统会自动识别 UTF-8 / GBK / GB18030。"
            if lang == "zh"
            else "Re-upload the file; UTF-8 / GBK / GB18030 are auto-detected."
        )
        st.warning(hint)
    
    start_btn = st.button(
        t("prep_start_full"),
        type="primary",
        key="prep_run",
        disabled=not text_ok,
    )
    
    if start_btn:
        import os

        if not settings.llm_api_key and not os.environ.get("DASHSCOPE_API_KEY"):
            st.error(t("prep_api_missing"))
            return
        with st.spinner(t("prep_segmenting")):
            with span("segmenter"):
                novel_id, paths, chapters = phase_a_segment_only(
                    data_dir=settings.data_dir,
                    raw_text=raw,
                    language=novel_lang,
                    title_stub=title or uploaded.name,
                    source_encoding=detected_encoding,
                )
            st.session_state["last_paths"] = paths
            st.session_state["last_chapters"] = chapters
        
        with st.spinner(t("prep_analyzing")):
            result = run_foreground_preprocessing(
                paths=paths,
                chapters=chapters,
                title=title or uploaded.name,
                settings=settings,
            )
        st.success(result.message)
        analyzed = result.analyzed_foreground
        if analyzed < len(chapters):
            start_background_chapter_analysis(
                paths=paths,
                chapters=chapters,
                start_from=analyzed,
                settings=settings,
            )
            st.session_state["_bg_processing_queue"] = st.session_state.get(
                "_bg_processing_queue", []
            ) + [title or uploaded.name]
            st.warning(t("prep_bg_continue", start=analyzed + 1, end=len(chapters)))

    paths = st.session_state.get("last_paths")
    if paths and paths.status_path.exists():
        st.subheader(t("prep_progress"))
        status = json.loads(paths.status_path.read_text(encoding="utf-8"))
        st.json(status)
        
        if status.get("chapters_analyzed", 0) >= status.get("total_chapters", 0):
            title_name = paths.novel_root.name
            queue = st.session_state.get("_bg_processing_queue", [])
            if title_name in queue:
                queue.remove(title_name)
                st.session_state["_bg_processing_queue"] = queue
        
        if paths.world_memory_path.exists():
            with st.expander("world_memory"):
                st.json(json.loads(paths.world_memory_path.read_text(encoding="utf-8")))
        if paths.plot_memory_path.exists():
            with st.expander("plot_memory"):
                st.json(json.loads(paths.plot_memory_path.read_text(encoding="utf-8")))


def main() -> None:
    _inject_css()
    
    settings = Settings.load()
    
    # Initialize language
    if "_output_lang" not in st.session_state:
        st.session_state["_output_lang"] = "zh"
    
    # Check if in immersive mode (set by play_tab when game is active)
    immersive_mode = st.session_state.get("_immersive_mode", False)
    lang = get_lang()

    # --- Language selector at top of page (always visible) ---
    if not immersive_mode:
        header_col1, header_col2 = st.columns([4, 1])
        with header_col1:
            st.title(t("app_title"))
            st.caption(t("app_subtitle"))
        with header_col2:
            st.selectbox(
                "🌐 Language",
                ["zh", "en"],
                format_func=lambda x: "中文" if x == "zh" else "English",
                key="_output_lang",
                label_visibility="collapsed",
            )

    with st.sidebar:
        if immersive_mode:
            # Simplified sidebar during gameplay - still show language selector
            st.selectbox(
                "🌐 Language",
                ["zh", "en"],
                format_func=lambda x: "中文" if x == "zh" else "English",
                key="_output_lang",
            )
            st.divider()
            st.markdown(f"### {t('sidebar_game_active')}")
            key_ok = bool(settings.llm_api_key)
            if key_ok:
                st.success("API Key ✓")
            else:
                st.error("API Key ✗")
            
            st.divider()
            back_label = "🏠 返回主界面" if lang == "zh" else "🏠 Back to Menu"
            if st.button(back_label, key="exit_immersive"):
                # Clear all active games
                for key in list(st.session_state.keys()):
                    if key.startswith("_active_game_"):
                        st.session_state.pop(key, None)
                st.session_state["_immersive_mode"] = False
                st.session_state["play_messages"] = []
                st.session_state["_play_key"] = None
                st.session_state["_current_theme_id"] = None
                st.rerun()
        else:
            # Full sidebar when not in game
            st.subheader(t("sidebar_env"))
            st.text(f"{t('sidebar_model')}: {settings.llm_model}")
            img_status = t("sidebar_on") if settings.enable_image else t("sidebar_off")
            st.text(f"{t('sidebar_image')}: {img_status} · {settings.wanx_model}")
            st.text(f"{t('sidebar_budget')}: {settings.foreground_budget_sec}s")
            key_ok = bool(settings.llm_api_key)
            if key_ok:
                st.success(t("sidebar_api_ok"))
            else:
                st.error(t("sidebar_api_missing"))

            if not settings.demo_mode:
                render_agent_sidebar_panel()
    
    # CRITICAL FIX: In immersive mode, skip tabs entirely and render play_tab directly
    if immersive_mode:
        # No title, no tabs - just the game interface
        render_play_tab(settings)
    else:
        # Normal mode with tabs (title already rendered above)
        tab_prep, tab_play, tab_note = st.tabs([
            t("tab_preprocess"),
            t("tab_play"),
            t("tab_notes"),
        ])

        with tab_prep:
            _render_preprocess(settings)

        with tab_play:
            render_play_tab(settings)

        with tab_note:
            st.markdown(t("notes_content"))


main()
