from pathlib import Path
import sys
import unittest

APP_DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIRECTORY))

from agent.workflow import DEFAULT_MODEL_ID, MAX_OUTPUT_TOKENS, build_incident_graph


class FakeDiagnosticTools:
    def get_alarm_state(self, service_name):
        return {"service": service_name, "state": "ALARM", "state_reason": "error"}

    def get_recent_error_logs(self, service_name, minutes=15, max_events=10):
        return {
            "service": service_name,
            "events": [
                {
                    "message": "orders-api configuration check failed: required non-secret setting ORDERS_API_ENVIRONMENT is not configured"
                }
            ],
        }

    def get_safe_function_metadata(self, service_name):
        return {"service": service_name, "runtime": "python3.14", "state": "Active"}


class FakeRunbookRetriever:
    def get_orders_api_runbook(self):
        return {
            "source": "s3://test-runbooks/runbooks/orders-api-missing-config.md",
            "content": "Restore the non-secret development setting through Terraform.",
        }


class HealthyFakeDiagnosticTools(FakeDiagnosticTools):
    def get_alarm_state(self, service_name):
        return {"service": service_name, "state": "OK", "state_reason": "no errors"}

    def get_recent_error_logs(self, service_name, minutes=15, max_events=10):
        return {"service": service_name, "window_minutes": minutes, "events": []}


class RecoveringFakeDiagnosticTools(FakeDiagnosticTools):
    def get_recent_error_logs(self, service_name, minutes=15, max_events=10):
        return {
            "service": service_name,
            "window_minutes": minutes,
            "events": [
                {
                    "timestamp": "2026-10-01T22:37:28.311000+00:00",
                    "message": "orders-api configuration check failed",
                }
            ],
        }

    def get_safe_function_metadata(self, service_name):
        return {
            "service": service_name,
            "state": "Active",
            "last_modified": "2026-10-01T22:38:55.000+0000",
        }


class FakeBedrockClient:
    def __init__(self):
        self.request = None

    def converse(self, **kwargs):
        self.request = kwargs
        return {
            "output": {
                "message": {
                    "content": [
                        {
                            "text": "## Observed evidence\nThe alarm is ALARM.\n\n## Runbook reference\nTest runbook.\n\n## Likely cause\nInference: the setting is absent.\n\n## Safe next step\nA human should restore it.\n\n## Confidence and limits\nHigh for this synthetic case."
                        }
                    ]
                }
            },
            "usage": {"inputTokens": 100, "outputTokens": 50},
        }


class AgentWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.bedrock = FakeBedrockClient()
        self.graph = build_incident_graph(
            FakeDiagnosticTools(),
            FakeRunbookRetriever(),
            self.bedrock,
        )

    def test_graph_collects_facts_before_a_single_bounded_model_call(self):
        result = self.graph.invoke({"question": "Why is orders-api failing?"})

        self.assertEqual(result["evidence"]["alarm"]["state"], "ALARM")
        self.assertIn("## Observed evidence", result["report"])
        self.assertEqual(result["usage"]["outputTokens"], 50)
        self.assertEqual(self.bedrock.request["modelId"], DEFAULT_MODEL_ID)
        self.assertEqual(
            self.bedrock.request["inferenceConfig"]["maxTokens"], MAX_OUTPUT_TOKENS
        )
        self.assertIn(
            "ORDERS_API_ENVIRONMENT",
            self.bedrock.request["messages"][0]["content"][0]["text"],
        )

    def test_graph_rejects_an_empty_question_before_calling_the_model(self):
        with self.assertRaisesRegex(ValueError, "non-empty incident question"):
            self.graph.invoke({"question": " "})

        self.assertIsNone(self.bedrock.request)

    def test_healthy_evidence_bypasses_the_model_and_reports_no_active_incident(self):
        graph = build_incident_graph(
            HealthyFakeDiagnosticTools(),
            FakeRunbookRetriever(),
            self.bedrock,
        )

        result = graph.invoke({"question": "Why is orders-api failing?"})

        self.assertEqual(result["incident_status"], "no_active_missing_config_incident")
        self.assertIn("No active missing-configuration incident", result["report"])
        self.assertEqual(result["usage"]["totalTokens"], 0)
        self.assertIsNone(self.bedrock.request)

    def test_recovery_evidence_bypasses_the_model_and_does_not_recommend_a_second_change(self):
        graph = build_incident_graph(
            RecoveringFakeDiagnosticTools(),
            FakeRunbookRetriever(),
            self.bedrock,
        )

        result = graph.invoke({"question": "Why is orders-api failing?"})

        self.assertEqual(
            result["incident_status"],
            "recent_missing_config_incident_may_be_recovering",
        )
        self.assertIn("Do not make another change", result["report"])
        self.assertEqual(result["usage"]["totalTokens"], 0)
        self.assertIsNone(self.bedrock.request)
