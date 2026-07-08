"""Sidebar panel showing agent status indicators."""
from __future__ import annotations

import time
from typing import Any

import streamlit as st

from dc_hmas.telemetry.agents import get_active_agents, get_event_log
from dc_hmas.ui.i18n import get_lang

# Agent definitions: (id, display_name, desc_zh, desc_en)
AGENT_ROWS: list[tuple[str, str, str, str]] = [
    ("segmenter", "📄 Segmenter", "分章切片", "Chapter segmentation"),
    ("scanner", "🔍 Scanner", "快速扫描", "Quick scan"),
    ("analyzer", "📊 Analyzer", "章节分析", "Chapter analysis"),
    ("arc_planner", "🗺️ Arc Planner", "弧/副本结构", "Arc/dungeon structure"),
    ("stylist", "🎨 Stylist", "文风锚定", "Style anchoring"),
    ("field_controller", "🎮 Field Controller", "场控规则", "Field control rules"),
    ("script_writer", "✍️ Writer", "剧本生成", "Script generation"),
    ("character_profiler", "👤 Profiler", "角色档案", "Character profiles"),
    ("perspective_adapter", "🔄 Adapter", "视角适配", "Perspective adaptation"),
    ("host", "🎭 Host", "交互叙事", "Interactive narrative"),
    ("image_gen", "🖼️ Wanx", "文生图", "Image generation"),
    ("status_init", "📋 Status Init", "角色状态初始化", "Character status init"),
    ("status_update", "🔄 Status Update", "角色状态更新", "Character status update"),
]


def render_agent_sidebar_panel() -> None:
    """Render agent status panel in sidebar."""
    lang = get_lang()
    
    st.divider()
    title = "Agent 状态" if lang == "zh" else "Agent Status"
    st.subheader(title)
    
    active = get_active_agents()
    
    if not active:
        msg = "当前无 Agent 运行中" if lang == "zh" else "No agents running"
        st.caption(msg)
    
    for aid, name, desc_zh, desc_en in AGENT_ROWS:
        desc = desc_zh if lang == "zh" else desc_en
        info = active.get(aid)
        if info:
            elapsed = time.time() - info.get("start_time", time.time())
            detail = info.get("detail", "")
            running = "运行中" if lang == "zh" else "Running"
            st.markdown(
                f":green[**●**] **{name}** · {desc}\n\n"
                f"<small style='color:gray'>{running} {elapsed:.1f}s {detail}</small>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(f":gray[○] {name} · {desc}")
    
    # Debug expander
    expander_title = "📋 最近事件日志" if lang == "zh" else "📋 Recent Events"
    with st.expander(expander_title, expanded=False):
        log = get_event_log()
        if not log:
            msg = "暂无事件记录" if lang == "zh" else "No events recorded"
            st.caption(msg)
        else:
            for row in reversed(log[-15:]):
                ts = time.strftime("%H:%M:%S", time.localtime(row["t"]))
                event = row["event"]
                icon = "🟢" if event == "start" else ("🔴" if event == "error" else "⚪")
                st.text(f"{ts} {icon} {row['agent']:<14} {event:<5} {row.get('detail', '')}")
