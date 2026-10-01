"""Synthetic development-only Lambda for the Cloud Operations Copilot study project."""

import json
import logging
import os

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

REQUIRED_SETTING = "ORDERS_API_ENVIRONMENT"
EXPECTED_ENVIRONMENT = "development"
MISSING_CONFIG_MESSAGE = (
    "orders-api configuration check failed: required non-secret setting "
    "ORDERS_API_ENVIRONMENT is not configured"
)


def lambda_handler(event, context):
    """Return a safe health response or emit the one documented synthetic error."""
    configured_environment = os.getenv(REQUIRED_SETTING)

    if configured_environment != EXPECTED_ENVIRONMENT:
        LOGGER.error(MISSING_CONFIG_MESSAGE)
        return {
            "statusCode": 503,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "service": "orders-api",
                    "status": "unhealthy",
                    "message": "Development configuration validation failed.",
                }
            ),
        }

    LOGGER.info("orders-api health check passed")
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "service": "orders-api",
                "status": "healthy",
                "environment": EXPECTED_ENVIRONMENT,
            }
        ),
    }
