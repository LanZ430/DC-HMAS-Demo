"""Themed panel rendering for DC-HMAS UI."""
from __future__ import annotations

from typing import Any

import streamlit as st

from dc_hmas.ui.i18n import t
from dc_hmas.ui.themes.definitions import Theme, get_theme


def _render_objective_list(objectives: list[dict[str, Any]], output_lang: str) -> None:
    for obj in objectives:
        if not isinstance(obj, dict):
            continue
        status = obj.get("status", "active")
        icon = "✅" if status == "completed" else "⏳" if status == "active" else "🔒"
        name = obj.get("title") or obj.get("name") or t("objectives_untitled", lang=output_lang)
        desc = (obj.get("description") or "").strip()
        st.markdown(f"**{icon} {name}**")
        if desc:
            st.caption(desc)


def render_objectives_panel(
    objectives: list[dict[str, Any]] | None,
    output_lang: str = "zh",
    *,
    theme: Theme | None = None,
) -> None:
    """Read-only goal/orientation panel (not an action menu)."""
    if theme:
        st.markdown('<div class="theme-status-panel theme-objectives-panel">', unsafe_allow_html=True)
    else:
        st.markdown('<div class="theme-objectives-panel">', unsafe_allow_html=True)

    quests = [o for o in (objectives or []) if o.get("type") == "quest"]
    orientations = [o for o in (objectives or []) if o.get("type") != "quest"]

    if quests:
        st.markdown(f"### {t('objectives_system_title', lang=output_lang)}")
        _render_objective_list(quests, output_lang)
        if orientations:
            st.markdown("---")

    if orientations:
        st.markdown(f"### {t('objectives_title', lang=output_lang)}")
        _render_objective_list(orientations, output_lang)

    if not quests and not orientations:
        st.markdown(f"### {t('objectives_title', lang=output_lang)}")
        st.caption(t("objectives_empty", lang=output_lang))

    st.markdown("</div>", unsafe_allow_html=True)


def render_themed_status_panel(
    theme: Theme,
    char_status: dict[str, Any] | None,
    character: str,
    output_lang: str = "zh",
    system_logs: list[str] | None = None,
    *,
    goal_mode: bool = False,
    objectives: list[dict[str, Any]] | None = None,
) -> None:
    """Render character status panel with theme styling."""
    # Panel title
    title = theme.status_panel_title_zh if output_lang == "zh" else theme.status_panel_title_en
    
    # Start themed panel container
    st.markdown(f'<div class="theme-status-panel">', unsafe_allow_html=True)
    st.markdown(f"<h3>{title}</h3>", unsafe_allow_html=True)
    
    if not char_status:
        st.caption(t("status_wait", lang=output_lang))
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    # Character name
    char_name = char_status.get("character_name", character)
    st.markdown(f"**{char_name}**")
    
    # Special cultivation display for xianxia
    if theme.has_cultivation_panel:
        _render_cultivation_realm(char_status, theme, output_lang)
    
    # Attributes
    attrs = char_status.get("attributes", {})
    if attrs:
        _render_attributes(attrs, theme, output_lang)
    
    # Status effects
    effects = char_status.get("status_effects", [])
    if effects:
        st.markdown(f"**{t('status_effects', lang=output_lang)}**")
        status_str = " · ".join(effects)
        st.caption(status_str)
    
    # System log for infinite flow style
    if theme.has_system_log and system_logs:
        _render_system_log(system_logs, output_lang)
    
    # Quest panel for RPG styles (legacy char_status quests when goal mode off)
    if theme.has_quest_panel and not goal_mode:
        quests = char_status.get("quests", [])
        if quests:
            _render_quest_panel(quests, output_lang)
    
    # Inventory
    inventory = char_status.get("inventory", [])
    if inventory:
        _render_inventory(inventory, output_lang)
    
    # Skills
    skills = char_status.get("skills", [])
    if skills:
        _render_skills(skills, output_lang)
    
    # Relationships
    rels = char_status.get("relationships", [])
    if rels:
        _render_relationships(rels, output_lang)
    
    # Last update notes
    if char_status.get("last_update_notes"):
        st.divider()
        st.caption(f"📝 {char_status['last_update_notes']}")
    
    st.markdown('</div>', unsafe_allow_html=True)


def _render_cultivation_realm(
    char_status: dict[str, Any],
    theme: Theme,
    output_lang: str,
) -> None:
    """Render cultivation realm display for xianxia theme."""
    attrs = char_status.get("attributes", {})
    realm = attrs.get("cultivation") or attrs.get("境界") or attrs.get("realm")
    if realm:
        st.markdown(
            f'<div class="cultivation-realm"><span style="font-size:0.9rem;">{realm}</span></div>',
            unsafe_allow_html=True,
        )


