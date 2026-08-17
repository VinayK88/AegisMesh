from __future__ import annotations

from .models import PolicyDecision


ROLE_TOOLS = {
    "red": {"select_simulated_path", "emit_synthetic_events"},
    "blue": {"correlate_evidence", "retrieve_knowledge", "map_techniques"},
    "green": {"propose_control", "counterfactual_replay"},
}

HUMAN_APPROVAL_TOOLS = {
    "contain_host",
    "revoke_token",
    "disable_account",
    "change_policy",
}


class PolicyGateway:
    def authorize(self, role: str, tool: str) -> PolicyDecision:
        if tool in HUMAN_APPROVAL_TOOLS:
            return PolicyDecision(False, True, "consequential action requires explicit human approval")
        if tool not in ROLE_TOOLS.get(role, set()):
            return PolicyDecision(False, False, f"tool '{tool}' is not allowed for role '{role}'")
        return PolicyDecision(True, False, "approved synthetic defensive tool")
