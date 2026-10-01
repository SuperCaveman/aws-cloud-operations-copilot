"""Small, deterministic AWS read-only tools used before any model reasoning occurs."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from typing import Any

from .config import AllowedResources


class ToolInputError(ValueError):
    """Raised when a request falls outside the fixed Phase 1 contract."""


SENSITIVE_ASSIGNMENT = re.compile(
    r"(?i)\b(password|token|api[_-]?key|secret)\s*[:=]\s*([^\s,;]+)"
)
ORDERS_API_ERROR_FILTER = '"orders-api configuration check failed"'


class DiagnosticTools:
    """Expose facts from one allow-listed development service and nothing else."""

    def __init__(
        self,
        resources: AllowedResources,
        cloudwatch_client: Any,
        logs_client: Any,
        lambda_client: Any,
    ) -> None:
        self.resources = resources
        self.cloudwatch_client = cloudwatch_client
        self.logs_client = logs_client
        self.lambda_client = lambda_client

    def get_alarm_state(self, service_name: str) -> dict[str, Any]:
        """Return the fixed development alarm state and its AWS-provided reason."""
        self._require_allowed_service(service_name)
        response = self.cloudwatch_client.describe_alarms(
            AlarmNames=[self.resources.alarm_name]
        )
        alarms = response.get("MetricAlarms", [])
        if len(alarms) != 1:
            raise RuntimeError("The allow-listed development alarm was not found.")

        alarm = alarms[0]
        return {
            "service": self.resources.service_name,
            "alarm_name": self.resources.alarm_name,
            "state": alarm.get("StateValue"),
            "state_reason": alarm.get("StateReason"),
            "state_updated_at": _as_iso_string(alarm.get("StateUpdatedTimestamp")),
        }

    def get_recent_error_logs(
        self,
        service_name: str,
        minutes: int = 15,
        max_events: int = 10,
    ) -> dict[str, Any]:
        """Return a bounded, redacted error-log excerpt from the fixed log group."""
        self._require_allowed_service(service_name)
        self._require_range("minutes", minutes, minimum=1, maximum=60)
        self._require_range("max_events", max_events, minimum=1, maximum=25)

        start_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        response = self.logs_client.filter_log_events(
            logGroupName=self.resources.log_group_name,
            startTime=int(start_time.timestamp() * 1000),
            filterPattern=ORDERS_API_ERROR_FILTER,
            limit=max_events,
        )

        events = [
            {
                "timestamp": _timestamp_millis_to_iso(event.get("timestamp")),
                "message": redact_log_message(event.get("message", "")),
            }
            for event in response.get("events", [])
        ]
        return {
            "service": self.resources.service_name,
            "log_group_name": self.resources.log_group_name,
            "window_minutes": minutes,
            "events": events,
        }

    def get_safe_function_metadata(self, service_name: str) -> dict[str, Any]:
        """Return an explicit allow-list of Lambda metadata, never its configuration values."""
        self._require_allowed_service(service_name)
        response = self.lambda_client.get_function_configuration(
            FunctionName=self.resources.function_name
        )
        return {
            "service": self.resources.service_name,
            "function_name": response.get("FunctionName"),
            "runtime": response.get("Runtime"),
            "memory_size_mb": response.get("MemorySize"),
            "timeout_seconds": response.get("Timeout"),
            "state": response.get("State"),
            "last_modified": response.get("LastModified"),
        }

    def _require_allowed_service(self, service_name: str) -> None:
        if service_name != self.resources.service_name:
            raise ToolInputError(
                "Only the allow-listed development service 'orders-api' may be queried."
            )

    @staticmethod
    def _require_range(name: str, value: int, minimum: int, maximum: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ToolInputError(f"{name} must be an integer.")
        if not minimum <= value <= maximum:
            raise ToolInputError(f"{name} must be between {minimum} and {maximum}.")


def build_aws_tools(resources: AllowedResources) -> DiagnosticTools:
    """Construct the three AWS SDK clients only when tools run outside unit tests."""
    import boto3

    return DiagnosticTools(
        resources=resources,
        cloudwatch_client=boto3.client("cloudwatch", region_name=resources.region),
        logs_client=boto3.client("logs", region_name=resources.region),
        lambda_client=boto3.client("lambda", region_name=resources.region),
    )


def redact_log_message(message: str) -> str:
    """Remove common key-value secrets before returning log text to a model or UI."""
    return SENSITIVE_ASSIGNMENT.sub(r"\1=[REDACTED]", message)


def _as_iso_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    return str(value)


def _timestamp_millis_to_iso(value: Any) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc).isoformat()
