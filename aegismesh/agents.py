from __future__ import annotations

from dataclasses import asdict

from .environment import apply_control, path_risk
from .evidence import build_evidence_graph
from .models import AgentResult, Evidence, Scenario
from .policy import PolicyGateway
from .retrieval import retrieve


class BaseAgent:
    role = "base"

    def __init__(self, policy: PolicyGateway, trace):
        self.policy = policy
        self.trace = trace

    def _authorize(self, tool: str) -> None:
        decision = self.policy.authorize(self.role, tool)
        self.trace.record_policy(self.role, tool, decision.allowed, decision.reason)
        if not decision.allowed:
            raise PermissionError(decision.reason)


class RedAgent(BaseAgent):
    role = "red"

    def run(self, scenario: Scenario) -> AgentResult:
        self._authorize("select_simulated_path")
        with self.trace.step(self.role, "select_simulated_path"):
            path = [asdict(edge) for edge in scenario.path]

        self._authorize("emit_synthetic_events")
        with self.trace.step(self.role, "emit_synthetic_events"):
            evidence = [
                Evidence(
                    id=f"evt-{scenario.id}-{i+1:02d}",
                    kind="synthetic_security_event",
                    source=edge.source,
                    target=edge.target,
                    summary=f"Synthetic {edge.relation} activity from {edge.source} to {edge.target}.",
                    supports=scenario.techniques,
                )
                for i, edge in enumerate(scenario.path)
            ]

        return AgentResult("red", "complete", {
            "scenario": scenario.name,
            "objective": scenario.objective,
            "techniques": scenario.techniques,
            "path": path,
            "evidence": [asdict(item) for item in evidence],
            "simulation_only": True,
        })


class BlueAgent(BaseAgent):
    role = "blue"

    def run(self, scenario: Scenario, red: AgentResult) -> AgentResult:
        self._authorize("correlate_evidence")
        with self.trace.step(self.role, "correlate_evidence"):
            evidence = red.payload["evidence"]
            coverage = len(evidence) / max(1, len(scenario.path))
            reconstructed = [f"{e['source']} -> {e['target']}" for e in evidence]
            evidence_graph = build_evidence_graph(red.payload)

        self._authorize("retrieve_knowledge")
        with self.trace.step(self.role, "retrieve_knowledge"):
            query = f"{scenario.objective} {' '.join(edge.control for edge in scenario.path)}"
            knowledge = retrieve(query)

        self._authorize("map_techniques")
        with self.trace.step(self.role, "map_techniques"):
            cited_ids = [e["id"] for e in evidence]

        return AgentResult("blue", "complete", {
            "verdict": "synthetic_attack_path_reconstructed",
            "evidence_coverage": round(coverage, 3),
            "reconstructed_path": reconstructed,
            "evidence_ids": cited_ids,
            "evidence_graph": evidence_graph,
            "techniques": scenario.techniques,
            "retrieval": [{"id": k.id, "title": k.title, "text": k.text} for k in knowledge],
            "grounded": bool(cited_ids),
            "recommended_response": "human review required before any consequential containment action",
        })


class GreenAgent(BaseAgent):
    role = "green"

    def run(self, scenario: Scenario, original_risk: float) -> AgentResult:
        self._authorize("propose_control")
        candidates = []
        with self.trace.step(self.role, "propose_control"):
            for i, edge in enumerate(scenario.path):
                hardened = apply_control(scenario.path, i)
                residual = path_risk(hardened)
                candidates.append({
                    "edge_index": i,
                    "control": edge.control,
                    "source": edge.source,
                    "target": edge.target,
                    "residual_risk": residual,
                    "risk_reduction": round(original_risk - residual, 4),
                })
            candidates.sort(key=lambda item: (-item["risk_reduction"], item["control"]))
            selected = candidates[0]

        self._authorize("counterfactual_replay")
        with self.trace.step(self.role, "counterfactual_replay"):
            hardened_path = apply_control(scenario.path, selected["edge_index"])
            residual_risk = path_risk(hardened_path)

        return AgentResult("green", "complete", {
            "selected_control": selected,
            "candidate_controls": candidates,
            "counterfactual": {
                "original_risk": original_risk,
                "residual_risk": residual_risk,
                "risk_reduction": round(original_risk - residual_risk, 4),
                "source_environment_mutated": False,
            },
        })
