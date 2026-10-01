"""A fixed LangGraph workflow: facts first, one bounded Bedrock explanation second."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Protocol, TypedDict

from langgraph.graph import END, START, StateGraph


DEFAULT_MODEL_ID = "amazon.nova-lite-v1:0"
MAX_OUTPUT_TOKENS = 350
MAX_QUESTION_CHARACTERS = 500

SYSTEM_PROMPT = """You are the AWS Cloud Operations Copilot for one development-only service.
Use only the supplied evidence and runbook. Do not invent AWS facts, quote unavailable
environment-variable values, claim you changed anything, or recommend an automatic change.

Return Markdown with exactly these headings:
## Observed evidence
## Runbook reference
## Likely cause
## Safe next step
## Confidence and limits

Label the likely cause as an inference. If the evidence does not establish a cause, say so.
The safe next step must be a human-reviewed, reversible development action.
Keep the total response under 180 words and do not reproduce the full runbook.
"""


class DiagnosticToolsProtocol(Protocol):
    def get_alarm_state(self, service_name: str) -> dict[str, Any]: ...

    def get_recent_error_logs(
        self, service_name: str, minutes: int = 15, max_events: int = 10
    ) -> dict[str, Any]: ...

    def get_safe_function_metadata(self, service_name: str) -> dict[str, Any]: ...


class RunbookRetrieverProtocol(Protocol):
    def get_orders_api_runbook(self) -> dict[str, str]: ...


class IncidentState(TypedDict, total=False):
    question: str
    evidence: dict[str, Any]
    runbook: dict[str, str]
    incident_status: str
    report: str
    usage: dict[str, Any]


def build_incident_graph(
    diagnostic_tools: DiagnosticToolsProtocol,
    runbook_retriever: RunbookRetrieverProtocol,
    bedrock_client: Any,
    model_id: str = DEFAULT_MODEL_ID,
):
    """Build the one-path workflow used for a safe, reproducible incident explanation."""

    def collect_evidence(state: IncidentState) -> dict[str, Any]:
        _validate_question(state["question"])
        return {
            "evidence": {
                "alarm": diagnostic_tools.get_alarm_state("orders-api"),
                "recent_error_logs": diagnostic_tools.get_recent_error_logs("orders-api"),
                "function_metadata": diagnostic_tools.get_safe_function_metadata(
                    "orders-api"
                ),
            }
        }

    def retrieve_runbook(state: IncidentState) -> dict[str, Any]:
        return {"runbook": runbook_retriever.get_orders_api_runbook()}

    def assess_evidence(state: IncidentState) -> dict[str, Any]:
        alarm_state = state["evidence"]["alarm"].get("state")
        logs = state["evidence"]["recent_error_logs"]
        matching_error_events = logs.get("events", [])
        metadata = state["evidence"]["function_metadata"]

        if alarm_state != "ALARM" or not matching_error_events:
            status = "no_active_missing_config_incident"
        elif _function_changed_after_latest_error(metadata, matching_error_events):
            status = "recent_missing_config_incident_may_be_recovering"
        else:
            status = "active_missing_config_incident"
        return {"incident_status": status}

    def no_active_incident_report(state: IncidentState) -> dict[str, Any]:
        alarm = state["evidence"]["alarm"]
        logs = state["evidence"]["recent_error_logs"]
        metadata = state["evidence"]["function_metadata"]
        return {
            "report": "\n\n".join(
                (
                    "## Observed evidence\n"
                    f"The allow-listed alarm is `{alarm.get('state')}`; the last "
                    f"{logs.get('window_minutes')} minutes contain "
                    f"{len(logs.get('events', []))} matching configuration error(s); "
                    f"and the Lambda state is `{metadata.get('state')}`.",
                    "## Runbook reference\n" + state["runbook"]["source"],
                    "## Likely cause\n"
                    "No active missing-configuration incident is evidenced. The scoped "
                    "tools cannot determine whether an unrelated problem exists.",
                    "## Safe next step\n"
                    "Do not change configuration. Confirm the reported symptom and, if it "
                    "persists, collect the appropriate additional evidence through the normal "
                    "human-reviewed process.",
                    "## Confidence and limits\n"
                    "High confidence only that the documented missing-configuration signal is "
                    "not currently active. This does not prove every possible service issue is absent.",
                )
            ),
            "usage": {"inputTokens": 0, "outputTokens": 0, "totalTokens": 0},
        }

    def recovery_in_progress_report(state: IncidentState) -> dict[str, Any]:
        metadata = state["evidence"]["function_metadata"]
        return {
            "report": "\n\n".join(
                (
                    "## Observed evidence\n"
                    "The alarm and matching error log show a recent missing-configuration "
                    "incident, but the Lambda was modified after that error at "
                    f"`{metadata.get('last_modified')}`.",
                    "## Runbook reference\n" + state["runbook"]["source"],
                    "## Likely cause\n"
                    "A recovery may already be in progress; the scoped evidence cannot confirm "
                    "the current environment-variable value.",
                    "## Safe next step\n"
                    "Do not make another change. Invoke the development health check and wait for "
                    "the next CloudWatch evaluation to confirm the alarm returns to `OK`.",
                    "## Confidence and limits\n"
                    "High confidence that the error occurred. Medium confidence that recovery is "
                    "complete until a fresh health check and alarm state confirm it.",
                )
            ),
            "usage": {"inputTokens": 0, "outputTokens": 0, "totalTokens": 0},
        }

    def generate_report(state: IncidentState) -> dict[str, Any]:
        prompt = _build_user_prompt(
            question=state["question"],
            evidence=state["evidence"],
            runbook=state["runbook"],
        )
        response = bedrock_client.converse(
            modelId=model_id,
            system=[{"text": SYSTEM_PROMPT}],
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": MAX_OUTPUT_TOKENS, "temperature": 0.2},
        )
        return {
            "report": response["output"]["message"]["content"][0]["text"],
            "usage": response.get("usage", {}),
        }

    def route_after_runbook(state: IncidentState) -> str:
        if state["incident_status"] == "active_missing_config_incident":
            return "generate_report"
        if state["incident_status"] == "recent_missing_config_incident_may_be_recovering":
            return "recovery_in_progress_report"
        return "no_active_incident_report"

    graph = StateGraph(IncidentState)
    graph.add_node("collect_evidence", collect_evidence)
    graph.add_node("retrieve_runbook", retrieve_runbook)
    graph.add_node("assess_evidence", assess_evidence)
    graph.add_node("no_active_incident_report", no_active_incident_report)
    graph.add_node("recovery_in_progress_report", recovery_in_progress_report)
    graph.add_node("generate_report", generate_report)
    graph.add_edge(START, "collect_evidence")
    graph.add_edge("collect_evidence", "assess_evidence")
    graph.add_edge("assess_evidence", "retrieve_runbook")
    graph.add_conditional_edges("retrieve_runbook", route_after_runbook)
    graph.add_edge("no_active_incident_report", END)
    graph.add_edge("recovery_in_progress_report", END)
    graph.add_edge("generate_report", END)
    return graph.compile()


def _build_user_prompt(
    question: str,
    evidence: dict[str, Any],
    runbook: dict[str, str],
) -> str:
    return "\n\n".join(
        (
            f"Engineer question:\n{question}",
            "Observed evidence JSON:\n" + json.dumps(evidence, default=str, indent=2),
            f"Runbook source:\n{runbook['source']}",
            f"Runbook content:\n{runbook['content']}",
        )
    )


def _validate_question(question: str) -> None:
    if not isinstance(question, str) or not question.strip():
        raise ValueError("A non-empty incident question is required.")
    if len(question) > MAX_QUESTION_CHARACTERS:
        raise ValueError(
            f"The incident question must be {MAX_QUESTION_CHARACTERS} characters or fewer."
        )


def _function_changed_after_latest_error(
    metadata: dict[str, Any], events: list[dict[str, Any]]
) -> bool:
    last_modified = _parse_iso_timestamp(metadata.get("last_modified"))
    event_times = [
        timestamp
        for event in events
        if (timestamp := _parse_iso_timestamp(event.get("timestamp"))) is not None
    ]
    return bool(last_modified and event_times and last_modified > max(event_times))


def _parse_iso_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None
