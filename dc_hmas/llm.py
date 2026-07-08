from __future__ import annotations

from openai import OpenAI

from dc_hmas.config import Settings


def get_client(settings: Settings | None = None) -> OpenAI:
    s = settings or Settings.load()
    key = s.require_api_key()
    return OpenAI(api_key=key, base_url=s.llm_base_url)


def chat_json(
    client: OpenAI,
    model: str,
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float = 0.3,
    max_tokens: int = 2000,
) -> str:
    """Return raw assistant text (expected JSON); caller parses."""
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()


def chat_text(
    client: OpenAI,
    model: str,
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float = 0.4,
    max_tokens: int = 800,
) -> str:
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()
