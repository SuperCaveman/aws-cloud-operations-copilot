from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

APP_DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIRECTORY))

from diagnostic_tools.config import AllowedResources
from diagnostic_tools.tools import (
    ORDERS_API_ERROR_FILTER,
    DiagnosticTools,
    ToolInputError,
    redact_log_message,
)


class DiagnosticToolsTests(unittest.TestCase):
    def setUp(self):
        self.resources = AllowedResources(
            service_name="orders-api",
            function_name="test-orders-api",
            log_group_name="/aws/lambda/test-orders-api",
            alarm_name="test-orders-api-missing-config",
            region="us-west-2",
        )
        self.cloudwatch = Mock()
        self.logs = Mock()
        self.lambda_client = Mock()
        self.tools = DiagnosticTools(
            self.resources,
            self.cloudwatch,
            self.logs,
            self.lambda_client,
        )

    def test_alarm_tool_queries_only_the_allow_listed_alarm(self):
        self.cloudwatch.describe_alarms.return_value = {
            "MetricAlarms": [
                {
                    "StateValue": "ALARM",
                    "StateReason": "Synthetic failure detected",
                    "StateUpdatedTimestamp": datetime(2026, 10, 1, tzinfo=timezone.utc),
                }
            ]
        }

        result = self.tools.get_alarm_state("orders-api")

        self.cloudwatch.describe_alarms.assert_called_once_with(
            AlarmNames=["test-orders-api-missing-config"]
        )
        self.assertEqual(result["state"], "ALARM")
        self.assertEqual(result["service"], "orders-api")

    def test_log_tool_bounds_the_time_window_and_redacts_log_values(self):
        self.logs.filter_log_events.return_value = {
            "events": [
                {
                    "timestamp": 1_791_388_800_000,
                    "message": "ERROR token=do-not-return-this-value",
                }
            ]
        }

        result = self.tools.get_recent_error_logs("orders-api", minutes=5, max_events=1)

        call = self.logs.filter_log_events.call_args.kwargs
        self.assertEqual(call["logGroupName"], "/aws/lambda/test-orders-api")
        self.assertEqual(call["filterPattern"], ORDERS_API_ERROR_FILTER)
        self.assertEqual(call["limit"], 1)
        self.assertEqual(result["events"][0]["message"], "ERROR token=[REDACTED]")

    def test_metadata_tool_does_not_return_environment_variables(self):
        self.lambda_client.get_function_configuration.return_value = {
            "FunctionName": "test-orders-api",
            "Runtime": "python3.14",
            "MemorySize": 128,
            "Timeout": 10,
            "State": "Active",
            "LastModified": "2026-10-01T00:00:00.000+0000",
            "Environment": {"Variables": {"DO_NOT_EXPOSE": "value"}},
        }

        result = self.tools.get_safe_function_metadata("orders-api")

        self.assertNotIn("Environment", result)
        self.assertNotIn("DO_NOT_EXPOSE", str(result))
        self.assertEqual(result["runtime"], "python3.14")

    def test_tools_refuse_an_unknown_service(self):
        with self.assertRaises(ToolInputError):
            self.tools.get_alarm_state("some-other-service")

    def test_log_tool_refuses_an_unbounded_request(self):
        with self.assertRaises(ToolInputError):
            self.tools.get_recent_error_logs("orders-api", minutes=61)

    def test_redaction_covers_common_secret_assignments(self):
        message = "password: nope api_key=also-nope secret=value"
        self.assertEqual(
            redact_log_message(message),
            "password=[REDACTED] api_key=[REDACTED] secret=[REDACTED]",
        )
