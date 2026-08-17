import unittest

from aegismesh.environment import get_scenario, path_risk
from aegismesh.orchestrator import AegisMeshOrchestrator
from aegismesh.policy import PolicyGateway
from aegismesh.report import build_report
from aegismesh.retrieval import retrieve


class AegisMeshTests(unittest.TestCase):
    def test_end_to_end_workflow(self):
        run = AegisMeshOrchestrator().run("identity-saas-exfil")
        self.assertEqual(run.red.status, "complete")
        self.assertEqual(run.blue.status, "complete")
        self.assertEqual(run.green.status, "complete")
        self.assertTrue(run.blue.payload["grounded"])
        self.assertLess(run.residual_risk, run.original_risk)
        self.assertFalse(run.green.payload["counterfactual"]["source_environment_mutated"])

    def test_all_scenarios_improve_under_selected_control(self):
        report = build_report()
        self.assertEqual(report["summary"]["workflow_completion"], "3/3")
        self.assertEqual(report["summary"]["counterfactuals_improved"], "3/3")
        for run in report["runs"]:
            self.assertLess(run["residual_risk"], run["original_risk"])

    def test_policy_blocks_cross_role_and_consequential_tools(self):
        policy = PolicyGateway()
        self.assertFalse(policy.authorize("red", "counterfactual_replay").allowed)
        consequential = policy.authorize("blue", "revoke_token")
        self.assertFalse(consequential.allowed)
        self.assertTrue(consequential.requires_approval)

    def test_retrieval_is_grounded_in_local_corpus(self):
        items = retrieve("token protection session replay")
        self.assertGreater(len(items), 0)
        self.assertTrue(any(item.id == "kb-token" for item in items))

    def test_risk_is_bounded(self):
        scenario = get_scenario("cloud-admin-pivot")
        score = path_risk(scenario.path)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()