def _render_attributes(
    attrs: dict[str, Any],
    theme: Theme,
    output_lang: str,
) -> None:
    """Render character attributes with themed progress bars."""
    st.markdown(f"**{t('status_attrs', lang=output_lang)}**")
    
    bar_attrs = {
        "health", "spirit", "sanity", "qi", "energy", "hp", "mp",
        "体力", "精神", "精神值", "生命", "生命值", "灵气", "真气",
        "理智", "san", "mana",
    }
    
    for key, val in attrs.items():
        # Get display label from theme or use key
        if key in theme.attr_labels:
            display_key = theme.attr_labels[key].get(output_lang, key)
        else:
            display_key = key
        
        # Render as progress bar or text
        if isinstance(val, (int, float)) and key.lower() in bar_attrs:
            max_val = 100
            pct = min(100, max(0, int(val / max_val * 100)))
            # Custom themed progress bar
            st.markdown(
                f"""
                <div style="margin: 4px 0;">
                    <small>{display_key}: {val}</small>
                    <div class="theme-attr-bar">
                        <div class="theme-attr-fill" style="width: {pct}%"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.caption(f"{display_key}: {val}")


def _render_system_log(logs: list[str], output_lang: str) -> None:
    """Render system log panel for infinite flow style."""
    label = "【系统日志】" if output_lang == "zh" else "[SYSTEM LOG]"
    st.markdown(f"**{label}**")
    
    log_html = '<div class="system-log">'
    for log in logs[-5:]:  # Show last 5 entries
        log_html += f'<div class="system-log-entry">{log}</div>'
    log_html += '</div>'
    
    st.markdown(log_html, unsafe_allow_html=True)


def _render_quest_panel(quests: list[dict[str, Any]], output_lang: str) -> None:
    """Render quest/task panel."""
    label = "任务" if output_lang == "zh" else "Quests"
    with st.expander(f"📜 {label} ({len(quests)})", expanded=True):
        for quest in quests:
            name = quest.get("name", "未知任务" if output_lang == "zh" else "Unknown")
            status = quest.get("status", "进行中" if output_lang == "zh" else "In Progress")
            icon = "✅" if status in ("完成", "completed") else "⏳"
            st.caption(f"{icon} {name}")


def _render_inventory(inventory: list[dict[str, Any]], output_lang: str) -> None:
    """Render inventory panel."""
    label = t("status_inventory", lang=output_lang).replace("🎒 ", "")
    with st.expander(f"🎒 {label} ({len(inventory)})", expanded=False):
        for item in inventory:
            name = item.get("name", "未知物品" if output_lang == "zh" else "Unknown")
            qty = item.get("quantity", 1)
            desc = item.get("description", "")
            if qty > 1:
                st.caption(f"• {name} x{qty}")
            else:
                st.caption(f"• {name}")
            if desc:
                st.caption(f"  _{desc}_")


def _render_skills(skills: list[str], output_lang: str) -> None:
    """Render skills panel."""
    label = t("status_skills", lang=output_lang).replace("⚡ ", "")
    with st.expander(f"⚡ {label} ({len(skills)})", expanded=False):
        for skill in skills:
            st.caption(f"• {skill}")


def _render_relationships(rels: list[dict[str, Any]], output_lang: str) -> None:
    """Render relationships panel."""
    label = t("status_relations", lang=output_lang).replace("👥 ", "")
    with st.expander(f"👥 {label} ({len(rels)})", expanded=False):
        for rel in rels:
            name = rel.get("name", "")
            attitude = rel.get("attitude", "")
            st.caption(f"• {name}: {attitude}")


def render_theme_selector(
    current_theme_id: str,
    suggested_theme_id: str | None = None,
    output_lang: str = "zh",
) -> str | None:
    """
    Render theme selection UI.
    Returns selected theme ID or None if unchanged.
    """
    from dc_hmas.ui.themes.definitions import THEMES, THEME_CATEGORIES
    
    label = "🎨 选择界面主题" if output_lang == "zh" else "🎨 Select Theme"
    
    # Group themes by category
    options = []
    for cat_id, cat_info in THEME_CATEGORIES.items():
        cat_name = cat_info["zh"] if output_lang == "zh" else cat_info["en"]
        for theme in THEMES.values():
            if theme.category == cat_id:
                theme_name = theme.name_zh if output_lang == "zh" else theme.name_en
                options.append((theme.id, f"{cat_name} - {theme_name}"))
    
    # Find current index
    current_idx = 0
    for i, (tid, _) in enumerate(options):
        if tid == current_theme_id:
            current_idx = i
            break
    
    # Show suggestion if different from current
    if suggested_theme_id and suggested_theme_id != current_theme_id:
        suggested_theme = THEMES.get(suggested_theme_id)
        if suggested_theme:
            sug_name = suggested_theme.name_zh if output_lang == "zh" else suggested_theme.name_en
            hint = f"💡 推荐: {sug_name}" if output_lang == "zh" else f"💡 Suggested: {sug_name}"
            st.caption(hint)
    
    selected_idx = st.selectbox(
        label,
        range(len(options)),
        index=current_idx,
        format_func=lambda i: options[i][1],
        key="theme_selector",
    )
    
    selected_id = options[selected_idx][0]
    return selected_id if selected_id != current_theme_id else None
