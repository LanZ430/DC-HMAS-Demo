# DC-HMAS Demo

**Interactive narrative prototype** — upload a novel (`.txt`), preprocess it, then play as a character with a Host-style scene loop.

This is a **public, trimmed demo** for evaluation. It does not include sample novels or preprocessed data — bring your own UTF-8 or GBK text file.

---

## Quick Start (5 minutes)

### 1. Clone and install

```bash
git clone <your-repo-url> dc-hmas-demo
cd dc-hmas-demo
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure API key

```bash
cp .env.example .env
```

Edit `.env` and set your **DashScope / 百炼** API key:

```env
DASHSCOPE_API_KEY=your_key_here
```

Compatible OpenAI-style endpoints are supported via `LLM_BASE_URL` and `LLM_MODEL`.

### 3. Run

```bash
python start.py
```

Open **http://localhost:8501**

---

## First run walkthrough

### Preprocessing

1. Tab **Preprocessing / 预处理**
2. **Language / 语言**: `zh` for Chinese novels, `en` for English
3. Upload a `.txt` file (UTF-8 or GBK — encoding is auto-detected)
4. Wait for **文本编码检测通过** / encoding OK
5. Click **Start Preprocessing**
6. First ~3 chapters are analyzed in the foreground; the rest continue in the background

### Interactive play

1. Tab **Interactive Play / 交互体验**
2. Select your processed novel → **New Game**
3. Pick chapter, character, and theme → **Start**
4. In-game top bar:
   - **Images / 配图** — off by default
   - **Goal Mode / 目标模式** — shows system tasks + scene orientation (left panel)
   - **Guidance / 引导强度** — weak / medium / strong
5. Click **Opening**, then use the chat box for free-text actions

Left and right panels stay **fixed in the window** while you scroll the story.

---

## Requirements

| Item | Detail |
|------|--------|
| Python | 3.10+ |
| Streamlit | **≥ 1.29** (fixed side panels during play need `st.container(height=…)`) |
| LLM | Qwen via DashScope (or compatible API) |
| Disk | Preprocessed data stored under `./data/` |

---

## Switch LLM provider (no code changes)

The demo uses any **OpenAI-compatible** chat API. Edit `.env` only, then restart `python start.py`:

| Variable | Purpose |
|----------|---------|
| `LLM_API_KEY` or `DASHSCOPE_API_KEY` | API key |
| `LLM_BASE_URL` | Provider base URL |
| `LLM_MODEL` | Model name |

**Examples:**

```env
# Qwen / DashScope (default)
DASHSCOPE_API_KEY=your_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus

# OpenAI
LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini

# DeepSeek
LLM_API_KEY=...
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

No source-code edits are required to switch models.

---

## Optional: image generation

Image generation is **off by default** (text-first demo). To enable Wanx at the environment level:

```env
DC_HMAS_ENABLE_IMAGE=1
```

You can also toggle images per session in the play UI.

---

## Tests

```bash
pytest
```

---

## Project layout

```text
dc-hmas-demo/
├── start.py           # Launch Streamlit UI
├── dc_hmas/           # Application code
├── data/              # Created at runtime (gitignored)
├── tests/
└── ARCHITECTURE.md    # Brief system overview
```

---

## 中文简要说明

1. `pip install -r requirements.txt`
2. 复制 `.env.example` 为 `.env`，填入百炼 API Key
3. `python start.py`，浏览器打开 http://localhost:8501
4. **预处理**页上传 `.txt` 小说 → 开始预处理
5. **预处理**页上传 `.txt` 小说 → 开始预处理
6. **交互体验**页选角色 → 开场 → 底部输入框自由行动
7. 开启 **目标模式** 可在左侧看到系统任务与当前关注；左右侧栏固定，中间对话区滚动

---

## License

MIT — see [LICENSE](LICENSE)

---

## Sync from development tree (maintainers)

If you maintain a private full repo with `DC-HMAS/`:

```bash
python scripts/sync_from_dev.py
```

Then re-test and commit the demo repo separately (fresh history recommended for public release).
