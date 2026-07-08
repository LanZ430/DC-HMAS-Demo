from pathlib import Path

from dc_hmas.text_encoding import (
    cjk_ratio,
    decode_text_bytes,
    detect_content_language,
    validate_chinese_text,
    validate_text_for_language,
    validation_message_for_mismatch,
)

SNIPPET = "第1章中华餐厅\n凌菁睁开眼，看到的就是这样一行字。\n中华餐厅"


def test_decode_utf8_bytes():
    data = SNIPPET.encode("utf-8")
    text, enc = decode_text_bytes(data)
    assert enc in ("utf-8", "utf-8-sig")
    assert "凌菁" in text
    assert "中华餐厅" in text


def test_decode_gbk_bytes():
    data = SNIPPET.encode("gbk")
    text, enc = decode_text_bytes(data)
    assert enc in ("gbk", "gb18030")
    assert "凌菁" in text
    assert "中华餐厅" in text


def test_utf8_ignore_produces_invalid_chinese():
    """Reproduce the bug: GBK bytes decoded as UTF-8 with ignore."""
    data = SNIPPET.encode("gbk")
    broken = data.decode("utf-8", errors="ignore")
    ok, _ = validate_chinese_text(broken)
    assert ok is False


def test_validate_real_novel_file():
    root = Path(__file__).resolve().parents[2]
    novel_path = root / "tests" / "我在末世经营中餐厅爆火.txt"
    if not novel_path.exists():
        return
    data = novel_path.read_bytes()
    text, enc = decode_text_bytes(data)
    ok, msg = validate_chinese_text(text)
    assert ok, msg
    assert "凌菁" in text[:50000]
    assert cjk_ratio(text[:10000]) > 0.2


def test_validate_language_router():
    ok, _ = validate_text_for_language(SNIPPET, "zh")
    assert ok


def test_detect_english_content():
    english = "Chapter 1\n\nThe quick brown fox jumped over the lazy dog.\n" * 50
    assert detect_content_language(english) == "en"
    ok, _ = validate_text_for_language(english, "en")
    assert ok


def test_mismatch_hint_for_english_with_zh_selected():
    english = "Chapter 1\n\nHarry Potter woke up.\n" * 100
    msg = validation_message_for_mismatch(english, "zh", ui_lang="zh")
    assert msg is not None
    assert "English" in msg or "英文" in msg
