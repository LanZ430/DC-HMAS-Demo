from dc_hmas.interaction.agency import resolve_goal_panel_items


def test_goal_panel_includes_system_status_effects():
    scene = {
        "scene_id": "ch001_sc05",
        "node_type": "decision",
        "decision_prompt": "如何促成首次交易？",
    }
    char_status = {
        "status_effects": [
            "末日经营系统已绑定",
            "每日营收任务倒计时中",
            "暴露于含微量毒素的荒原环境",
        ],
    }
    world = {
        "quick_scan": {"genre_tags": ["末世", "系统", "经营"]},
        "infinite_flow": {
            "arcs": [{
                "arc_id": "arc_001",
                "title": "新手立足",
                "chapter_span_estimate": "1-25",
                "entry_signals": ["系统发布新手交易任务与每日经营额考核"],
            }],
        },
    }
    items = resolve_goal_panel_items(
        scene=scene,
        guidance_level="medium",
        output_lang="zh",
        char_status=char_status,
        world=world,
        chapter_num=1,
    )
    titles = " ".join(i["title"] for i in items)
    assert "末日经营系统已绑定" in titles
    assert "每日营收任务倒计时中" in titles
    assert any(i["type"] == "quest" for i in items)
    assert any(i["type"] != "quest" for i in items)
