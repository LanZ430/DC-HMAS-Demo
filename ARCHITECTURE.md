# Architecture (Demo)

High-level flow for reviewers — not a full research specification.

## Pipeline

```text
Upload .txt
    → encoding detection (UTF-8 / GBK / GB18030)
    → chapter split
    → per-chapter LLM analysis (characters, events, summary)
    → world / plot / style memory
    → dual-script generation (DM script + player script)
    → saved under data/{novel_id}/
```

## Runtime play loop

```text
Select character + chapter
    → perspective adaptation (third-person script → first-person)
    → Host generates opening / continue scenes from:
        - player script scenes
        - agency & interaction necessity rules
        - character status
    → player free-text input
    → scene advances with Field/Host JSON output
```

## UI (immersive mode)

```text
┌─ Sticky top bar: Images | Goal Mode | Guidance ─────────────┐
├──────────┬─────────────────────────┬──────────────────────┤
│ Goal     │  Narrative + chat       │  Character status      │
│ (fixed)  │  (scrolls)              │  (fixed)               │
└──────────┴─────────────────────────┴──────────────────────┘
```

## Key modules

| Module | Role |
|--------|------|
| `preprocessing/pipeline.py` | Foreground + background analysis |
| `agents/writer.py` | Chapter analysis, scripts, world memory |
| `interaction/scene_engine.py` | Host opening / continue scenes |
| `interaction/agency.py` | Scene agency, goal panel items |
| `ui/play_tab.py` | Streamlit play experience |

## Data on disk

```text
data/{novel_id}/
├── chapters/          # split text
├── analyses/          # per-chapter JSON
├── scripts/           # dual-script JSON
├── world_memory.json
├── plot_memory.json
└── sessions/          # play saves
```

No sample data is shipped with this repo.
