"""Theme definitions for DC-HMAS UI."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Theme:
    """Theme configuration."""
    id: str
    name_zh: str
    name_en: str
    category: str
    description_zh: str
    description_en: str
    css: str
    is_dark: bool = False  # Whether this is a dark theme
    # Panel configuration
    status_panel_title_zh: str = "角色状态"
    status_panel_title_en: str = "Status"
    # Attribute display names (can be customized per theme)
    attr_labels: dict[str, dict[str, str]] = field(default_factory=dict)
    # Special UI elements
    has_system_log: bool = False
    has_quest_panel: bool = False
    has_cultivation_panel: bool = False


# Theme categories
THEME_CATEGORIES = {
    "modern": {"zh": "现代", "en": "Modern"},
    "ancient": {"zh": "古代", "en": "Ancient"},
    "fantasy": {"zh": "奇幻/魔幻", "en": "Fantasy"},
    "scifi": {"zh": "科幻/未来", "en": "Sci-Fi"},
}

# ============================================================================
# Base CSS - Applied to all themes to override Streamlit defaults
# ============================================================================

BASE_LIGHT_CSS = """
/* Base light theme - Override Streamlit defaults */

/* Hide Streamlit header */
[data-testid="stHeader"], header[data-testid="stHeader"] {
    display: none !important;
    height: 0 !important;
}
div[data-testid="stToolbar"] { 
    visibility: hidden !important; 
    height: 0 !important; 
}

/* Main app background */
.stApp, [data-testid="stAppViewContainer"] {
    background: var(--bg-primary) !important;
}
[data-testid="stSidebar"], [data-testid="stSidebar"] > div {
    background: var(--bg-sidebar) !important;
}
[data-testid="stSidebar"] * {
    color: var(--text-primary) !important;
}
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-secondary) !important;
    border-radius: 8px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: var(--text-secondary) !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    background: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    border-radius: 6px;
}
h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown {
    color: var(--text-primary) !important;
}
.stCaption, small {
    color: var(--text-secondary) !important;
}
[data-testid="stChatMessage"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 8px;
}
.stButton > button {
    background: var(--accent-primary) !important;
    color: var(--accent-text) !important;
    border: none !important;
}
.stButton > button:hover {
    background: var(--accent-hover) !important;
}
.stSelectbox > div > div, .stTextInput > div > div > input {
    background: var(--bg-input) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-color) !important;
}
.stProgress > div > div {
    background: var(--bg-secondary) !important;
}
.stProgress > div > div > div {
    background: var(--accent-primary) !important;
}

/* Ensure dropdowns appear above other elements */
[data-baseweb="popover"] {
    z-index: 9999 !important;
}
"""

BASE_DARK_CSS = """
/* Base dark theme - Override Streamlit defaults */

/* Hide Streamlit header */
[data-testid="stHeader"], header[data-testid="stHeader"] {
    display: none !important;
    height: 0 !important;
}
div[data-testid="stToolbar"] { 
    visibility: hidden !important; 
    height: 0 !important; 
}

/* Main app background */
.stApp, [data-testid="stAppViewContainer"] {
    background: var(--bg-primary) !important;
}
[data-testid="stSidebar"], [data-testid="stSidebar"] > div {
    background: var(--bg-sidebar) !important;
}
[data-testid="stSidebar"] *, [data-testid="stSidebar"] p, 
[data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
    color: var(--text-primary) !important;
}
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-secondary) !important;
    border-radius: 8px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: var(--text-secondary) !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border-radius: 6px;
}
h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, div {
    color: var(--text-primary) !important;
}
.stCaption, small {
    color: var(--text-secondary) !important;
}
[data-testid="stChatMessage"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 8px;
}
[data-testid="stChatMessageContent"] p {
    color: var(--text-primary) !important;
}
.stButton > button {
    background: var(--accent-primary) !important;
    color: var(--accent-text) !important;
    border: none !important;
}
.stButton > button:hover {
    background: var(--accent-hover) !important;
}
.stSelectbox > div > div, .stTextInput > div > div > input {
    background: var(--bg-input) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-color) !important;
}
.stSelectbox svg {
    fill: var(--text-primary) !important;
}
[data-baseweb="select"] * {
    color: var(--text-primary) !important;
}
.stProgress > div > div {
    background: var(--bg-secondary) !important;
}
.stProgress > div > div > div {
    background: var(--accent-primary) !important;
}

