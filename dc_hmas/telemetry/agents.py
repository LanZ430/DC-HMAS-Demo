"""Agent telemetry: track which agents are currently active."""
from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from typing import Any, Callable

# Thread-safe storage for active agents
_lock = threading.Lock()
_active: dict[str, dict[str, Any]] = {}  # agent_id -> {start_time, detail}
_event_log: list[dict[str, Any]] = []  # Recent events for debugging

# Optional listener callback: (agent_id, event, detail) -> None
AgentListener = Callable[[str, str, str | None], Any]
_listener: AgentListener | None = None


def set_listener(fn: AgentListener | None) -> None:
    global _listener
    _listener = fn


def emit(agent_id: str, event: str, detail: str | None = None) -> None:
    """Emit an agent event (start/end/error)."""
    global _active, _event_log
    now = time.time()
    
    with _lock:
        row = {"t": now, "agent": agent_id, "event": event, "detail": detail or ""}
        _event_log.append(row)
        _event_log[:] = _event_log[-50:]  # Keep last 50 events
        
        if event == "start":
            _active[agent_id] = {"start_time": now, "detail": detail}
        elif event in ("end", "error"):
            _active.pop(agent_id, None)
    
    if _listener:
        try:
            _listener(agent_id, event, detail)
        except Exception:
            pass


def get_active_agents() -> dict[str, dict[str, Any]]:
    """Return currently active agents with their start times."""
    with _lock:
        return dict(_active)


def get_event_log() -> list[dict[str, Any]]:
    """Return recent event log for debugging."""
    with _lock:
        return list(_event_log)


@contextmanager
def span(agent_id: str, detail: str | None = None):
    """Context manager to track agent execution span."""
    emit(agent_id, "start", detail)
    try:
        yield
    except BaseException:
        emit(agent_id, "error", detail)
        raise
    finally:
        emit(agent_id, "end", detail)
