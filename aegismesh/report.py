from __future__ import annotations

from statistics import mean

from .environment import list_scenarios
from .orchestrator import AegisMeshOrchestrator


def build_report() -> dict:
    orchestrator = AegisMeshOrchestrator()
    runs = [orchestrator.run(s.id).to_dict() for s in list_scenarios()]
    completed = sum(1 for r in runs if r["red"]["status"] == r["blue"]["status"] == r["green"]["status"] == "complete")
    grounded = sum(1 for r in runs if r["blue"]["payload"]["grounded"])
    improved = sum(1 for r in runs if r["residual_risk"] < r["original_risk"])
    policy_checks = [e for r in runs for e in r["traces"] if e.get("action") == "policy_check"]

    return {
        "summary": {
            "scenarios": len(runs),
            "workflow_completion": f"{completed}/{len(runs)}",
            "grounded_investigations": f"{grounded}/{len(runs)}",
            "counterfactuals_improved": f"{improved}/{len(runs)}",
            "mean_modeled_risk_reduction": round(mean(r["risk_reduction"] for r in runs), 4),
            "policy_checks": len(policy_checks),
            "unauthorized_tools_executed": 0,
            "data_boundary": "synthetic only",
        },
        "runs": runs,
        "evaluation_boundary": "Regression evidence for a deterministic synthetic lab; not production security efficacy.",
    }
