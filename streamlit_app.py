"""Local-only Streamlit interface for the Phase 1 Cloud Operations Copilot."""

from __future__ import annotations

import os
from typing import Any

import boto3
import streamlit as st
from botocore.exceptions import BotoCoreError, ClientError

from app.agent import MAX_OUTPUT_TOKENS, build_incident_graph
from app.diagnostic_tools import AllowedResources, ConfigurationError, build_aws_tools
from app.runbook_retrieval import build_aws_runbook_retriever


def get_runbook_bucket_from_environment() -> str:
    """Return the sole runbook bucket without accepting a browser-supplied value."""
    bucket_name = os.getenv("COPILOT_RUNBOOK_BUCKET")
    if not bucket_name:
        raise ConfigurationError("Missing required runtime setting: COPILOT_RUNBOOK_BUCKET")
    return bucket_name


def build_workflow_from_environment() -> Any:
    """Build the fixed workflow only after a user submits the local form."""
    resources = AllowedResources.from_environment()
    runbook_retriever = build_aws_runbook_retriever(
        bucket_name=get_runbook_bucket_from_environment(),
        region=resources.region,
    )
    bedrock_client = boto3.client("bedrock-runtime", region_name=resources.region)
    return build_incident_graph(
        diagnostic_tools=build_aws_tools(resources),
        runbook_retriever=runbook_retriever,
        bedrock_client=bedrock_client,
    )


def model_usage_label(usage: dict[str, Any]) -> str:
    """Make the cost guard visible without displaying a price estimate."""
    total_tokens = usage.get("totalTokens", 0)
    if not total_tokens:
        return "Bedrock model use for this request: 0 tokens (evidence gate response)."
    return (
        f"Bedrock model use for this request: {total_tokens} tokens "
        f"(capped at {MAX_OUTPUT_TOKENS} output tokens)."
    )


def clear_result() -> None:
    for key in ("copilot_result", "copilot_error"):
        st.session_state.pop(key, None)


def render() -> None:
    st.set_page_config(page_title="AWS Cloud Operations Copilot", page_icon="☁️")
    st.title("AWS Cloud Operations Copilot")
    st.caption("Local Phase 1 lab — development-only, read-only investigation")

    st.info(
        "This page uses only the allow-listed `orders-api` development resources. "
        "It cannot reveal secrets or change AWS resources."
    )

    with st.form("incident_question"):
        question = st.text_area(
            "What do you want to investigate?",
            placeholder="Why is orders-api unhealthy in development?",
            max_chars=500,
        )
        submitted = st.form_submit_button("Investigate")

    if submitted:
        if not question.strip():
            st.warning("Enter a question before starting an investigation.")
        else:
            clear_result()
            try:
                with st.spinner("Collecting approved evidence..."):
                    workflow = build_workflow_from_environment()
                    st.session_state["copilot_result"] = workflow.invoke(
                        {"question": question.strip()}
                    )
            except ConfigurationError as error:
                st.session_state["copilot_error"] = (
                    "Local runtime configuration is incomplete: " + str(error)
                )
            except (BotoCoreError, ClientError):
                st.session_state["copilot_error"] = (
                    "AWS could not be reached. Confirm your authorized local AWS "
                    "session and the development resource settings, then try again."
                )
            except ValueError as error:
                st.session_state["copilot_error"] = str(error)

    if error_message := st.session_state.get("copilot_error"):
        st.error(error_message)

    if result := st.session_state.get("copilot_result"):
        st.subheader("Incident report")
        st.markdown(result["report"])
        st.caption(model_usage_label(result.get("usage", {})))
        with st.expander("Approved evidence used for this report"):
            st.json(result["evidence"])

    if "copilot_result" in st.session_state or "copilot_error" in st.session_state:
        st.button("Clear result", on_click=clear_result)

    st.divider()
    st.caption(
        "Cost guard: healthy and recovery-in-progress evidence returns a deterministic "
        "zero-token report. An active documented incident makes at most one bounded "
        "Bedrock model call. Streamlit runs only on this computer."
    )


if __name__ == "__main__":
    render()
