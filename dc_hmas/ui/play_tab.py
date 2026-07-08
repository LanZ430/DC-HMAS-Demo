from __future__ import annotations

import json
import time
from typing import Any

import streamlit as st

from dc_hmas.catalog import discover_novels, novel_paths_from_row
from dc_hmas.config import Settings
from dc_hmas.interaction.character_status import (
    initialize_character_status,
    load_character_status,
    save_character_status,
    update_character_status,
)
from dc_hmas.interaction.agency import (
    compute_scene_advance_target,
    ordered_player_scenes,
    resolve_goal_panel_items,
    scene_by_order,
)
from dc_hmas.interaction.scene_engine import (
    generate_continue_scene,
    generate_opening_scene,
    load_play_context,
    generate_perspective_adaptation,
    load_perspective_adaptation,
)
from dc_hmas.interaction.session_store import (
    append_turn,
    create_new_session,
    get_session_settings,
    list_sessions,
    load_play_session,
    save_play_session,
    session_path,
    get_scene_progress,
    advance_scene,
    update_session_settings,
)
from dc_hmas.llm import get_client
from dc_hmas.memory.paths import read_json
from dc_hmas.services.wanx_image import synthesize_image_url
from dc_hmas.telemetry import span
from dc_hmas.ui.i18n import t, get_lang
from dc_hmas.ui.themes import (
    THEMES,
    get_theme,
    get_theme_css,
    suggest_theme_from_genre,
)
from dc_hmas.ui.themes.panels import render_objectives_panel, render_theme_selector, render_themed_status_panel
from dc_hmas.ui.play_layout_css import play_viewport_css


