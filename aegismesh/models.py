from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    relation: str
    risk: float
    control: str


@dataclass
class Scenario:
    id: str
    name: str
    objective: str
    path: list[Edge]
    techniques: list[str]


@dataclass
class Evidence:
    id: str
    kind: str
    source: str
    target: str
    summary: str
    supports: list[str] = field(default_factory=list)


@dataclass
class PolicyDecision:
    allowed: bool
    requires_approval: bool
    reason: str


@dataclass
class AgentResult:
    agent: str
    status: str
    payload: dict[str, Any]


@dataclass
class RunReport:
    run_id: str
    scenario_id: str
    original_risk: float
    residual_risk: float
    risk_reduction: float
    red: AgentResult
    blue: AgentResult
    green: AgentResult
    traces: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
