from dc_hmas.interaction.agency import resolve_scene_objectives
from dc_hmas.interaction.session_store import (
    DEFAULT_SESSION_SETTINGS,
    normalize_session_settings,
    update_session_settings,
)
from dc_hmas.memory.paths import NovelPaths


def test_normalize_session_settings_defaults():
    assert normalize_session_settings(None) == DEFAULT_SESSION_SETTINGS
    assert normalize_session_settings({"guidance_level": "invalid"})["guidance_level"] == "medium"


def test_normalize_session_settings_merge():
    merged = normalize_session_settings({"goal_mode": True, "guidance_level": "strong"})
    assert merged["goal_mode"] is True
    assert merged["guidance_level"] == "strong"
    assert merged["enable_image"] is False


def test_resolve_scene_objectives_from_hooks(tmp_path):
    scene = {
        "scene_id": "ch001_sc02",
        "node_type": "decision",
        "interaction_hooks": "Malfoy has taken Neville's Remembrall.",
        "decision_prompt": "You may choose how to respond.",
    }
    objs = resolve_scene_objectives(scene, guidance_level="medium", output_lang="en")
    assert len(objs) == 1
    assert "respond" in objs[0]["description"]


def test_resolve_scene_objectives_weak_returns_empty():
    scene = {"interaction_hooks": "Look around."}
    assert resolve_scene_objectives(scene, guidance_level="weak") == []


def test_resolve_scene_objectives_explicit_list():
    scene = {
        "objectives": [
            {"id": "a", "title": "Find the key", "visibility": "player", "status": "active"},
            {"id": "b", "title": "Secret", "visibility": "dm_only", "status": "active"},
        ]
    }
    objs = resolve_scene_objectives(scene, guidance_level="medium")
    assert len(objs) == 1
    assert objs[0]["title"] == "Find the key"


def test_update_session_settings_persists(tmp_path):
    root = tmp_path / "novel"
    paths = NovelPaths(novel_root=root)
    root.mkdir(parents=True)
    from dc_hmas.interaction.session_store import create_new_session

    name = create_new_session(paths, 1, "Harry")
    updated = update_session_settings(paths, name, goal_mode=True, enable_image=True)
    assert updated["goal_mode"] is True
    assert updated["enable_image"] is True