def render_play_tab(settings: Settings) -> None:
    output_lang = st.session_state.get("_output_lang", "zh")
    st.subheader(t("play_title"))

    novels = discover_novels(settings.data_dir)
    if not novels:
        st.warning(t("play_no_archives"))
        st.session_state["_immersive_mode"] = False
        return

    # --- 小说选择 ---
    ch_word = "章" if output_lang == "zh" else "ch."
    labels = [
        f"{r.get('title', r['_novel_id'])} · {r.get('total_chapters', '?')} {ch_word}"
        for r in novels
    ]
    choice = st.selectbox(t("play_select_novel"), range(len(labels)), format_func=lambda i: labels[i])
    doc = novels[choice]
    novel_id = doc["_novel_id"]
    paths = novel_paths_from_row(doc)
    if paths is None:
        st.error(t("play_invalid_path"))
        return

    total = int(doc.get("total_chapters") or 1)
    
    # Get genre tags for theme suggestion
    genre_tags = []
    if paths.world_memory_path.exists():
        try:
            wm = read_json(paths.world_memory_path)
            genre_tags = wm.get("quick_scan", {}).get("genre_tags", [])
        except Exception:
            pass
    suggested_theme = suggest_theme_from_genre(genre_tags)

    # --- 检查是否有活跃的游戏会话 ---
    active_key = f"_active_game_{novel_id}"
    active_game = st.session_state.get(active_key)
    
    # 如果有活跃会话，进入沉浸模式
    if active_game and active_game.get("session_name"):
        session_name = active_game["session_name"]
        chapter = active_game["chapter"]
        character = active_game["character"]
        theme_id = active_game.get("theme_id", "modern_minimal")
        
        # Set immersive mode flag
        st.session_state["_immersive_mode"] = True
        st.session_state["_current_theme_id"] = theme_id
        
        # Apply theme CSS
        theme = get_theme(theme_id)
        if theme:
            st.markdown(f"<style>{theme.css}</style>", unsafe_allow_html=True)
        
        # Sticky session control bar + compact session info
        session_settings = _render_session_control_bar(
            paths, session_name, settings, output_lang, theme,
            chapter=chapter, character=character,
        )
        
        st.markdown(
            """
            <style>
            div[data-testid="stVerticalBlock"]:has(> div > div > .dc-hmas-control-bar-anchor) {
                position: sticky;
                top: 0;
                z-index: 999;
                background: var(--background-color, #0e1117);
                padding-bottom: 0.25rem;
                border-bottom: 1px solid rgba(128, 128, 128, 0.25);
                margin-bottom: 0.75rem;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Not in immersive mode
        st.session_state["_immersive_mode"] = False
        
        # --- 存档模式选择 ---
        st.divider()
        existing_sessions = list_sessions(paths)
        
        session_mode = st.radio(
            t("play_mode"),
            ["new", "continue"],
            format_func=lambda x: t("play_new_game") if x == "new" else t("play_continue", count=len(existing_sessions)),
            horizontal=True,
            key=f"session_mode_{novel_id}",
        )

        session_name = "default"
        chapter = 1
        character = "祝宁"
        theme_id = suggested_theme
        
        if session_mode == "continue" and existing_sessions:
            # 显示存档列表
            session_labels = []
            for s in existing_sessions:
                ts = time.strftime("%m/%d %H:%M", time.localtime(s.get("modified", 0)))
                ch = s.get("chapter") or "?"
                turns = s.get("turn_count", 0)
                turn_word = "轮对话" if output_lang == "zh" else "turns"
                ch_prefix = "第" if output_lang == "zh" else "Ch."
                ch_suffix = "章" if output_lang == "zh" else ""
                session_labels.append(f"{ch_prefix}{ch}{ch_suffix} · {turns} {turn_word} · {ts} · {s['name']}")
            
            session_idx = st.selectbox(
                t("play_select_save"),
                range(len(existing_sessions)),
                format_func=lambda i: session_labels[i],
                key=f"session_select_{novel_id}",
            )
            selected_session = existing_sessions[session_idx]
            session_name = selected_session["name"]
            
            # 加载存档信息
            sp = session_path(paths, session_name)
            saved_data = load_play_session(sp)
            chapter = saved_data.get("chapter", 1)
            character = saved_data.get("character", "") or "祝宁"
            theme_id = saved_data.get("theme_id", suggested_theme)
            
            col1, col2 = st.columns(2)
            with col1:
                st.caption(t("play_save_chapter", num=chapter))
            with col2:
                st.caption(t("play_save_character", name=character))
            
            # 开始继续游戏按钮
            if st.button(t("play_btn_continue"), type="primary", key="continue_game"):
                st.session_state[active_key] = {
                    "session_name": session_name,
                    "chapter": chapter,
                    "character": character,
                    "theme_id": theme_id,
                }
                st.rerun()
            return  # 等待用户点击继续
            
        else:
            # 新游戏：选择章节和角色
            col1, col2 = st.columns(2)
            with col1:
                chapter = st.number_input(t("play_select_chapter"), min_value=1, max_value=max(1, total), value=1, step=1)
            
            # 获取角色列表
            an_path = paths.analysis_path(int(chapter))
            char_list: list[dict] = []
            if an_path.exists():
                try:
                    analysis = json.loads(an_path.read_text(encoding="utf-8"))
                    chars = analysis.get("characters") or []
                    char_list = [c for c in chars if isinstance(c, dict) and c.get("name")]
                except (OSError, json.JSONDecodeError):
                    pass
            
            with col2:
                if char_list:
                    # 下拉选择角色
                    char_names = [c.get("name", "") for c in char_list]
                    char_labels = [
                        f"{c.get('name', '')} - {c.get('role_in_chapter', '')[:30]}"
                        for c in char_list
                    ]
                    selected_idx = st.selectbox(
                        t("play_select_character"),
                        range(len(char_names)),
                        format_func=lambda i: char_labels[i],
                        key="char_select",
                    )
                    character = char_names[selected_idx]
                    # 保存选中角色的详细信息供后续使用
                    st.session_state["_selected_char_info"] = char_list[selected_idx]
                else:
                    # 无角色数据时允许手动输入
                    default_char = "祝宁" if output_lang == "zh" else "Protagonist"
                    character = st.text_input(
                        t("play_select_character"),
                        value=default_char,
                        help=t("play_char_hint_none"),
                    )
                    st.session_state["_selected_char_info"] = {"name": character, "role_in_chapter": ""}
            
            # --- 主题选择 ---
            st.divider()
            _render_theme_selection(suggested_theme, output_lang)
            theme_id = st.session_state.get("_selected_theme", suggested_theme)
            
            # 开始新游戏按钮
            if st.button(t("play_btn_start"), type="primary", key="start_new_game"):
                session_name = create_new_session(paths, int(chapter), character)
                # Save theme to session
                sp = session_path(paths, session_name)
                saved = load_play_session(sp)
                saved["theme_id"] = theme_id
                save_play_session(sp, saved)
                
                st.session_state[active_key] = {
                    "session_name": session_name,
                    "chapter": int(chapter),
                    "character": character,
                    "theme_id": theme_id,
                }
                st.rerun()
            return  # 等待用户点击开始

    # --- 会话状态管理（仅在有活跃游戏时执行） ---
    play_key = (novel_id, int(chapter), session_name)
    st.session_state.setdefault("play_messages", [])
    st.session_state.setdefault("_play_key", None)
    st.session_state.setdefault("_char_status", None)
    st.session_state.setdefault("_system_logs", [])
    
    output_lang = st.session_state.get("_output_lang", "zh")
    theme = get_theme(theme_id)
    
    # 切换存档时重新加载
    if st.session_state["_play_key"] != play_key:
        sp = session_path(paths, session_name)
        saved = load_play_session(sp)
        st.session_state["play_messages"] = [
            {"role": t["role"], "content": t["content"], "meta": t.get("meta", {})}
            for t in saved.get("turns", [])
        ]
        st.session_state["_play_key"] = play_key
        # 加载角色状态
        st.session_state["_char_status"] = load_character_status(paths, session_name)
        # 加载系统日志（如果有）
        st.session_state["_system_logs"] = saved.get("system_logs", [])

    guidance_level = session_settings.get("guidance_level", "medium")
    goal_on = bool(session_settings.get("goal_mode"))
    session_enable_image = bool(session_settings.get("enable_image"))

    current_scene_order, _ = get_scene_progress(paths, session_name)
    char_info = st.session_state.get("_selected_char_info") or {}
    play_ctx = load_play_context(paths, int(chapter), character, char_info)
    objectives: list[dict[str, Any]] = []
    if goal_on:
        ordered = ordered_player_scenes(play_ctx.get("chapter_script") or {})
        current_scene = scene_by_order(ordered, current_scene_order)
        objectives = resolve_goal_panel_items(
            scene=current_scene,
            guidance_level=guidance_level,
            output_lang=output_lang,
            char_status=st.session_state.get("_char_status"),
            world=play_ctx.get("world"),
            chapter_num=int(chapter),
        )

    # --- Play layout: 20% | 60% | 20%, viewport-fixed side panels ---
    layout_class = "dc-hmas-layout-three" if goal_on else "dc-hmas-layout-two"
    st.markdown(play_viewport_css(goal_on=goal_on), unsafe_allow_html=True)

    st.markdown(f'<div class="dc-hmas-play-row-marker {layout_class}"></div>', unsafe_allow_html=True)
    if goal_on:
        goal_col, main_col, status_col = st.columns([1, 3, 1])
    else:
        goal_col = None
        main_col, status_col = st.columns([3, 1])

    if goal_col is not None:
        with goal_col:
            st.markdown('<div class="dc-hmas-left-panel-marker"></div>', unsafe_allow_html=True)
            render_objectives_panel(objectives, output_lang, theme=theme)

    with status_col:
        st.markdown('<div class="dc-hmas-right-panel-marker"></div>', unsafe_allow_html=True)
        if theme:
            render_themed_status_panel(
                theme=theme,
                char_status=st.session_state.get("_char_status"),
                character=character,
                output_lang=output_lang,
                system_logs=st.session_state.get("_system_logs"),
                goal_mode=goal_on,
            )
        else:
            _render_character_status_panel(
                paths, session_name, character, settings, int(chapter)
            )

    with main_col:
        st.markdown('<div class="dc-hmas-main-col-marker"></div>', unsafe_allow_html=True)
        if session_enable_image:
            img_help = t("ctrl_image_session_on")
            if not settings.llm_api_key:
                img_help += f" ({t('ctrl_image_need_key')})"
        else:
            img_help = t("ctrl_image_session_off")
        st.caption(img_help)

        # --- 开场按钮 ---
        if not st.session_state["play_messages"]:
            if st.button(t("play_btn_opening"), type="primary"):
                if not settings.llm_api_key:
                    st.error(t("play_need_api"))
                    return
                with st.spinner(t("play_generating")):
                    client = get_client(settings)
                    
                    # Generate perspective adaptation layer if not exists
                    existing_adaptation = load_perspective_adaptation(paths, int(chapter), character)
                    if not existing_adaptation:
                        with st.spinner(t("play_adapting_perspective")):
                            with span("perspective_adapter", "generate"):
                                generate_perspective_adaptation(
                                    client, settings.llm_model, paths,
                                    int(chapter), character, output_lang
                                )
                    
                    ctx = load_play_context(paths, int(chapter), character, char_info)
                    with span("host", "opening"):
                        scene = generate_opening_scene(
                            client,
                            settings.llm_model,
                            ctx,
                            output_lang=output_lang,
                            guidance_level=guidance_level,
                        )
                    meta = _scene_meta(scene, settings, session_enable_image)
                    _persist_scene_progress(
                        paths, session_name, int(chapter), ctx, character,
                        current_scene_order=1, scene=scene,
                    )
                    append_turn(
                        paths,
                        role="assistant",
                        content=scene.get("narrative", ""),
                        meta=meta,
                        session_name=session_name,
                    )
                    st.session_state["play_messages"].append(
                        {"role": "assistant", "content": scene.get("narrative", ""), "meta": meta}
                    )
                    # 初始化角色状态（传入开场文本作为唯一事实依据）
                    _initialize_status_if_needed(
                        client, settings.llm_model, paths, session_name,
                        character, int(chapter), output_lang,
                        opening_narrative=scene.get("narrative", ""),
                    )
                    # 添加系统日志（用于无限流主题）
                    log_msg = f"[系统] 副本开始 - 第{chapter}章" if output_lang == "zh" else f"[SYSTEM] Dungeon Start - Chapter {chapter}"
                    _add_system_log(log_msg, output_lang)
                    mem_updates = meta.get("memory_updates") or []
                    if isinstance(mem_updates, list):
                        for update in mem_updates[:2]:
                            _add_system_log(f"[记录] {update}" if output_lang == "zh" else f"[LOG] {update}", output_lang)
                st.rerun()
        
        # --- 显示对话历史 ---
        for msg in st.session_state["play_messages"]:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.write(msg["content"])
            else:
                with st.chat_message("assistant"):
                    st.markdown(msg["content"])
                    m = msg.get("meta") or {}
                    if m.get("image_url"):
                        try:
                            st.image(m["image_url"], caption=t("play_image_caption"), use_container_width=True)
                        except Exception:
                            st.caption(f"Image URL: {m['image_url']}")
                    if m.get("image_prompt_zh") or m.get("image_prompt_en"):
                        with st.expander(t("play_image_prompt")):
                            st.text(m.get("image_prompt_zh") or "")
                            st.text(m.get("image_prompt_en") or "")
                    if m.get("interaction_hint") and guidance_level != "weak":
                        hint = m["interaction_hint"]
                        if guidance_level == "strong":
                            st.info(t("play_hint", hint=hint))
                        else:
                            st.caption(t("play_hint", hint=hint))

        # --- 输入框 ---
        if prompt := st.chat_input(t("play_input_hint")):
            if not settings.llm_api_key:
                st.error(t("play_need_api"))
                return
            st.session_state["play_messages"].append({"role": "user", "content": prompt})
            append_turn(paths, role="user", content=prompt, session_name=session_name)
            last_ai = next(
                (m for m in reversed(st.session_state["play_messages"]) if m["role"] == "assistant"),
                None,
            )
            last_narr = (last_ai or {}).get("content", "") if last_ai else ""
            recent = "\n".join(
                f"{m['role']}: {m['content'][:300]}"
                for m in st.session_state["play_messages"][-8:]
            )
            with st.spinner(t("play_continuing")):
                client = get_client(settings)
                ctx = load_play_context(paths, int(chapter), character, char_info)
                
                # Get current scene progress
                current_scene_order, completed_scenes = get_scene_progress(paths, session_name)
                
                with span("host", "continue"):
                    scene = generate_continue_scene(
                        client,
                        settings.llm_model,
                        ctx,
                        last_narr,
                        prompt,
                        recent,
                        output_lang=output_lang,
                        current_scene_order=current_scene_order,
                        guidance_level=guidance_level,
                    )
                
                # Advance scene with passive fast-forward rules
                _persist_scene_progress(
                    paths, session_name, int(chapter), ctx, character,
                    current_scene_order=current_scene_order,
                    scene=scene,
                    user_input=prompt,
                )
                
                meta = _scene_meta(scene, settings, session_enable_image)
                append_turn(
                    paths,
                    role="assistant",
                    content=scene.get("narrative", ""),
                    meta=meta,
                    session_name=session_name,
                )
                st.session_state["play_messages"].append(
                    {"role": "assistant", "content": scene.get("narrative", ""), "meta": meta}
                )
                # 更新角色状态
                _update_status_after_action(
                    client, settings.llm_model, paths, session_name,
                    prompt, scene.get("narrative", ""),
                    meta.get("memory_updates", []), output_lang
                )
                # 添加系统日志
                mem_updates = meta.get("memory_updates") or []
                if isinstance(mem_updates, list):
                    for update in mem_updates[:2]:
                        log_prefix = "[更新]" if output_lang == "zh" else "[UPDATE]"
                        _add_system_log(f"{log_prefix} {update}", output_lang)
            st.rerun()

        # --- 存档信息 ---
        st.divider()
        with st.expander(t("play_save_details")):
            sp = session_path(paths, session_name)
            st.caption(f"{t('play_save_name')}: {session_name}")
            st.caption(f"{t('play_save_path')}: {sp}")
            if sp.exists():
                st.json(load_play_session(sp))


def _persist_scene_progress(
    paths: Any,
    session_name: str,
    chapter: int,
    ctx: dict[str, Any],
    character: str,
    current_scene_order: int,
    scene: dict[str, Any],
    user_input: str = "",
) -> None:
    """Update session scene progress with model output + passive fast-forward rules."""
    ordered = ordered_player_scenes(ctx.get("chapter_script") or {})
    model_to = scene.get("scene_advanced_to")
    if isinstance(model_to, str) and model_to.isdigit():
        model_to = int(model_to)

    target = compute_scene_advance_target(
        current_order=current_scene_order,
        ordered_scenes=ordered,
        character=character,
        adaptation=ctx.get("perspective_adaptation"),
        user_input=user_input,
        model_advanced_to=model_to if isinstance(model_to, int) else None,
    )
    if target <= current_scene_order:
        return

    sess_path = session_path(paths, session_name)
    sess_data = load_play_session(sess_path)
    sess_data["current_scene_order"] = target
    completed = sess_data.setdefault("completed_scenes", [])
    for order in range(current_scene_order, target):
        sid = f"ch{int(chapter):03d}_sc{order:02d}"
        if sid not in completed:
            completed.append(sid)
    save_play_session(sess_path, sess_data)


def _add_system_log(message: str, output_lang: str) -> None:
    """Add a system log entry for infinite flow theme."""
    logs = st.session_state.get("_system_logs", [])
    timestamp = time.strftime("%H:%M:%S")
    logs.append(f"{timestamp} {message}")
    # Keep only last 20 entries
    st.session_state["_system_logs"] = logs[-20:]


def _render_session_control_bar(
    paths: Any,
    session_name: str,
    settings: Settings,
    output_lang: str,
    theme: Any,
    *,
    chapter: int,
    character: str,
) -> dict[str, Any]:
    """Sticky top bar: image toggle, goal mode, guidance level."""
    st.markdown('<div class="dc-hmas-control-bar-anchor"></div>', unsafe_allow_html=True)
    current = get_session_settings(paths, session_name)

    c_info, c_img, c_goal, c_guide, c_exit = st.columns([2.4, 0.9, 0.9, 2.0, 0.7])
    with c_info:
        theme_name = ""
        if theme:
            theme_name = theme.name_zh if output_lang == "zh" else theme.name_en
        info = f"{t('play_chapter', num=chapter)} · {t('play_character', name=character)}"
        if theme_name:
            info += f" · 🎨 {theme_name}"
        st.caption(info)

    with c_img:
        img_val = st.toggle(
            t("ctrl_image"),
            value=current["enable_image"],
            key=f"toggle_img_{session_name}",
        )
    with c_goal:
        goal_val = st.toggle(
            t("ctrl_goal_mode"),
            value=current["goal_mode"],
            key=f"toggle_goal_{session_name}",
        )
    with c_guide:
        levels = ["weak", "medium", "strong"]
        label_map = {
            "weak": t("ctrl_guidance_weak"),
            "medium": t("ctrl_guidance_medium"),
            "strong": t("ctrl_guidance_strong"),
        }
        guide_val = st.radio(
            t("ctrl_guidance"),
            levels,
            index=levels.index(current["guidance_level"]),
            horizontal=True,
            format_func=lambda x: label_map[x],
            key=f"guide_{session_name}",
        )
    with c_exit:
        if st.button(t("play_exit"), key="exit_game", help=t("play_exit_help")):
            for key in list(st.session_state.keys()):
                if key.startswith("_active_game_"):
                    st.session_state.pop(key, None)
            st.session_state["play_messages"] = []
            st.session_state["_play_key"] = None
            st.session_state["_immersive_mode"] = False
            st.session_state["_current_theme_id"] = None
            st.rerun()

    changed = False
    kwargs: dict[str, Any] = {}
    if img_val != current["enable_image"]:
        kwargs["enable_image"] = img_val
        changed = True
    if goal_val != current["goal_mode"]:
        kwargs["goal_mode"] = goal_val
        changed = True
    if guide_val != current["guidance_level"]:
        kwargs["guidance_level"] = guide_val
        changed = True
    if changed:
        update_session_settings(paths, session_name, **kwargs)
        st.rerun()
    return current


def _render_theme_selection(suggested_theme: str, output_lang: str) -> None:
    """Render theme selection UI."""
    from dc_hmas.ui.themes.definitions import THEMES, THEME_CATEGORIES
    
    st.markdown(f"**{t('play_select_theme')}**")
    
    # Show suggestion
    suggested = THEMES.get(suggested_theme)
    if suggested:
        sug_name = suggested.name_zh if output_lang == "zh" else suggested.name_en
        st.caption(t("play_theme_suggest", name=sug_name))
    
    # Create options grouped by category
    all_options = []
    for cat_id in ["modern", "ancient", "fantasy", "scifi"]:
        cat_info = THEME_CATEGORIES.get(cat_id, {})
        cat_name = cat_info.get("zh" if output_lang == "zh" else "en", cat_id)
        for theme in THEMES.values():
            if theme.category == cat_id:
                theme_name = theme.name_zh if output_lang == "zh" else theme.name_en
                theme_desc = theme.description_zh if output_lang == "zh" else theme.description_en
                all_options.append({
                    "id": theme.id,
                    "label": f"{cat_name} › {theme_name}",
                    "desc": theme_desc,
                })
    
    # Find default index
    default_idx = 0
    current = st.session_state.get("_selected_theme", suggested_theme)
    for i, opt in enumerate(all_options):
        if opt["id"] == current:
            default_idx = i
            break
    
    selected_idx = st.selectbox(
        "主题" if output_lang == "zh" else "Theme",
        range(len(all_options)),
        index=default_idx,
        format_func=lambda i: all_options[i]["label"],
        key="theme_select_box",
        label_visibility="collapsed",
    )
    
    selected_theme = all_options[selected_idx]
    st.session_state["_selected_theme"] = selected_theme["id"]
    
    # Show description
    st.caption(f"_{selected_theme['desc']}_")
    
    # Preview theme colors
    theme_obj = THEMES.get(selected_theme["id"])
    if theme_obj:
        preview_label = t("theme_preview")
        theme_type = t("theme_dark") if theme_obj.is_dark else t("theme_light")
        
        with st.expander(f"👁 {preview_label} ({theme_type})", expanded=False):
            # Extract key colors from CSS for preview
            preview_bg = "#222831" if theme_obj.is_dark else "#F5F5F5"
            preview_text = "#EEEEEE" if theme_obj.is_dark else "#333333"
            
            st.markdown(
                f"""
                <style>
                .theme-preview-{theme_obj.id} {{
                    padding: 16px;
                    border-radius: 8px;
                    margin: 8px 0;
                }}
                </style>
                <div class="theme-preview-{theme_obj.id}" style="background: {preview_bg}; color: {preview_text};">
                    <div style="font-size: 0.85rem; margin-bottom: 12px; opacity: 0.8;">
                        {theme_type}
                    </div>
                    <style>{theme_obj.css}</style>
                    <div class="theme-status-panel" style="max-width: 250px;">
                        <h3 style="font-size: 0.9rem; margin: 0 0 10px 0;">
                            {theme_obj.status_panel_title_zh if output_lang == "zh" else theme_obj.status_panel_title_en}
                        </h3>
                        <div style="margin: 8px 0;">
                            <small style="display: block; margin-bottom: 4px;">{t("theme_hp")}: 75</small>
                            <div class="theme-attr-bar">
                                <div class="theme-attr-fill" style="width: 75%;"></div>
                            </div>
                        </div>
                        <div style="margin: 8px 0;">
                            <small style="display: block; margin-bottom: 4px;">{t("theme_sp")}: 90</small>
                            <div class="theme-attr-bar">
                                <div class="theme-attr-fill" style="width: 90%;"></div>
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _scene_meta(
    scene: dict[str, Any],
    settings: Settings,
    session_enable_image: bool = False,
) -> dict[str, Any]:
    zh = (scene.get("image_prompt_zh") or "").strip()
    en = (scene.get("image_prompt_en") or "").strip()
    img_prompt = en or zh
    url = None
    if session_enable_image and settings.llm_api_key and img_prompt:
        with span("image_gen", "wanx"):
            url = synthesize_image_url(settings, img_prompt)
    raw_mem = scene.get("memory_updates", [])
    mem_list = raw_mem if isinstance(raw_mem, list) else []
    return {
        "interaction_hint": scene.get("interaction_hint", ""),
        "image_prompt_zh": zh,
        "image_prompt_en": en,
        "image_url": url,
        "field": scene.get("field", {}),
        "memory_updates": mem_list,
    }


def _render_character_status_panel(
    paths: Any,
    session_name: str,
    character: str,
    settings: Settings,
    chapter: int,
) -> None:
    """Render character status panel on the right side."""
    st.markdown("### 🎭 角色状态")
    
    char_status = st.session_state.get("_char_status")
    if not char_status:
        st.caption("开场后显示角色状态")
        return
    
    # Character name
    st.markdown(f"**{char_status.get('character_name', character)}**")
    
    # Attributes
    attrs = char_status.get("attributes", {})
    if attrs:
        st.markdown("**属性**")
        for key, val in attrs.items():
            # Display progress bar for numeric attributes
            if isinstance(val, (int, float)) and key.lower() in (
                "health", "spirit", "sanity", "qi", "energy", "hp", "mp",
                "体力", "精神", "精神值", "生命", "生命值", "灵气", "真气",
            ):
                max_val = 100
                pct = min(100, max(0, int(val / max_val * 100)))
                st.progress(pct / 100, text=f"{key}: {val}")
            else:
                st.caption(f"{key}: {val}")
    
    # Status effects
    effects = char_status.get("status_effects", [])
    if effects:
        st.markdown("**状态**")
        status_str = " · ".join(effects)
        st.caption(status_str)
    
    # Inventory
    inventory = char_status.get("inventory", [])
    if inventory:
        with st.expander(f"🎒 背包 ({len(inventory)})", expanded=False):
            for item in inventory:
                name = item.get("name", "未知物品")
                qty = item.get("quantity", 1)
                desc = item.get("description", "")
                if qty > 1:
                    st.caption(f"• {name} x{qty}")
                else:
                    st.caption(f"• {name}")
                if desc:
                    st.caption(f"  _{desc}_")
    
    # Skills
    skills = char_status.get("skills", [])
    if skills:
        with st.expander(f"⚡ 技能 ({len(skills)})", expanded=False):
            for skill in skills:
                st.caption(f"• {skill}")
    
    # Relationships
    rels = char_status.get("relationships", [])
    if rels:
        with st.expander(f"👥 关系 ({len(rels)})", expanded=False):
            for rel in rels:
                name = rel.get("name", "")
                attitude = rel.get("attitude", "")
                st.caption(f"• {name}: {attitude}")
    
    # Last update notes
    if char_status.get("last_update_notes"):
        st.divider()
        st.caption(f"📝 {char_status['last_update_notes']}")


def _initialize_status_if_needed(
    client: Any,
    model: str,
    paths: Any,
    session_name: str,
    character: str,
    chapter: int,
    output_lang: str,
    opening_narrative: str = "",
) -> None:
    """Initialize character status based on opening narrative text."""
    existing = load_character_status(paths, session_name)
    if existing:
        st.session_state["_char_status"] = existing
        return
    
    world_memory = {}
    if paths.world_memory_path.exists():
        try:
            world_memory = read_json(paths.world_memory_path)
        except Exception:
            pass
    
    with span("status_init", character):
        status = initialize_character_status(
            client, model,
            character_name=character,
            world_memory=world_memory,
            chapter_analysis={},
            opening_narrative=opening_narrative,
            output_lang=output_lang,
        )
    
    save_character_status(paths, session_name, status)
    st.session_state["_char_status"] = status


def _update_status_after_action(
    client: Any,
    model: str,
    paths: Any,
    session_name: str,
    user_action: str,
    narrative_result: str,
    memory_updates: list[str],
    output_lang: str,
) -> None:
    """Update character status after player action."""
    current_status = st.session_state.get("_char_status")
    if not current_status:
        return
    
    with span("status_update", "action"):
        new_status = update_character_status(
            client, model,
            current_status=current_status,
            user_action=user_action,
            narrative_result=narrative_result,
            memory_updates=memory_updates,
            output_lang=output_lang,
        )
    
    save_character_status(paths, session_name, new_status)
    st.session_state["_char_status"] = new_status
