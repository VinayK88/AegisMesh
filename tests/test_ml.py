import unittest

from aegismesh.environment import get_scenario, path_risk
from aegismesh.ml import (
    control_model,
    rank_controls,
    recommend_model,
    router_model,
    score_workflow,
)
from aegismesh.orchestrator import AegisMeshOrchestrator


class AegisMeshMLTests(unittest.TestCase):
    def test_router_has_strong_synthetic_holdout_and_safe_override(self):
        _, metrics = router_model()
        self.assertGreater(metrics["synthetic_holdout_accuracy"], 0.9)

        routed = recommend_model("high_impact_proposal", {
            "complexity": 0.1,
            "risk": 0.1,
            "latency_budget_ms": 200,
            "cost_budget": 0.005,
            "approval_required": True,
        })
        self.assertTrue(routed["safety_override"])
        self.assertEqual(routed["selected_model_class"], "high-reliability-model")

    def test_control_ranker_quality_and_replay_boundary(self):
        _, metrics = control_model()
        self.assertLess(metrics["synthetic_holdout_mae"], 0.02)
        self.assertGreater(metrics["synthetic_holdout_r2"], 0.9)

        scenario = get_scenario("oauth-mailbox-abuse")
        ranking = rank_controls(scenario, path_risk(scenario.path))
        self.assertEqual(ranking["model"], "GradientBoostingRegressor")
        self.assertGreater(len(ranking["ranked_candidates"]), 0)

        run = AegisMeshOrchestrator().run("oauth-mailbox-abuse")
        self.assertTrue(run.green.payload["counterfactual"]["prediction_verified_by_replay"])
        self.assertLess(run.residual_risk, run.original_risk)

    def test_workflow_health_is_advisory_and_bounded(self):
        run = AegisMeshOrchestrator().run("identity-saas-exfil")
        health = run.workflow_ml
        self.assertEqual(health["model"], "IsolationForest")
        self.assertGreaterEqual(health["anomaly_percentile"], 0.0)
        self.assertLessEqual(health["anomaly_percentile"], 100.0)
        self.assertIn(health["status"], {"NORMAL", "REVIEW"})
        self.assertIn("not a compromise probability", health["boundary"])

    def test_abnormal_trace_scores_as_more_unusual(self):
        normal_run = AegisMeshOrchestrator().run("cloud-admin-pivot")
        normal_score = normal_run.workflow_ml["anomaly_percentile"]

        abnormal = []
        for _ in range(18):
            abnormal.append({"agent": "blue", "action": "retrieve_knowledge", "status": "ok", "latency_ms": 40.0})
            abnormal.append({"agent": "blue", "action": "policy_check", "tool": "unknown", "allowed": False, "reason": "denied"})
        abnormal_score = score_workflow(abnormal)["anomaly_percentile"]
        self.assertGreater(abnormal_score, normal_score)
        self.assertGreaterEqual(abnormal_score, 95.0)


if __name__ == "__main__":
    unittest.main()