/* Ensure dropdowns appear above other elements */
[data-baseweb="popover"] {
    z-index: 9999 !important;
}
.stExpander {
    background: var(--bg-card) !important;
    border-color: var(--border-color) !important;
}
.stExpander summary span {
    color: var(--text-primary) !important;
}
div[data-testid="stToolbar"] { visibility: hidden; height: 0; }
/* Chat input */
[data-testid="stChatInput"] textarea {
    background: var(--bg-input) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-color) !important;
}
[data-testid="stChatInput"] button {
    background: var(--accent-primary) !important;
    color: var(--accent-text) !important;
}
"""

# ============================================================================
# Theme CSS Definitions - Using color palettes provided
# ============================================================================

# Palette b: #C0E1D2 #E5EEE4 #F6F4E8 #DC9B9B - Light pink-cyan (fresh, sweet)
CSS_FRESH_MINT = f"""
:root {{
    --bg-primary: #F6F4E8;
    --bg-secondary: #E5EEE4;
    --bg-sidebar: #C0E1D2;
    --bg-card: #FFFFFF;
    --bg-input: #FFFFFF;
    --text-primary: #2D3436;
    --text-secondary: #636E72;
    --border-color: #C0E1D2;
    --accent-primary: #DC9B9B;
    --accent-hover: #C88A8A;
    --accent-text: #FFFFFF;
}}
{BASE_LIGHT_CSS}
.theme-status-panel {{
    background: var(--bg-card);
    border: 2px solid var(--border-color);
    border-radius: 12px;
    padding: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}}
