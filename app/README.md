# Application

The first implementation is intentionally small:

1. A synthetic `orders-api` Lambda that demonstrates one known failure.
2. Three deterministic, read-only diagnostic tools in `diagnostic_tools/`:
   - `get_alarm_state`
   - `get_recent_error_logs`
   - `get_safe_function_metadata`
3. One Bedrock-powered agent workflow.
4. A Streamlit page that displays the agent's evidence-based incident report.

No multi-agent design, external MCP server, Kubernetes integration, or automatic remediation belongs in Phase 1.

## Tool configuration

The tools accept only the logical service name `orders-api`; callers cannot supply an AWS function name, alarm name, log group, Region, filter pattern, or arbitrary AWS API name. At runtime, set these non-secret environment variables from the Terraform outputs:

```text
AWS_REGION=us-west-2
COPILOT_FUNCTION_NAME=aws-cloud-operations-copilot-development-orders-api
COPILOT_LOG_GROUP_NAME=/aws/lambda/aws-cloud-operations-copilot-development-orders-api
COPILOT_ALARM_NAME=aws-cloud-operations-copilot-development-orders-api-missing-config
```

The `get_safe_function_metadata` response deliberately excludes Lambda environment variables. Log messages are bounded and redact common `password`, `token`, `api_key`, and `secret` assignments before they can reach a model or interface.

## Single-agent workflow

`agent/workflow.py` uses LangGraph to enforce a fixed safe order:

```text
question -> read-only alarm/log/metadata tools -> fixed S3 runbook -> one Bedrock Converse call -> report
```

The agent uses Amazon Nova Lite (`amazon.nova-lite-v1:0`) with a maximum 350-token response and a low temperature **only when the alarm is `ALARM`, a matching configuration error is present, and the Lambda has not changed since that error**. Otherwise, a deterministic evidence gate returns either a no-active-incident or recovery-in-progress report at zero model-token cost. It cannot choose another AWS resource, invoke a tool with arbitrary input, or perform remediation. AgentCore deployment remains a later phase; this Streamlit interface runs locally.

## Run the local Streamlit interface

The interface is local-only: `.streamlit/config.toml` binds it to `127.0.0.1`, so it does not deploy an application or create a hosting bill. It performs AWS reads only after you press **Investigate**.

From the repository root, activate the existing virtual environment and set the non-secret resource names from Terraform:

```powershell
.\.venv\Scripts\Activate.ps1

$env:AWS_REGION = "us-west-2"
$env:COPILOT_FUNCTION_NAME = terraform -chdir=infra output -raw orders_api_function_name
$env:COPILOT_LOG_GROUP_NAME = terraform -chdir=infra output -raw orders_api_log_group_name
$env:COPILOT_ALARM_NAME = terraform -chdir=infra output -raw orders_api_missing_config_alarm_name
$env:COPILOT_RUNBOOK_BUCKET = terraform -chdir=infra output -raw runbook_bucket_name

streamlit run streamlit_app.py
```

Use the local URL Streamlit opens (normally `http://127.0.0.1:8501`). Each submitted question creates one fixed investigation. Healthy evidence and recently recovering evidence use no Bedrock tokens; an active documented incident makes at most one model call with a 350-output-token cap. This is a guardrail, not a promise of a specific AWS bill.
