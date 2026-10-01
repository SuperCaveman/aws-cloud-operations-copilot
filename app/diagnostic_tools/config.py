"""Configuration for the one permitted Phase 1 development service."""

from dataclasses import dataclass
import os


class ConfigurationError(ValueError):
    """Raised when a required non-secret runtime setting is missing."""


@dataclass(frozen=True)
class AllowedResources:
    """Names the tools are permitted to query; no caller supplies AWS names directly."""

    service_name: str
    function_name: str
    log_group_name: str
    alarm_name: str
    region: str

    @classmethod
    def from_environment(cls) -> "AllowedResources":
        required_names = (
            "COPILOT_FUNCTION_NAME",
            "COPILOT_LOG_GROUP_NAME",
            "COPILOT_ALARM_NAME",
            "AWS_REGION",
        )
        values = {name: os.getenv(name) for name in required_names}
        missing = [name for name, value in values.items() if not value]

        if missing:
            names = ", ".join(missing)
            raise ConfigurationError(f"Missing required runtime settings: {names}")

        return cls(
            service_name="orders-api",
            function_name=values["COPILOT_FUNCTION_NAME"],
            log_group_name=values["COPILOT_LOG_GROUP_NAME"],
            alarm_name=values["COPILOT_ALARM_NAME"],
            region=values["AWS_REGION"],
        )
