"""Preprocessing orchestration (phase A/B/C)."""

from dc_hmas.preprocessing.pipeline import (
    ForegroundResult,
    phase_a_segment_only,
    run_foreground_preprocessing,
    start_background_chapter_analysis,
)

__all__ = [
    "ForegroundResult",
    "phase_a_segment_only",
    "run_foreground_preprocessing",
    "start_background_chapter_analysis",
]
