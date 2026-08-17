from __future__ import annotations

from .ml import recommend_model


DEFAULT_CONTEXT = {
    "complexity": 0.5,
    "evidence_count": 0,
    "graph_depth": 1,
    "risk": 0.5,
    "latency_budget_ms": 1200,
    "cost_budget": 0.05,
    "approval_required": False,
}


def route(task: str, context: dict | None = None) -> dict:
    merged = dict(DEFAULT_CONTEXT)
    merged.update(context or {})
    result = recommend_model(task, merged)
    return {
        **result,
        "adapter": "deterministic-reference-agent",
    }
