"""Unit tests for local Streamlit configuration helpers; no AWS calls are made."""

import os
import unittest
from unittest.mock import Mock, patch

from app.diagnostic_tools import AllowedResources, ConfigurationError
from streamlit_app import (
    MAX_OUTPUT_TOKENS,
    build_workflow_from_environment,
    get_runbook_bucket_from_environment,
    model_usage_label,
)


class StreamlitAppTests(unittest.TestCase):
    def test_bucket_setting_is_required(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ConfigurationError, "COPILOT_RUNBOOK_BUCKET"):
                get_runbook_bucket_from_environment()

    def test_zero_token_label_makes_the_gate_visible(self):
        self.assertEqual(
            model_usage_label({"inputTokens": 0, "outputTokens": 0, "totalTokens": 0}),
            "Bedrock model use for this request: 0 tokens (evidence gate response).",
        )

    def test_nonzero_label_names_the_output_limit(self):
        label = model_usage_label({"totalTokens": 22})
        self.assertIn("22 tokens", label)
        self.assertIn(str(MAX_OUTPUT_TOKENS), label)

    @patch("streamlit_app.build_incident_graph")
    @patch("streamlit_app.boto3.client")
    @patch("streamlit_app.build_aws_runbook_retriever")
    @patch("streamlit_app.build_aws_tools")
    @patch("streamlit_app.AllowedResources.from_environment")
    def test_workflow_uses_only_environment_scoped_dependencies(
        self,
        resources_from_environment: Mock,
        diagnostic_tools: Mock,
        runbook_retriever: Mock,
        bedrock_client: Mock,
        incident_graph: Mock,
    ):
        resources = AllowedResources(
            service_name="orders-api",
            function_name="orders-api-dev",
            log_group_name="/aws/lambda/orders-api-dev",
            alarm_name="orders-api-dev-alarm",
            region="us-west-2",
        )
        resources_from_environment.return_value = resources

        with patch.dict(
            os.environ,
            {"COPILOT_RUNBOOK_BUCKET": "lab-runbooks"},
            clear=True,
        ):
            result = build_workflow_from_environment()

        runbook_retriever.assert_called_once_with(
            bucket_name="lab-runbooks",
            region="us-west-2",
        )
        bedrock_client.assert_called_once_with(
            "bedrock-runtime",
            region_name="us-west-2",
        )
        diagnostic_tools.assert_called_once_with(resources)
        incident_graph.assert_called_once()
        self.assertEqual(result, incident_graph.return_value)


if __name__ == "__main__":
    unittest.main()