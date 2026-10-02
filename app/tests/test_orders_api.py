import json
import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch

HANDLER_PATH = Path(__file__).resolve().parents[1] / "lambda_src" / "app.py"
HANDLER_SPEC = importlib.util.spec_from_file_location("orders_api_handler", HANDLER_PATH)
assert HANDLER_SPEC and HANDLER_SPEC.loader
orders_api_handler = importlib.util.module_from_spec(HANDLER_SPEC)
HANDLER_SPEC.loader.exec_module(orders_api_handler)



class OrdersApiTests(unittest.TestCase):
    def test_returns_healthy_response_when_development_setting_exists(self):
        with patch.dict(
            os.environ,
            {
                orders_api_handler.REQUIRED_SETTING: orders_api_handler.EXPECTED_ENVIRONMENT,
            },
            clear=True,
        ):
            response = orders_api_handler.lambda_handler({}, None)

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"])["status"], "healthy")

    def test_emits_documented_error_when_development_setting_is_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertLogs(orders_api_handler.LOGGER, level="ERROR") as captured_logs:
                response = orders_api_handler.lambda_handler({}, None)

        self.assertEqual(response["statusCode"], 503)
        self.assertEqual(json.loads(response["body"])["status"], "unhealthy")
        self.assertIn(orders_api_handler.MISSING_CONFIG_MESSAGE, captured_logs.output[0])
