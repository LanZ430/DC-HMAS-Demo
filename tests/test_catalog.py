from pathlib import Path

from dc_hmas.catalog import discover_novels


def test_discover_novels(tmp_path: Path):
    (tmp_path / "n1").mkdir()
    (tmp_path / "n1" / "document_info.json").write_text(
        '{"document_id":"n1","title":"t","total_chapters":3}', encoding="utf-8"
    )
    rows = discover_novels(tmp_path)
    assert len(rows) == 1
    assert rows[0]["_novel_id"] == "n1"
