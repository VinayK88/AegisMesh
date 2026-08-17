from __future__ import annotations

import time
from contextlib import contextmanager


TRACE_STORE: dict[str, list[dict]] = {}


class TraceCollector:
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.events: list[dict] = []

    @contextmanager
    def step(self, agent: str, action: str):
        started = time.perf_counter()
        event = {"agent": agent, "action": action, "status": "started"}
        try:
            yield event
            event["status"] = "ok"
        except Exception as exc:
            event["status"] = "error"
            event["error"] = type(exc).__name__
            raise
        finally:
            event["latency_ms"] = round((time.perf_counter() - started) * 1000, 3)
            self.events.append(event)

    def record_policy(self, agent: str, tool: str, allowed: bool, reason: str) -> None:
        self.events.append({
            "agent": agent,
            "action": "policy_check",
            "tool": tool,
            "allowed": allowed,
            "reason": reason,
        })

    def persist(self) -> None:
        TRACE_STORE[self.run_id] = [dict(event) for event in self.events]


def get_trace(run_id: str) -> list[dict] | None:
    trace = TRACE_STORE.get(run_id)
    return [dict(event) for event in trace] if trace is not None else None
