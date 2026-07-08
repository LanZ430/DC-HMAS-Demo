from __future__ import annotations

import json
import logging
import os
import re
import statistics
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# 约每多少字一块（20 万字 → ~20 块）。可用环境变量 DC_HMAS_CHARS_PER_PART 覆盖。
_DEFAULT_CHARS_PER_PART = 10_000

# 仅当匹配到这些「强」标记模式时才考虑按标记切分（避免 \d+. 等误伤正文）
_STRONG_KEYS_ZH: frozenset[str] = frozenset(
    {
        "chinese_num",
        "chinese_digit",
        "chinese_num_section",
        "chinese_digit_section",
        "chinese_num_part",
        "chinese_digit_part",
        "episode",
        "title_vol",
    }
)
_STRONG_KEYS_EN: frozenset[str] = frozenset(
    {
        "english_lower",
        "english_upper",
        "english_part_lower",
        "english_part_upper",
    }
)


def _chars_per_part() -> int:
    raw = os.environ.get("DC_HMAS_CHARS_PER_PART", "").strip()
    if not raw:
        return _DEFAULT_CHARS_PER_PART
    try:
        return max(2000, int(raw))
    except ValueError:
        return _DEFAULT_CHARS_PER_PART


def split_into_chapters(
    content: str,
    language: str = "zh",
    *,
    chars_per_part: int | None = None,
) -> list[str]:
    """
    将全书正文切成多块。

    - 默认：按字符大致均分（每块约 ``chars_per_part`` 字，遇换行优先断句）。
    - 若检测到高置信的章节标记（如「第N章」且块长度合理），则按标记切分。
    """
    content = (content or "").strip()
    if not content:
        return []

    cpp = int(chars_per_part) if chars_per_part is not None else _chars_per_part()
    picked = _pick_strong_marker_pattern(content, language)
    if picked is not None:
        pattern_name, pattern = picked
        marker_chapters = _split_with_pattern(content, pattern)
        if marker_chapters and _marker_split_trustworthy(marker_chapters, len(content)):
            logger.info("Chapter split: marker-based (%s), %s parts", pattern_name, len(marker_chapters))
            return marker_chapters

    n = max(1, (len(content) + cpp - 1) // cpp)
    parts = _even_split_by_chars(content, n)
    logger.info("Chapter split: even-by-chars (~%s chars/part), %s parts", cpp, len(parts))
    return parts


def _build_chapter_patterns(language: str) -> dict[str, str]:
    if language == "zh":
        return {
            "chinese_num": r"第[一二三四五六七八九十百千]+章",
            "chinese_digit": r"第\d+章",
            "chinese_num_section": r"第[一二三四五六七八九十百千]+节",
            "chinese_digit_section": r"第\d+节",
            "chinese_num_part": r"第[一二三四五六七八九十百千]+回",
            "chinese_digit_part": r"第\d+回",
            "mixed": r"第.+章.*\n",
            "chinese_dot": r"[一二三四五六七八九十]+[\.、]",
            "number_dot": r"\d+[\.、]",
            "title_vol": r"【[^】]+】",
            "episode": r"第\d+话|第[一二三四五六七八九十百千]+话",
        }
    return {
        "english_lower": r"chapter\s+\d+",
        "english_upper": r"CHAPTER\s+\d+",
        "english_part_lower": r"part\s+\d+",
        "english_part_upper": r"PART\s+\d+",
        "number_dot": r"\d+[\.、]",
        "star_line": r"\*{3,}.*\*{3,}",
        "dash_line": r"-{3,}.*-{3,}",
    }


def _pick_strong_marker_pattern(content: str, language: str) -> tuple[str, str] | None:
    """若在正文中「强」章节标记至少出现 2 次，返回 (模式名, 正则)；否则不做标记切分。"""
    patterns = _build_chapter_patterns(language)
    strong = _STRONG_KEYS_ZH if language == "zh" else _STRONG_KEYS_EN
    counts: dict[str, int] = {}
    for name, pat in patterns.items():
        if name not in strong:
            continue
        counts[name] = len(re.findall(pat, content, re.IGNORECASE | re.MULTILINE))

    candidates = [k for k in counts if counts[k] >= 2]
    if not candidates:
        return None
    best = max(candidates, key=lambda k: counts[k])
    return best, patterns[best]


def _split_with_pattern(content: str, pattern: str) -> list[str]:
    chapter_splits = re.split(f"({pattern})", content)
    current_title: str | None = None
    current_body: list[str] = []
    chapters: list[str] = []

    for part in chapter_splits:
        if not part.strip():
            continue
        if re.search(pattern, part):
            if current_title is not None:
                text = current_title + "\n\n" + "\n".join(current_body)
                chapters.append(text.strip())
            current_title = part.strip()
            current_body = []
        else:
            current_body.append(part.strip())

    if current_title is not None:
        text = current_title + "\n\n" + "\n".join(current_body)
        chapters.append(text.strip())

    return [c for c in chapters if c]


def _marker_split_trustworthy(chapters: list[str], total_len: int) -> bool:
    if not chapters:
        return False
    lens = [len(c) for c in chapters]
    tiny = sum(1 for L in lens if L < 200)
    ratio_tiny = tiny / len(chapters)

    if total_len <= 12_000:
        if len(chapters) < 2:
            return True
        return bool(min(lens) >= 15 and ratio_tiny <= 0.5)

    if len(chapters) < 2:
        return False
    if ratio_tiny > 0.25:
        return False
    if statistics.median(lens) < 300:
        return False
    if len(chapters) > max(40, total_len // 80):
        return False
    return True


def _even_split_by_chars(content: str, num_parts: int) -> list[str]:
    """按字符数均分，边界附近优先找换行。"""
    n = max(1, num_parts)
    total = len(content)
    if n <= 1 or total == 0:
        return [content]

    parts: list[str] = []
    start = 0
    for i in range(1, n):
        ideal = (total * i) // n
        low = max(start + 1, ideal - 2000)
        high = min(total, ideal + 2000)
        cut = _find_break_point(content, low, high, total)
        parts.append(content[start:cut].strip())
        start = cut
    parts.append(content[start:].strip())
    return [p for p in parts if p]


def _find_break_point(content: str, low: int, high: int, total: int) -> int:
    """在 [low, high) 内优先选 \\n\\n，其次 \\n，否则 midpoint。"""
    if high <= low:
        return min(low, total)
    window = content[low:high]
    pp = window.rfind("\n\n")
    if pp != -1:
        return low + pp + 2
    p1 = window.rfind("\n")
    if p1 != -1:
        return low + p1 + 1
    return min(high, total)


def save_chapters(chapters_dir: Path, chapters: list[str]) -> None:
    chapters_dir.mkdir(parents=True, exist_ok=True)
    for i, ch in enumerate(chapters):
        path = chapters_dir / f"chapter_{i + 1:03d}.txt"
        path.write_text(ch, encoding="utf-8")


def load_chapter(chapters_dir: Path, chapter_num: int) -> str:
    path = chapters_dir / f"chapter_{chapter_num:03d}.txt"
    return path.read_text(encoding="utf-8")


def truncate_chapter_for_llm(text: str, head: int = 4000, tail: int = 1200) -> str:
    if len(text) <= head + tail:
        return text
    return text[:head] + "\n...\n" + text[-tail:]


def parse_json_loose(raw: str) -> Any:
    """Parse JSON from LLM output, stripping markdown fences if present."""
    s = raw.strip()
    if s.startswith("```json"):
        s = s.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    elif s.startswith("```"):
        s = s.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", s)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        repaired = _repair_truncated_json(s)
        if repaired is not None:
            return json.loads(repaired)
        raise


def _repair_truncated_json(s: str) -> str | None:
    """Best-effort repair for truncated or slightly malformed LLM JSON."""
    start = s.find("{")
    if start < 0:
        return None
    fragment = s[start:]

    # Drop trailing incomplete string (odd number of unescaped quotes at end)
    fragment = re.sub(r',?\s*"[^"]*$', "", fragment)
    fragment = re.sub(r",\s*$", "", fragment.rstrip())

    opens = {"{": "}", "[": "]"}
    closers = {v: k for k, v in opens.items()}
    stack: list[str] = []
    in_string = False
    escape = False

    for ch in fragment:
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in opens:
            stack.append(ch)
        elif ch in closers:
            if stack and stack[-1] == closers[ch]:
                stack.pop()

    suffix = "".join(opens[c] for c in reversed(stack))
    candidate = fragment + suffix
    try:
        json.loads(candidate)
        return candidate
    except json.JSONDecodeError:
        return None
