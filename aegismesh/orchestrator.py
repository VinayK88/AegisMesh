from __future__ import annotations

import uuid

from .agents import BlueAgent, GreenAgent, RedAgent
from .environment import get_scenario, path_risk
from .models import RunReport
from .observability import TraceCollector
from .policy import PolicyGateway


class AegisMeshOrchestrator:
    def __init__(self):
        self.policy = PolicyGateway()

    def run(self, scenario_id: str) -> RunReport:
        run_id = uuid.uuid4().hex[:12]
        trace = TraceCollector(run_id)
        scenario = get_scenario(scenario_id)
        original_risk = path_risk(scenario.path)

        red = RedAgent(self.policy, trace).run(scenario)
        blue = BlueAgent(self.policy, trace).run(scenario, red)
        green = GreenAgent(self.policy, trace).run(scenario, original_risk)

        residual = green.payload["counterfactual"]["residual_risk"]
        trace.persist()
        return RunReport(
            run_id=run_id,
            scenario_id=scenario_id,
            original_risk=original_risk,
            residual_risk=residual,
            risk_reduction=round(original_risk - residual, 4),
            red=red,
            blue=blue,
            green=green,
            traces=trace.events,
        )
