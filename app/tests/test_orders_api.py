import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE_DIRECTORY = Path(__file__).resolve().parents[1] / "lambda_src"
sys.path.insert(0, str(SOURCE_DIRECTORY))

import app  # noqa: E402


class OrdersApiTests(unittest.TestCase):
    def test_returns_healthy_response_when_development_setting_exists(self):
        with patch.dict(
            os.environ,
            {app.REQUIRED_SETTING: app.EXPECTED_ENVIRONMENT},
            clear=True,
        ):
            response = app.lambda_handler({}, None)

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"])["status"], "healthy")

    def test_emits_documented_error_when_development_setting_is_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertLogs(app.LOGGER, level="ERROR") as captured_logs:
                response = app.lambda_handler({}, None)

        self.assertEqual(response["statusCode"], 503)
        self.assertEqual(json.loads(response["body"])["status"], "unhealthy")
        self.assertIn(app.MISSING_CONFIG_MESSAGE, captured_logs.output[0])
