"""Viewport-fixed play layout CSS (side panels stay visible while scrolling)."""


def play_viewport_css(*, goal_on: bool) -> str:
    """
    Fixed-to-viewport side panels (not page-sticky).

    Left + right panels use position:fixed so they remain visible when the
    center narrative column scrolls. Center column gets horizontal margins
    so content is not covered.
    """
    layout_class = "dc-hmas-layout-three" if goal_on else "dc-hmas-layout-two"
    return f"""
<style>
:root {{
  --dc-hmas-top: 4.5rem;
  --dc-hmas-panel-w: min(18vw, 280px);
  --dc-hmas-sidebar-w: 21rem;
}}

section.main .block-container {{
  max-width: min(96vw, 1920px) !important;
}}

/* Reserve horizontal space in the play row */
section.main [data-testid="stHorizontalBlock"]:has(.{layout_class}) > div[data-testid="column"] {{
  align-self: flex-start;
}}

/* --- Right panel: fixed to viewport --- */
section.main [data-testid="stHorizontalBlock"]:has(.{layout_class})
  > div[data-testid="column"]:has(.dc-hmas-right-panel-marker) {{
  position: fixed !important;
  top: var(--dc-hmas-top) !important;
  right: max(0.75rem, calc((100vw - min(96vw, 1920px)) / 2 + 0.25rem)) !important;
  width: var(--dc-hmas-panel-w) !important;
  max-height: calc(100vh - var(--dc-hmas-top) - 0.75rem) !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  z-index: 250 !important;
  background: var(--background-color, #0e1117) !important;
  padding: 0.25rem 0.5rem 0.75rem 0.25rem !important;
  box-sizing: border-box !important;
}}

/* --- Left panel (goal mode): fixed to viewport --- */
section.main [data-testid="stHorizontalBlock"]:has(.dc-hmas-layout-three)
  > div[data-testid="column"]:has(.dc-hmas-left-panel-marker) {{
  position: fixed !important;
  top: var(--dc-hmas-top) !important;
  left: calc(var(--dc-hmas-sidebar-w) + max(0.75rem, calc((100vw - min(96vw, 1920px)) / 2))) !important;
  width: var(--dc-hmas-panel-w) !important;
  max-height: calc(100vh - var(--dc-hmas-top) - 0.75rem) !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  z-index: 250 !important;
  background: var(--background-color, #0e1117) !important;
  padding: 0.25rem 0.25rem 0.75rem 0.5rem !important;
  box-sizing: border-box !important;
}}

/* Spacer width so center column does not expand under fixed panels */
section.main [data-testid="stHorizontalBlock"]:has(.dc-hmas-layout-three)
  > div[data-testid="column"]:has(.dc-hmas-left-panel-marker),
section.main [data-testid="stHorizontalBlock"]:has(.{layout_class})
  > div[data-testid="column"]:has(.dc-hmas-right-panel-marker) {{
  min-height: 120px;
  flex: 0 0 var(--dc-hmas-panel-w) !important;
  max-width: var(--dc-hmas-panel-w) !important;
}}

/* Center narrative column */
section.main [data-testid="stHorizontalBlock"]:has(.{layout_class})
  > div[data-testid="column"]:has(.dc-hmas-main-col-marker) {{
  flex: 1 1 auto !important;
  min-width: 0 !important;
  max-width: none !important;
}}

section.main [data-testid="stHorizontalBlock"]:has(.dc-hmas-layout-three)
  > div[data-testid="column"]:has(.dc-hmas-main-col-marker) {{
  margin-left: 0.5rem !important;
  margin-right: 0.5rem !important;
}}

section.main [data-testid="stHorizontalBlock"]:has(.dc-hmas-layout-two)
  > div[data-testid="column"]:has(.dc-hmas-main-col-marker) {{
  margin-right: calc(var(--dc-hmas-panel-w) + 1rem) !important;
}}

/* Collapsed Streamlit sidebar — shift left panel inward */
@media (max-width: 768px) {{
  :root {{ --dc-hmas-sidebar-w: 5rem; --dc-hmas-panel-w: min(28vw, 220px); }}
}}
</style>
"""
