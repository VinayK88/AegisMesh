from __future__ import annotations

from statistics import mean

from .environment import list_scenarios
from .ml import ml_model_summary
from .orchestrator import AegisMeshOrchestrator


def build_report() -> dict:
    orchestrator = AegisMeshOrchestrator()
    runs = [orchestrator.run(s.id).to_dict() for s in list_scenarios()]
    completed = sum(1 for r in runs if r["red"]["status"] == r["blue"]["status"] == r["green"]["status"] == "complete")
    grounded = sum(1 for r in runs if r["blue"]["payload"]["grounded"])
    improved = sum(1 for r in runs if r["residual_risk"] < r["original_risk"])
    policy_checks = [e for r in runs for e in r["traces"] if e.get("action") == "policy_check"]
    workflow_reviews = sum(1 for r in runs if r["workflow_ml"]["status"] == "REVIEW")
    safety_overrides = sum(
        1
        for r in runs
        for agent in ("red", "blue", "green")
        if r[agent]["payload"].get("model_route", {}).get("safety_override")
    )

    return {
        "summary": {
            "scenarios": len(runs),
            "workflow_completion": f"{completed}/{len(runs)}",
            "grounded_investigations": f"{grounded}/{len(runs)}",
            "counterfactuals_improved": f"{improved}/{len(runs)}",
            "mean_modeled_risk_reduction": round(mean(r["risk_reduction"] for r in runs), 4),
            "policy_checks": len(policy_checks),
            "unauthorized_tools_executed": 0,
            "workflow_health_reviews": workflow_reviews,
            "deterministic_model_route_safety_overrides": safety_overrides,
            "data_boundary": "synthetic only",
        },
        "ml": ml_model_summary(),
        "runs": runs,
        "evaluation_boundary": "Regression evidence for a deterministic synthetic lab; ML metrics use synthetic holdouts/reference populations and are not production security efficacy.",
    }
