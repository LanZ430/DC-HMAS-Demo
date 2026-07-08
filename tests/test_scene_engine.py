from dc_hmas.interaction.scene_engine import (
    _opening_player_script_payload,
    _ordered_player_scenes,
)


def test_ordered_player_scenes_sorts_by_order():
    script = {
        "player_script": {
            "scenes": [
                {"order": 3, "player_facing_text": "c"},
                {"order": 1, "player_facing_text": "a"},
                {"order": 2, "player_facing_text": "b"},
            ]
        }
    }
    o = _ordered_player_scenes(script)
    assert [x["player_facing_text"] for x in o] == ["a", "b", "c"]


def test_opening_payload_first_scene_only():
    script = {
        "player_script": {
            "scenes": [
                {"order": 1, "node_type": "plot", "player_facing_text": "开篇"},
                {"order": 2, "node_type": "decision", "player_facing_text": "之后"},
            ]
        }
    }
    p = _opening_player_script_payload(script)
    assert p["scene"]["player_facing_text"] == "开篇"
    assert p["total_scenes_in_chapter"] == 2
