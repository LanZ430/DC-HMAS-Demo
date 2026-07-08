from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env_str(name: str, default: str = "") -> str:
    v = os.environ.get(name)
    return v.strip() if v else default


def _env_path(name: str, default: Path) -> Path:
    v = _env_str(name)
    return Path(v).expanduser() if v else default


@dataclass(frozen=True)
class Settings:
    """Runtime configuration. Reads environment variables; does not load .env files here."""

    llm_api_key: str
    llm_base_url: str
    llm_model: str
    data_dir: Path
    foreground_budget_sec: float
    enable_image: bool
    wanx_model: str
    dashscope_api_base: str
    image_poll_interval_sec: float
    image_poll_max_sec: float
    script_phase_budget_sec: float
    demo_mode: bool

    @classmethod
    def load(cls) -> "Settings":
        # DashScope OpenAI-compatible; override via env for other providers.
        key = _env_str("LLM_API_KEY") or _env_str("DASHSCOPE_API_KEY")
        base = _env_str(
            "LLM_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        model = _env_str("LLM_MODEL", "qwen-plus")
        root = Path(__file__).resolve().parent.parent
        data = _env_path("DC_HMAS_DATA_DIR", root / "data")
        budget = float(_env_str("DC_HMAS_FOREGROUND_SEC", "180") or "180")
        enable_image = _env_str("DC_HMAS_ENABLE_IMAGE", "0").lower() in (
            "1",
            "true",
            "yes",
        )
        wanx_model = _env_str("DC_HMAS_WANX_MODEL", "wanx2.1-t2i-turbo")
        ds_base = _env_str(
            "DASHSCOPE_HTTP_BASE",
            "https://dashscope.aliyuncs.com",
        ).rstrip("/")
        poll_iv = float(_env_str("DC_HMAS_IMAGE_POLL_INTERVAL", "2") or "2")
        poll_mx = float(_env_str("DC_HMAS_IMAGE_POLL_MAX", "120") or "120")
        script_budget = float(_env_str("DC_HMAS_SCRIPT_BUDGET_SEC", "600") or "600")
        demo_mode = _env_str("DC_HMAS_DEMO", "1").lower() in ("1", "true", "yes")
        return cls(
            llm_api_key=key,
            llm_base_url=base,
            llm_model=model,
            data_dir=data,
            foreground_budget_sec=budget,
            enable_image=enable_image,
            wanx_model=wanx_model,
            dashscope_api_base=ds_base,
            image_poll_interval_sec=poll_iv,
            image_poll_max_sec=poll_mx,
            script_phase_budget_sec=script_budget,
            demo_mode=demo_mode,
        )

    def require_api_key(self) -> str:
        if not self.llm_api_key:
            raise RuntimeError(
                "Missing LLM_API_KEY (or DASHSCOPE_API_KEY). Set in environment before preprocessing."
            )
        return self.llm_api_key
