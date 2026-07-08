"""Detect and decode novel text bytes (UTF-8, GBK/GB18030, BOM variants)."""
from __future__ import annotations

import re

_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")

# Common chapter markers — used to sanity-check decoded Chinese fiction.
_ZH_CHAPTER_MARKERS = (
    "第",
    "章",
    "节",
    "回",
    "卷",
)


def cjk_char_count(text: str) -> int:
    return len(_CJK_RE.findall(text))


def cjk_ratio(text: str) -> float:
    n = len(text)
    if n == 0:
        return 0.0
    return cjk_char_count(text) / n


def mojibake_score(text: str) -> float:
    """Higher values suggest UTF-8/GBK mismatch or replacement-character loss."""
    if not text:
        return 0.0
    bad = 0
    for c in text:
        if c == "\ufffd":
            bad += 2
        elif "\u0080" <= c <= "\u00ff":
            bad += 1
        elif "\u0100" <= c <= "\u024f":
            bad += 1
    return bad / len(text)


def _chapter_marker_hits(text: str) -> int:
    sample = text[:50000]
    return sum(sample.count(m) for m in _ZH_CHAPTER_MARKERS)


def _latin_alpha_ratio(text: str) -> float:
    if not text:
        return 0.0
    return sum(1 for c in text if c.isascii() and c.isalpha()) / len(text)


def _score_decoding(text: str, *, expect_chinese: bool) -> float:
    moji = mojibake_score(text)
    if expect_chinese:
        ratio = cjk_ratio(text)
        score = ratio * 10.0 - moji * 8.0
        score += min(_chapter_marker_hits(text), 20) * 0.05
        return score
    alpha = _latin_alpha_ratio(text)
    return alpha * 10.0 - moji * 8.0


def decode_text_bytes(data: bytes, *, expect_chinese: bool = True) -> tuple[str, str]:
    """
    Decode uploaded novel bytes with encoding detection.

    Returns (text, encoding_label).
    """
    if not data:
        return "", "empty"

    if data.startswith(b"\xef\xbb\xbf"):
        text = data[3:].decode("utf-8")
        return text, "utf-8-sig"

    if len(data) >= 2 and data.startswith(b"\xff\xfe"):
        return data.decode("utf-16-le"), "utf-16-le"
    if len(data) >= 2 and data.startswith(b"\xfe\xff"):
        return data.decode("utf-16-be"), "utf-16-be"

    candidates: list[tuple[str, str, float]] = []
    encodings = ("utf-8", "gb18030", "gbk", "big5") if expect_chinese else ("utf-8", "latin-1", "cp1252")
    for enc in encodings:
        try:
            text = data.decode(enc)
        except UnicodeDecodeError:
            continue
        candidates.append((enc, text, _score_decoding(text, expect_chinese=expect_chinese)))

    if not candidates:
        return data.decode("utf-8", errors="replace"), "utf-8-replace"

    best_enc, best_text, _ = max(candidates, key=lambda item: item[2])
    return best_text, best_enc


def validate_chinese_text(
    text: str,
    *,
    min_cjk_ratio: float = 0.04,
    sample_size: int = 20000,
) -> tuple[bool, str]:
    """Return (ok, message). Fails fast on obvious mojibake."""
    if not text or not text.strip():
        return False, "文件内容为空"

    sample = text[:sample_size]
    ratio = cjk_ratio(sample)
    if ratio < min_cjk_ratio:
        return False, f"中文字符占比过低 ({ratio:.1%})，疑似编码错误"

    moji = mojibake_score(sample)
    if moji > 0.025 and ratio < 0.15:
        return False, f"检测到乱码特征 (异常字符 {moji:.1%})，请勿使用 errors=ignore 强转 UTF-8"

    if _chapter_marker_hits(sample) == 0 and ratio < 0.08:
        return False, "未找到常见章节标记且中文占比偏低，请确认文件编码"

    return True, "ok"


def validate_english_text(text: str, *, min_alpha_ratio: float = 0.35) -> tuple[bool, str]:
    if not text or not text.strip():
        return False, "File is empty"
    sample = text[:20000]
    alpha = sum(1 for c in sample if c.isalpha()) / max(len(sample), 1)
    if alpha < min_alpha_ratio:
        return False, f"Low alphabetic ratio ({alpha:.1%}), possible encoding error"
    if mojibake_score(sample) > 0.04:
        return False, "Suspected mojibake in English text"
    return True, "ok"


def latin_alpha_ratio(text: str) -> float:
    return _latin_alpha_ratio(text)


def detect_content_language(text: str, sample_size: int = 12000) -> str:
    """Heuristic: zh | en | unknown."""
    sample = (text or "")[:sample_size]
    if not sample.strip():
        return "unknown"
    cjk = cjk_ratio(sample)
    alpha = _latin_alpha_ratio(sample)
    if cjk >= 0.06:
        return "zh"
    if alpha >= 0.35:
        return "en"
    return "unknown"


def validate_text_for_language(text: str, language: str) -> tuple[bool, str]:
    if language == "zh":
        return validate_chinese_text(text)
    return validate_english_text(text)


def validation_message_for_mismatch(
    text: str,
    selected_language: str,
    *,
    ui_lang: str = "zh",
) -> str | None:
    """Return a user-facing hint when selected language does not match file content."""
    detected = detect_content_language(text)
    if detected == "unknown" or detected == selected_language:
        return None
    if ui_lang == "zh":
        if detected == "en" and selected_language == "zh":
            return "文件内容主要为英文，请先将上方「语言」切换为 English (en)。"
        if detected == "zh" and selected_language == "en":
            return "文件内容主要为中文，请先将「语言」切换为 中文 (zh)。"
    else:
        if detected == "en" and selected_language == "zh":
            return "File appears to be English — switch Language to English (en) above."
        if detected == "zh" and selected_language == "en":
            return "File appears to be Chinese — switch Language to 中文 (zh) above."
    return None
