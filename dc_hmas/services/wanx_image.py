from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from typing import Any

from dc_hmas.config import Settings

logger = logging.getLogger(__name__)


def synthesize_image_url(settings: Settings, prompt: str) -> str | None:
    """Async Wanx task: submit + poll. Returns HTTPS URL or None on failure."""
    if not settings.llm_api_key or not prompt.strip():
        return None
    key = settings.llm_api_key
    base = settings.dashscope_api_base
    url_create = f"{base}/api/v1/services/aigc/text2image/image-synthesis"
    body = {
        "model": settings.wanx_model,
        "input": {"prompt": prompt[:2000]},
        "parameters": {"size": "1024*1024", "n": 1},
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url_create,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "X-DashScope-Async": "enable",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        logger.warning("Wanx submit failed: %s", e)
        return None

    task_id = (payload.get("output") or {}).get("task_id")
    if not task_id:
        logger.warning("Wanx no task_id: %s", payload)
        return None

    task_url = f"{base}/api/v1/tasks/{task_id}"
    deadline = time.monotonic() + settings.image_poll_max_sec
    while time.monotonic() < deadline:
        time.sleep(settings.image_poll_interval_sec)
        t_req = urllib.request.Request(
            task_url,
            method="GET",
            headers={"Authorization": f"Bearer {key}"},
        )
        try:
            with urllib.request.urlopen(t_req, timeout=60) as tr:
                task_payload: dict[str, Any] = json.loads(tr.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            logger.warning("Wanx poll failed: %s", e)
            return None

        out = task_payload.get("output") or {}
        status = out.get("task_status") or task_payload.get("task_status")
        if status == "SUCCEEDED":
            results = out.get("results") or []
            if results and isinstance(results[0], dict):
                u = results[0].get("url")
                if u:
                    return str(u)
            url = out.get("image_url") or out.get("url")
            if url:
                return str(url)
            logger.warning("Wanx success but no url: %s", task_payload)
            return None
        if status in ("FAILED", "UNKNOWN"):
            logger.warning("Wanx task ended bad: %s", task_payload)
            return None
    logger.warning("Wanx poll timeout task=%s", task_id)
    return None