.theme-status-panel h3 {{
    color: #DC9B9B !important;
    border-bottom: 2px solid #C0E1D2;
    padding-bottom: 0.5rem;
}}
.theme-attr-bar {{
    background: #E5EEE4;
    border-radius: 10px;
    height: 12px;
}}
.theme-attr-fill {{
    background: linear-gradient(90deg, #DC9B9B, #C0E1D2);
    border-radius: 10px;
    height: 100%;
}}
"""

# Palette e: #F8EDE3 #BDD2B6 #A2B29F #798777 - Light yellow-green (soft)
CSS_SOFT_SAGE = f"""
:root {{
    --bg-primary: #F8EDE3;
    --bg-secondary: #BDD2B6;
    --bg-sidebar: #A2B29F;
    --bg-card: #FFFFFF;
    --bg-input: #FFFFFF;
    --text-primary: #3D3D3D;
    --text-secondary: #798777;
    --border-color: #BDD2B6;
    --accent-primary: #798777;
    --accent-hover: #6A7868;
    --accent-text: #FFFFFF;
}}
{BASE_LIGHT_CSS}
.theme-status-panel {{
    background: var(--bg-card);
    border: 2px solid #BDD2B6;
    border-radius: 12px;
    padding: 1rem;
}}
.theme-status-panel h3 {{
    color: #798777 !important;
    border-bottom: 2px solid #BDD2B6;
    padding-bottom: 0.5rem;
}}
.theme-attr-bar {{
    background: #BDD2B6;
    border-radius: 10px;
    height: 12px;
}}
.theme-attr-fill {{
    background: linear-gradient(90deg, #798777, #A2B29F);
    border-radius: 10px;
    height: 100%;
}}
"""

# Palette g: #F5EFE6 #E8DFCA #AEBDCA #7895B2 - Light yellow-blue (low-key)
CSS_CALM_BLUE = f"""
:root {{
    --bg-primary: #F5EFE6;
    --bg-secondary: #E8DFCA;
    --bg-sidebar: #AEBDCA;
    --bg-card: #FFFFFF;
    --bg-input: #FFFFFF;
    --text-primary: #2C3E50;
    --text-secondary: #7895B2;
    --border-color: #AEBDCA;
    --accent-primary: #7895B2;
    --accent-hover: #6884A1;
    --accent-text: #FFFFFF;
}}
{BASE_LIGHT_CSS}
.theme-status-panel {{
    background: var(--bg-card);
    border: 2px solid #AEBDCA;
    border-radius: 8px;
    padding: 1rem;
}}
.theme-status-panel h3 {{
    color: #7895B2 !important;
    border-bottom: 2px solid #E8DFCA;
    padding-bottom: 0.5rem;
}}
.theme-attr-bar {{
    background: #E8DFCA;
    border-radius: 8px;
    height: 12px;
}}
.theme-attr-fill {{
    background: linear-gradient(90deg, #7895B2, #AEBDCA);
    border-radius: 8px;
    height: 100%;
}}
"""

# Palette k: #222831 #393E46 #00ADB5 #EEEEEE - Dark black-cyan-white (tech)
CSS_TECH_DARK = f"""
:root {{
    --bg-primary: #222831;
    --bg-secondary: #393E46;
    --bg-sidebar: #1a1f27;
    --bg-card: #393E46;
    --bg-input: #393E46;
    --text-primary: #EEEEEE;
    --text-secondary: #B0B0B0;
    --border-color: #00ADB5;
    --accent-primary: #00ADB5;
    --accent-hover: #00CED8;
    --accent-text: #222831;
}}
{BASE_DARK_CSS}
.theme-status-panel {{
    background: #393E46;
    border: 1px solid #00ADB5;
    border-radius: 4px;
    padding: 1rem;
    box-shadow: 0 0 15px rgba(0, 173, 181, 0.15);
}}
.theme-status-panel h3 {{
    color: #00ADB5 !important;
    border-bottom: 1px solid #00ADB5;
    padding-bottom: 0.5rem;
    font-family: 'Consolas', 'Monaco', monospace;
    letter-spacing: 1px;
}}
.theme-attr-bar {{
    background: #222831;
    border: 1px solid #00ADB5;
    border-radius: 2px;
    height: 16px;
}}
.theme-attr-fill {{
    background: linear-gradient(90deg, #00ADB5, #00CED8);
    height: 100%;
}}
.system-log {{
    background: #1a1f27;
    border: 1px solid #00ADB5;
    padding: 0.5rem;
    font-size: 0.75rem;
    max-height: 150px;
    overflow-y: auto;
    color: #00ADB5 !important;
    font-family: 'Consolas', monospace;
}}
.system-log-entry {{
    border-left: 2px solid #00ADB5;
    padding-left: 8px;
    margin: 4px 0;
    color: #EEEEEE !important;
}}
"""

# Palette l: #1B262C #0F4C75 #3282B8 #BBE1FA - Dark black-blue (tech hardcore)
CSS_DEEP_BLUE = f"""
:root {{
    --bg-primary: #1B262C;
    --bg-secondary: #0F4C75;
    --bg-sidebar: #152028;
    --bg-card: #0F4C75;
    --bg-input: #0F4C75;
    --text-primary: #BBE1FA;
    --text-secondary: #8AC4E8;
    --border-color: #3282B8;
    --accent-primary: #3282B8;
    --accent-hover: #4A9FD4;
    --accent-text: #FFFFFF;
}}
{BASE_DARK_CSS}
.theme-status-panel {{
    background: #0F4C75;
    border: 1px solid #3282B8;
    border-radius: 4px;
    padding: 1rem;
}}
.theme-status-panel h3 {{
    color: #BBE1FA !important;
    border-bottom: 1px solid #3282B8;
    padding-bottom: 0.5rem;
}}
.theme-attr-bar {{
    background: #1B262C;
    border: 1px solid #3282B8;
    border-radius: 4px;
    height: 14px;
}}
.theme-attr-fill {{
    background: linear-gradient(90deg, #3282B8, #BBE1FA);
    border-radius: 4px;
    height: 100%;
}}
"""

# Palette c: #F9F7F7 #DBE2EF #3F72AF #112D4E - Blue-white tech
CSS_TECH_BLUE = f"""
:root {{
    --bg-primary: #F9F7F7;
    --bg-secondary: #DBE2EF;
    --bg-sidebar: #DBE2EF;
    --bg-card: #FFFFFF;
    --bg-input: #FFFFFF;
    --text-primary: #112D4E;
    --text-secondary: #3F72AF;
    --border-color: #3F72AF;
    --accent-primary: #3F72AF;
    --accent-hover: #112D4E;
    --accent-text: #FFFFFF;
}}
{BASE_LIGHT_CSS}
.theme-status-panel {{
    background: var(--bg-card);
    border: 2px solid #3F72AF;
    border-radius: 8px;
    padding: 1rem;
}}
.theme-status-panel h3 {{
    color: #3F72AF !important;
    border-bottom: 2px solid #DBE2EF;
    padding-bottom: 0.5rem;
}}
.theme-attr-bar {{
    background: #DBE2EF;
    border-radius: 6px;
    height: 12px;
}}
.theme-attr-fill {{
    background: linear-gradient(90deg, #3F72AF, #112D4E);
    border-radius: 6px;
    height: 100%;
}}
"""

# Palette a: #346739 #79AE6F #9FCB98 #F2EDC2 - Dark yellow-green (neutral, stable)
CSS_FOREST_GREEN = f"""
:root {{
    --bg-primary: #F2EDC2;
    --bg-secondary: #9FCB98;
    --bg-sidebar: #79AE6F;
    --bg-card: #FFFEF5;
    --bg-input: #FFFFFF;
    --text-primary: #2D3B2D;
    --text-secondary: #346739;
    --border-color: #79AE6F;
    --accent-primary: #346739;
    --accent-hover: #2A5530;
    --accent-text: #FFFFFF;
}}
{BASE_LIGHT_CSS}
[data-testid="stSidebar"] *, [data-testid="stSidebar"] p {{
    color: #FFFFFF !important;
}}
.theme-status-panel {{
    background: var(--bg-card);
    border: 2px solid #79AE6F;
    border-radius: 8px;
    padding: 1rem;
    background-image: linear-gradient(135deg, transparent 40%, rgba(159, 203, 152, 0.1) 100%);
}}
.theme-status-panel h3 {{
    color: #346739 !important;
    border-bottom: 2px solid #9FCB98;
    padding-bottom: 0.5rem;
    font-family: 'STKaiti', 'KaiTi', serif;
}}
.theme-attr-bar {{
    background: #9FCB98;
    border-radius: 10px;
    height: 14px;
}}
.theme-attr-fill {{
    background: linear-gradient(90deg, #346739, #79AE6F);
    border-radius: 10px;
    height: 100%;
}}
.cultivation-realm {{
    text-align: center;
    padding: 1rem;
    background: linear-gradient(135deg, rgba(52, 103, 57, 0.1), transparent);
    border: 2px solid #79AE6F;
    border-radius: 50%;
    margin: 0.5rem auto;
    width: 80px;
    height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #346739 !important;
}}
"""

# Palette f: #FFB6B9 #FAE3D9 #BBDED6 #61C0BF - Light blue-pink (vibrant)
CSS_CORAL_TEAL = f"""
:root {{
    --bg-primary: #FAE3D9;
    --bg-secondary: #BBDED6;
    --bg-sidebar: #61C0BF;
    --bg-card: #FFFFFF;
    --bg-input: #FFFFFF;
    --text-primary: #2D3436;
    --text-secondary: #636E72;
    --border-color: #61C0BF;
    --accent-primary: #FFB6B9;
    --accent-hover: #FF9A9E;
    --accent-text: #2D3436;
}}
{BASE_LIGHT_CSS}
[data-testid="stSidebar"] *, [data-testid="stSidebar"] p {{
    color: #FFFFFF !important;
}}
.theme-status-panel {{
    background: var(--bg-card);
    border: 2px solid #61C0BF;
    border-radius: 16px;
    padding: 1rem;
}}
.theme-status-panel h3 {{
    color: #61C0BF !important;
    border-bottom: 2px solid #BBDED6;
    padding-bottom: 0.5rem;
}}
.theme-attr-bar {{
    background: #BBDED6;
    border-radius: 10px;
    height: 12px;
}}
.theme-attr-fill {{
    background: linear-gradient(90deg, #FFB6B9, #61C0BF);
    border-radius: 10px;
    height: 100%;
}}
"""

# Palette i: #427AB5 #406AAF #F7DD7D #FFE8BE - Dark blue-yellow (formal)
CSS_ROYAL_BLUE = f"""
:root {{
    --bg-primary: #FFE8BE;
    --bg-secondary: #F7DD7D;
    --bg-sidebar: #427AB5;
    --bg-card: #FFFFFF;
    --bg-input: #FFFFFF;
    --text-primary: #1A365D;
    --text-secondary: #406AAF;
    --border-color: #427AB5;
    --accent-primary: #406AAF;
    --accent-hover: #365A8F;
    --accent-text: #FFFFFF;
}}
{BASE_LIGHT_CSS}
[data-testid="stSidebar"] *, [data-testid="stSidebar"] p {{
    color: #FFFFFF !important;
}}
.theme-status-panel {{
    background: var(--bg-card);
    border: 3px double #427AB5;
    border-radius: 4px;
    padding: 1.2rem;
    position: relative;
}}
.theme-status-panel::before {{
    content: '';
    position: absolute;
    top: 6px; right: 6px; bottom: 6px; left: 6px;
    border: 1px solid #F7DD7D;
    pointer-events: none;
}}
.theme-status-panel h3 {{
    color: #406AAF !important;
    text-align: center;
    font-family: 'Georgia', serif;
}}
.theme-attr-bar {{
    background: #F7DD7D;
    border-radius: 4px;
    height: 14px;
}}
.theme-attr-fill {{
    background: linear-gradient(90deg, #406AAF, #427AB5);
    border-radius: 4px;
    height: 100%;
}}
"""

# Wuxia/Martial Arts - Dark with gold accents
CSS_WUXIA = f"""
:root {{
    --bg-primary: #1a1510;
    --bg-secondary: #2a2018;
    --bg-sidebar: #0f0a05;
    --bg-card: #2a2018;
    --bg-input: #2a2018;
    --text-primary: #e8dcc0;
    --text-secondary: #c9a227;
    --border-color: #8b6914;
    --accent-primary: #c9a227;
    --accent-hover: #dab32f;
    --accent-text: #1a1510;
}}
{BASE_DARK_CSS}
.theme-status-panel {{
    background: #2a2018;
    border: 1px solid #8b6914;
    border-top: 3px solid #8b2500;
    padding: 1rem;
}}
.theme-status-panel h3 {{
    color: #c9a227 !important;
    font-family: 'STKaiti', 'KaiTi', serif;
    text-align: center;
}}
.theme-attr-bar {{
    background: #1a1510;
    height: 14px;
    border: 1px solid #8b6914;
}}
.theme-attr-fill {{
    background: linear-gradient(90deg, #8b2500, #c9a227);
    height: 100%;
}}
"""

# Fantasy Magic - Purple glow
CSS_FANTASY = f"""
:root {{
    --bg-primary: #1a1a2e;
    --bg-secondary: #16213e;
    --bg-sidebar: #0f0f1a;
    --bg-card: #16213e;
    --bg-input: #16213e;
    --text-primary: #e8e8f0;
    --text-secondary: #c77dff;
    --border-color: #4a3b6b;
    --accent-primary: #9d4edd;
    --accent-hover: #b366e8;
    --accent-text: #FFFFFF;
}}
{BASE_DARK_CSS}
.theme-status-panel {{
    background: linear-gradient(135deg, #16213e, #1a1a30);
    border: 1px solid #4a3b6b;
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 0 30px rgba(157, 78, 221, 0.2);
}}
.theme-status-panel h3 {{
    color: #c77dff !important;
    text-shadow: 0 0 10px #9d4edd;
}}
.theme-attr-bar {{
    background: #0f0f1a;
    border: 1px solid #4a3b6b;
    border-radius: 4px;
    height: 16px;
}}
.theme-attr-fill {{
    background: linear-gradient(90deg, #9d4edd, #c77dff);
    box-shadow: 0 0 8px #9d4edd;
    border-radius: 4px;
    height: 100%;
}}
"""

# Cyberpunk - Neon pink/cyan
CSS_CYBERPUNK = f"""
:root {{
    --bg-primary: #0d0221;
    --bg-secondary: #1a0a3e;
    --bg-sidebar: #08011a;
    --bg-card: #1a0a3e;
    --bg-input: #1a0a3e;
    --text-primary: #f0e6ff;
    --text-secondary: #00ffff;
    --border-color: #ff00ff;
    --accent-primary: #ff00ff;
    --accent-hover: #ff66ff;
    --accent-text: #0d0221;
}}
{BASE_DARK_CSS}
.theme-status-panel {{
    background: rgba(26, 10, 62, 0.9);
    border: 2px solid #ff00ff;
    border-radius: 0;
    padding: 1rem;
    box-shadow: 0 0 30px rgba(255, 0, 255, 0.3), inset 0 0 20px rgba(0, 255, 255, 0.1);
}}
.theme-status-panel h3 {{
    color: #00ffff !important;
    text-shadow: 0 0 10px #00ffff;
    text-transform: uppercase;
    letter-spacing: 3px;
}}
.theme-attr-bar {{
    background: #0d0221;
    border: 1px solid #ff00ff;
    height: 18px;
}}
.theme-attr-fill {{
    background: linear-gradient(90deg, #ff00ff, #00ffff);
    box-shadow: 0 0 10px #00ffff;
    height: 100%;
}}
.system-log {{
    background: #08011a;
    border: 1px solid #ff00ff;
    padding: 0.5rem;
    font-family: 'Consolas', monospace;
    color: #00ffff !important;
}}
.system-log-entry {{
    border-left: 2px solid #ff00ff;
    padding-left: 8px;
    margin: 4px 0;
    color: #f0e6ff !important;
}}
"""

# Palette h: #96B6C5 #ADC4CE #EEE0C9 #F1F0E8 - Soft blue-cream
CSS_SOFT_OCEAN = f"""
:root {{
    --bg-primary: #F1F0E8;
    --bg-secondary: #EEE0C9;
    --bg-sidebar: #96B6C5;
    --bg-card: #FFFFFF;
    --bg-input: #FFFFFF;
    --text-primary: #3D4F5F;
    --text-secondary: #6B8A9A;
    --border-color: #ADC4CE;
    --accent-primary: #96B6C5;
    --accent-hover: #7FA5B6;
    --accent-text: #FFFFFF;
}}
{BASE_LIGHT_CSS}
[data-testid="stSidebar"] *, [data-testid="stSidebar"] p {{
    color: #FFFFFF !important;
}}
.theme-status-panel {{
    background: var(--bg-card);
    border: 2px solid #ADC4CE;
    border-radius: 12px;
    padding: 1rem;
}}
.theme-status-panel h3 {{
    color: #6B8A9A !important;
    border-bottom: 2px solid #EEE0C9;
    padding-bottom: 0.5rem;
}}
.theme-attr-bar {{
    background: #EEE0C9;
    border-radius: 10px;
    height: 12px;
}}
.theme-attr-fill {{
    background: linear-gradient(90deg, #96B6C5, #ADC4CE);
    border-radius: 10px;
    height: 100%;
}}
"""

# Medieval - Parchment style
CSS_MEDIEVAL = f"""
:root {{
    --bg-primary: #2c2416;
    --bg-secondary: #3d3225;
    --bg-sidebar: #1a150e;
    --bg-card: #3d3225;
    --bg-input: #3d3225;
    --text-primary: #d4c4a8;
    --text-secondary: #c9a227;
    --border-color: #6b5a3e;
    --accent-primary: #c9a227;
    --accent-hover: #dab32f;
    --accent-text: #2c2416;
}}
{BASE_DARK_CSS}
.theme-status-panel {{
    background: #3d3225;
    border: 3px solid #6b5a3e;
    border-radius: 0;
    padding: 1rem;
    position: relative;
}}
.theme-status-panel::after {{
    content: '';
    position: absolute;
    top: 4px; right: 4px; bottom: 4px; left: 4px;
    border: 1px solid #c9a227;
    pointer-events: none;
}}
.theme-status-panel h3 {{
    color: #c9a227 !important;
    font-family: 'Georgia', serif;
    text-align: center;
}}
.theme-attr-bar {{
    background: #2c2416;
    border: 1px solid #6b5a3e;
    height: 14px;
}}
.theme-attr-fill {{
    background: linear-gradient(90deg, #8b2500, #c9a227);
    height: 100%;
}}
"""

# ============================================================================
# Theme Definitions
# ============================================================================

THEMES: dict[str, Theme] = {
    # --- Modern Light ---
    "fresh_mint": Theme(
        id="fresh_mint",
        name_zh="清新薄荷",
        name_en="Fresh Mint",
        category="modern",
        description_zh="粉青色系，清新甜美",
        description_en="Pink-cyan palette, fresh and sweet",
        css=CSS_FRESH_MINT,
        is_dark=False,
    ),
    "soft_sage": Theme(
        id="soft_sage",
        name_zh="柔和青绿",
        name_en="Soft Sage",
        category="modern",
        description_zh="黄绿色系，柔和自然",
        description_en="Yellow-green palette, soft and natural",
        css=CSS_SOFT_SAGE,
        is_dark=False,
    ),
    "calm_blue": Theme(
        id="calm_blue",
        name_zh="宁静蓝调",
        name_en="Calm Blue",
        category="modern",
        description_zh="黄蓝色系，低调沉稳",
        description_en="Yellow-blue palette, calm and stable",
        css=CSS_CALM_BLUE,
        is_dark=False,
    ),
    "soft_ocean": Theme(
        id="soft_ocean",
        name_zh="柔和海洋",
        name_en="Soft Ocean",
        category="modern",
        description_zh="蓝黄色系，柔和模糊",
        description_en="Blue-cream palette, soft and muted",
        css=CSS_SOFT_OCEAN,
        is_dark=False,
    ),
    
    # --- Ancient/Classical ---
    "forest_green": Theme(
        id="forest_green",
        name_zh="仙侠青林",
        name_en="Forest Green",
        category="ancient",
        description_zh="黄绿色系，古典修仙风格",
        description_en="Yellow-green palette, classical cultivation style",
        css=CSS_FOREST_GREEN,
        is_dark=False,
        status_panel_title_zh="修炼境界",
        status_panel_title_en="Cultivation",
        has_cultivation_panel=True,
    ),
    "royal_blue": Theme(
        id="royal_blue",
        name_zh="皇家蓝金",
        name_en="Royal Blue",
        category="ancient",
        description_zh="蓝黄色系，典雅正式",
        description_en="Blue-yellow palette, elegant and formal",
        css=CSS_ROYAL_BLUE,
        is_dark=False,
        status_panel_title_zh="人物属性",
        status_panel_title_en="Character",
    ),
    "wuxia": Theme(
        id="wuxia",
        name_zh="武侠江湖",
        name_en="Wuxia",
        category="ancient",
        description_zh="深色金棕，江湖侠客风",
        description_en="Dark gold-brown, martial arts world",
        css=CSS_WUXIA,
        is_dark=True,
        status_panel_title_zh="侠客属性",
        status_panel_title_en="Martial Status",
        has_quest_panel=True,
    ),
    "medieval": Theme(
        id="medieval",
        name_zh="中世纪",
        name_en="Medieval",
        category="ancient",
        description_zh="羊皮纸风格，西方古典",
        description_en="Parchment style, Western classical",
        css=CSS_MEDIEVAL,
        is_dark=True,
        has_quest_panel=True,
    ),
    
    # --- Fantasy ---
    "fantasy_magic": Theme(
        id="fantasy_magic",
        name_zh="魔幻紫光",
        name_en="Fantasy Magic",
        category="fantasy",
        description_zh="紫色光效，魔法世界",
        description_en="Purple glow, magical world",
        css=CSS_FANTASY,
        is_dark=True,
        has_quest_panel=True,
    ),
    "coral_teal": Theme(
        id="coral_teal",
        name_zh="珊瑚青绿",
        name_en="Coral Teal",
        category="fantasy",
        description_zh="蓝粉色系，活泼鲜明",
        description_en="Blue-pink palette, vibrant and bright",
        css=CSS_CORAL_TEAL,
        is_dark=False,
    ),
    
    # --- Sci-Fi ---
    "tech_dark": Theme(
        id="tech_dark",
        name_zh="科技暗黑",
        name_en="Tech Dark",
        category="scifi",
        description_zh="黑青白色调，科技终端风",
        description_en="Black-cyan-white, tech terminal style",
        css=CSS_TECH_DARK,
        is_dark=True,
        status_panel_title_zh="【系统面板】",
        status_panel_title_en="[SYSTEM]",
        has_system_log=True,
    ),
    "deep_blue": Theme(
        id="deep_blue",
        name_zh="深邃蓝海",
        name_en="Deep Blue",
        category="scifi",
        description_zh="黑蓝色调，科技硬核",
        description_en="Black-blue palette, tech hardcore",
        css=CSS_DEEP_BLUE,
        is_dark=True,
        has_system_log=True,
    ),
    "tech_blue": Theme(
        id="tech_blue",
        name_zh="科技蓝白",
        name_en="Tech Blue",
        category="scifi",
        description_zh="蓝白色系，现代科技风",
        description_en="Blue-white palette, modern tech style",
        css=CSS_TECH_BLUE,
        is_dark=False,
    ),
    "cyberpunk": Theme(
        id="cyberpunk",
        name_zh="赛博朋克",
        name_en="Cyberpunk",
        category="scifi",
        description_zh="霓虹粉青，未来都市",
        description_en="Neon pink-cyan, future city",
        css=CSS_CYBERPUNK,
        is_dark=True,
        has_system_log=True,
    ),
}


def get_theme(theme_id: str) -> Theme | None:
    """Get theme by ID."""
    return THEMES.get(theme_id)


def get_theme_css(theme_id: str) -> str:
    """Get CSS for a theme."""
    theme = THEMES.get(theme_id)
    return theme.css if theme else ""


def get_themes_by_category(category: str) -> list[Theme]:
    """Get all themes in a category."""
    return [t for t in THEMES.values() if t.category == category]


def suggest_theme_from_genre(genre_tags: list[str]) -> str:
    """Suggest a theme based on genre tags."""
    tags_lower = [t.lower() for t in genre_tags]
    tags_str = " ".join(tags_lower)
    
    # Infinite flow / system
    if any(k in tags_str for k in ["无限流", "infinite", "副本", "dungeon", "系统", "system"]):
        return "tech_dark"
    
    # Cyberpunk / Sci-fi
    if any(k in tags_str for k in ["赛博", "cyber", "未来", "future", "科幻", "scifi"]):
        return "cyberpunk"
    
    # Xianxia
    if any(k in tags_str for k in ["修仙", "修真", "仙侠", "cultivation", "xianxia", "immortal"]):
        return "forest_green"
    
    # Wuxia
    if any(k in tags_str for k in ["武侠", "江湖", "wuxia", "martial"]):
        return "wuxia"
    
    # Fantasy / Magic
    if any(k in tags_str for k in ["魔幻", "奇幻", "fantasy", "magic", "魔法"]):
        return "fantasy_magic"
    
    # Medieval
    if any(k in tags_str for k in ["中世纪", "medieval", "骑士", "knight"]):
        return "medieval"
    
    # Chinese classical
    if any(k in tags_str for k in ["宫廷", "古代", "历史", "palace", "historical", "古风"]):
        return "royal_blue"
    
    # Default to fresh mint
    return "fresh_mint"
