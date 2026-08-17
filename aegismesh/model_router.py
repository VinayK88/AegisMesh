from __future__ import annotations


ROUTES = {
    "extract": "compact-structured-model",
    "retrieve": "retrieval-component",
    "investigate": "reasoning-model",
    "summarize": "compact-generation-model",
    "high_impact_proposal": "reasoning-model-with-approval",
}


def route(task: str) -> dict[str, str]:
    return {
        "task": task,
        "model_class": ROUTES.get(task, "reasoning-model"),
        "adapter": "deterministic-reference-agent",
        "external_call": "false",
    }
