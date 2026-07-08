"""Internationalization (i18n) for DC-HMAS UI."""
from __future__ import annotations

import streamlit as st

# UI Text translations
UI_TEXT = {
    # Main app
    "app_title": {"zh": "DC-HMAS", "en": "DC-HMAS"},
    "app_subtitle": {"zh": "预处理 · 交互叙事 · 多模态（文生图）", "en": "Preprocessing · Interactive Narrative · Multimodal"},
    "tab_preprocess": {"zh": "预处理", "en": "Preprocessing"},
    "tab_play": {"zh": "交互体验", "en": "Interactive Play"},
    "tab_notes": {"zh": "说明", "en": "Help"},
    
    # Sidebar
    "sidebar_env": {"zh": "环境", "en": "Environment"},
    "sidebar_model": {"zh": "对话模型", "en": "Model"},
    "sidebar_image": {"zh": "文生图", "en": "Image Gen"},
    "sidebar_on": {"zh": "开", "en": "On"},
    "sidebar_off": {"zh": "关", "en": "Off"},
    "sidebar_budget": {"zh": "前台预算", "en": "Foreground Budget"},
    "sidebar_api_ok": {"zh": "API Key 已配置", "en": "API Key configured"},
    "sidebar_api_missing": {"zh": "未配置 LLM_API_KEY / DASHSCOPE_API_KEY", "en": "LLM_API_KEY / DASHSCOPE_API_KEY not configured"},
    "sidebar_game_active": {"zh": "🎮 游戏进行中", "en": "🎮 Game in Progress"},
    "sidebar_switch_tab": {"zh": "切换到「预处理」Tab 可查看完整侧边栏", "en": "Switch to 'Preprocessing' tab for full sidebar"},
    
    # Preprocessing
    "prep_title": {"zh": "预处理", "en": "Preprocessing"},
    "prep_lang": {"zh": "语言", "en": "Language"},
    "prep_book_title": {"zh": "书名 / 标识（用于存档名）", "en": "Book Title / ID (for archive name)"},
    "prep_upload": {"zh": "上传 .txt 小说全文", "en": "Upload .txt novel file"},
    "prep_info": {
        "zh": "上传 UTF-8 文本后开始「分章 + 前台分析」。交互页可读取已生成的存档。\n\n💡 **并行处理**：预处理在后台运行，你可以随时切换到「交互体验」Tab 与已处理的小说互动。",
        "en": "Upload UTF-8 text to start 'segmentation + foreground analysis'. The interaction page can read generated archives.\n\n💡 **Parallel Processing**: Preprocessing runs in the background, you can switch to 'Interactive Play' tab to interact with processed novels anytime."
    },
    "prep_last_progress": {"zh": "上次本会话的预处理进度：", "en": "Last preprocessing progress in this session:"},
    "prep_start_full": {"zh": "🚀 开始预处理", "en": "🚀 Start Preprocessing"},
    "prep_api_missing": {"zh": "请先设置 API Key", "en": "Please set API Key first"},
    "prep_segmenting": {"zh": "分章与写入目录…", "en": "Segmenting and writing..."},
    "prep_analyzing": {"zh": "前台 LLM 分析（含无限流弧）…", "en": "Foreground LLM analysis (including infinite flow arcs)..."},
    "prep_bg_processing": {"zh": "📊 后台正在处理 {count} 个任务: {names}", "en": "📊 Background processing {count} task(s): {names}"},
    "prep_done_fast": {"zh": "✅ 分章完成 ({count} 章)，后台开始全量分析。可切换到「交互体验」Tab。", "en": "✅ Segmentation complete ({count} chapters), background analysis started. Switch to 'Interactive Play' tab."},
    "prep_bg_continue": {"zh": "后台线程继续分析第 {start}–{end} 章…可切换到「交互体验」Tab。", "en": "Background thread continues analyzing chapters {start}–{end}... Switch to 'Interactive Play' tab."},
    "prep_progress": {"zh": "进度", "en": "Progress"},
    
    # Play tab
    "play_title": {"zh": "交互体验", "en": "Interactive Play"},
    "play_no_archives": {"zh": "暂无预处理存档。请先在「预处理」页上传并处理小说。", "en": "No preprocessed archives. Please upload and process a novel in 'Preprocessing' tab first."},
    "play_output_lang": {"zh": "🌐 输出语言", "en": "🌐 Output Language"},
    "play_select_novel": {"zh": "📚 选择已处理的小说", "en": "📚 Select processed novel"},
    "play_invalid_path": {"zh": "存档路径无效", "en": "Invalid archive path"},
    "play_chapter": {"zh": "📖 第 {num} 章", "en": "📖 Chapter {num}"},
    "play_character": {"zh": "🎭 {name}", "en": "🎭 {name}"},
    "play_exit": {"zh": "🔄 退出", "en": "🔄 Exit"},
    "play_exit_help": {"zh": "返回存档选择", "en": "Return to archive selection"},
    "play_mode": {"zh": "🎮 游玩模式", "en": "🎮 Play Mode"},
    "play_new_game": {"zh": "🆕 开始新游戏", "en": "🆕 New Game"},
    "play_continue": {"zh": "📂 继续已有存档 ({count} 个)", "en": "📂 Continue ({count} saves)"},
    "play_select_save": {"zh": "选择存档", "en": "Select Save"},
    "play_save_chapter": {"zh": "存档章节: 第 {num} 章", "en": "Save chapter: Chapter {num}"},
    "play_save_character": {"zh": "扮演角色: {name}", "en": "Character: {name}"},
    "play_btn_continue": {"zh": "▶️ 继续游戏", "en": "▶️ Continue Game"},
    "play_select_chapter": {"zh": "📖 选择章节", "en": "📖 Select Chapter"},
    "play_select_character": {"zh": "🎭 扮演角色", "en": "🎭 Play as"},
    "play_char_hint": {"zh": "本章出现角色: {names}", "en": "Characters in this chapter: {names}"},
    "play_char_hint_none": {"zh": "无角色数据，请手动输入", "en": "No character data, please enter manually"},
    "play_btn_start": {"zh": "🎬 开始新游戏", "en": "🎬 Start New Game"},
    "play_select_theme": {"zh": "🎨 选择界面主题", "en": "🎨 Select Theme"},
    "play_theme_suggest": {"zh": "💡 根据小说类型推荐: {name}", "en": "💡 Suggested based on genre: {name}"},
    "play_image_on": {"zh": "✅ 已开启文生图（百炼 Wanx）", "en": "✅ Image generation enabled (Wanx)"},
    "play_image_off": {"zh": "⚪ 未开启配图：设置 DC_HMAS_ENABLE_IMAGE=1", "en": "⚪ Image generation disabled: Set DC_HMAS_ENABLE_IMAGE=1"},
    "play_btn_opening": {"zh": "🎬 开场（生成本章第一个场景）", "en": "🎬 Opening (Generate first scene)"},
    "play_need_api": {"zh": "需要 LLM API Key", "en": "LLM API Key required"},
    "play_generating": {"zh": "生成叙事与配图（若开启）……", "en": "Generating narrative and image (if enabled)..."},
    "play_adapting_perspective": {"zh": "适配角色视角……", "en": "Adapting to character perspective..."},
    "play_continuing": {"zh": "推进剧情与配图（若开启）……", "en": "Advancing story and image (if enabled)..."},
    "play_input_hint": {"zh": "输入行动、台词或选择…", "en": "Enter action, dialogue or choice..."},
    "play_image_caption": {"zh": "场景配图（Wanx）", "en": "Scene image (Wanx)"},
    "play_image_prompt": {"zh": "画面提示词", "en": "Image prompt"},
    "play_hint": {"zh": "💡 提示：{hint}", "en": "💡 Hint: {hint}"},
    "play_save_details": {"zh": "💾 当前存档详情", "en": "💾 Current Save Details"},
    "play_save_name": {"zh": "存档名", "en": "Save name"},
    "play_save_path": {"zh": "路径", "en": "Path"},

    # Session control bar
    "ctrl_image": {"zh": "配图", "en": "Images"},
    "ctrl_goal_mode": {"zh": "目标模式", "en": "Goal Mode"},
    "ctrl_guidance": {"zh": "引导强度", "en": "Guidance"},
    "ctrl_guidance_weak": {"zh": "弱", "en": "Weak"},
    "ctrl_guidance_medium": {"zh": "中", "en": "Med"},
    "ctrl_guidance_strong": {"zh": "强", "en": "Strong"},
    "ctrl_image_session_on": {"zh": "本会话已开启配图", "en": "Images ON for this session"},
    "ctrl_image_session_off": {"zh": "本会话未开启配图", "en": "Images OFF for this session"},
    "ctrl_image_need_key": {"zh": "需要 API Key 才能生图", "en": "API Key required for images"},

    # Objectives panel
    "objectives_title": {"zh": "🎯 当前关注", "en": "🎯 Current Focus"},
    "objectives_system_title": {"zh": "📋 系统任务", "en": "📋 System Tasks"},
    "objectives_empty": {"zh": "暂无明确目标，自由探索即可。", "en": "No active objective — explore freely."},
    "objectives_untitled": {"zh": "探索提示", "en": "Orientation"},
    
    # Theme
    "theme_preview": {"zh": "预览效果", "en": "Preview"},
    "theme_dark": {"zh": "深色主题", "en": "Dark Theme"},
    "theme_light": {"zh": "浅色主题", "en": "Light Theme"},
    "theme_hp": {"zh": "生命值", "en": "HP"},
    "theme_sp": {"zh": "精神值", "en": "SP"},
    
    # Status panel
    "status_title": {"zh": "角色状态", "en": "Status"},
    "status_wait": {"zh": "开场后显示角色状态", "en": "Status will appear after opening"},
    "status_attrs": {"zh": "属性", "en": "Attributes"},
    "status_effects": {"zh": "状态", "en": "Status"},
    "status_inventory": {"zh": "🎒 背包", "en": "🎒 Inventory"},
    "status_skills": {"zh": "⚡ 技能", "en": "⚡ Skills"},
    "status_relations": {"zh": "👥 关系", "en": "👥 Relations"},
    
    # Notes tab
    "notes_content": {
        "zh": """
**交互**：选择 `data/` 下已预处理的存档，选定章节与扮演角色后点「开场」，再用底部输入框推进剧情。

**配图**：在 `.env` 或环境中设置 `DC_HMAS_ENABLE_IMAGE=1`，并确保 API Key 已开通通义万相；否则仅展示模型生成的画面提示词。

**主题**：开始新游戏时可选择界面主题，系统会根据小说类型自动推荐。

**存档**：每轮对话写入 `data/{novel_id}/sessions/` 目录，包含主题设置。
""",
        "en": """
**Interaction**: Select a preprocessed archive from `data/`, choose chapter and character, click 'Opening', then use the input box at the bottom to advance the story.

**Image**: Set `DC_HMAS_ENABLE_IMAGE=1` in `.env` or environment, and ensure API Key has Wanx enabled; otherwise only the generated image prompt will be shown.

**Theme**: Select UI theme when starting a new game. System will recommend based on novel type.

**Save**: Each turn is saved to `data/{novel_id}/sessions/` directory, including theme settings.
"""
    },
}


def t(key: str, lang: str = None, **kwargs) -> str:
    """Get translated text for given key.
    
    Args:
        key: Translation key
        lang: Language code ('zh' or 'en'). If None, uses session state.
        **kwargs: Format arguments for the string
    
    Returns:
        Translated string
    """
    if lang is None:
        lang = st.session_state.get("_output_lang", "zh")
    
    texts = UI_TEXT.get(key, {})
    text = texts.get(lang, texts.get("zh", key))
    
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def get_lang() -> str:
    """Get current UI language."""
    return st.session_state.get("_output_lang", "zh")
