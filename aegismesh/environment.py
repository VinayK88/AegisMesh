from __future__ import annotations

import copy
from math import prod

from .models import Edge, Scenario


SCENARIOS: dict[str, Scenario] = {
    "identity-saas-exfil": Scenario(
        id="identity-saas-exfil",
        name="Identity to SaaS data path",
        objective="Reach a synthetic sensitive collaboration resource through identity and SaaS trust.",
        techniques=["T1566", "T1078", "T1528", "T1530"],
        path=[
            Edge("internet", "finance_user", "social_engineering", 0.42, "phishing-resistant MFA"),
            Edge("finance_user", "session_token", "session_access", 0.55, "token protection"),
            Edge("session_token", "saas_app", "federated_access", 0.62, "continuous access evaluation"),
            Edge("saas_app", "sensitive_docs", "delegated_read", 0.66, "least-privilege OAuth scopes"),
        ],
    ),
    "oauth-mailbox-abuse": Scenario(
        id="oauth-mailbox-abuse",
        name="OAuth mailbox abuse",
        objective="Exercise a synthetic risky-consent path into mailbox data.",
        techniques=["T1098.003", "T1114.002"],
        path=[
            Edge("user", "oauth_grant", "consent", 0.58, "admin consent workflow"),
            Edge("oauth_grant", "mailbox", "persistent_api_access", 0.69, "scope reduction"),
        ],
    ),
    "cloud-admin-pivot": Scenario(
        id="cloud-admin-pivot",
        name="Cloud administrator pivot",
        objective="Model a privileged identity path to a critical workload.",
        techniques=["T1078.004", "T1098", "T1530"],
        path=[
            Edge("internet", "cloud_admin", "credential_exposure", 0.36, "phishing-resistant MFA"),
            Edge("cloud_admin", "admin_session", "privileged_session", 0.61, "privileged access workstation"),
            Edge("admin_session", "critical_workload", "management_plane_access", 0.72, "just-in-time privilege"),
        ],
    ),
}


def list_scenarios() -> list[Scenario]:
    return list(SCENARIOS.values())


def get_scenario(scenario_id: str) -> Scenario:
    if scenario_id not in SCENARIOS:
        raise KeyError(f"unknown scenario: {scenario_id}")
    return copy.deepcopy(SCENARIOS[scenario_id])


def path_risk(path: list[Edge]) -> float:
    # Probability-like internal score for a synthetic graph only.
    if not path:
        return 0.0
    survival = prod(1.0 - max(0.0, min(1.0, edge.risk)) for edge in path)
    return round(1.0 - survival, 4)


def apply_control(path: list[Edge], index: int, effectiveness: float = 0.65) -> list[Edge]:
    hardened = copy.deepcopy(path)
    edge = hardened[index]
    hardened[index] = Edge(
        edge.source,
        edge.target,
        edge.relation,
        round(edge.risk * (1.0 - effectiveness), 4),
        edge.control,
    )
    return hardened
