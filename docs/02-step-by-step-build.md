# Step-by-step build plan

Complete one checkpoint at a time. Stop after each checkpoint and verify it before starting the next one.

## Step 1 - Confirm the safe lab

**You do:**

1. Use a separate AWS learning account or clearly isolated development environment.
2. Enable MFA and use IAM Identity Center or temporary credentials.
3. Create a small monthly AWS Budget with an email alert.
4. Install and authenticate the AWS CLI, Python 3.11+, Git, and Terraform.

**Checkpoint:** `aws sts get-caller-identity` succeeds with temporary credentials, and you can see the budget alert.

## Step 2 - Define the synthetic incident

**You do:**

1. Create a short runbook named `orders-api-missing-config.md`.
2. Define one known, non-secret configuration key that the development Lambda expects.
3. Define the error message the sample Lambda will write when that key is absent.
4. Write the expected healthy behavior and recovery check.

**Checkpoint:** Another person could read the runbook and manually diagnose the incident without an AI agent.

## Step 3 - Create the minimal AWS application

**You do:**

1. Use Terraform to create a development Lambda named `orders-api`, its CloudWatch log group, and a CloudWatch alarm for the known error pattern.
2. Deploy a small Python handler that returns a normal response when its non-secret setting is present and logs a clear error when it is absent.
3. Trigger the safe synthetic failure in development only.
4. Verify the log line and alarm manually in the AWS console.

**Checkpoint:** You can cause and then resolve the sample incident without using an AI agent.

## Step 4 - Build the read-only diagnostic tools

**You do:**

1. Implement `get_alarm_state` to return the allowed alarm's state and reason.
2. Implement `get_recent_error_logs` to return a bounded, redacted error excerpt from the allowed log group.
3. Implement `get_safe_function_metadata` to return an allow-listed subset of Lambda metadata. Do not return environment-variable values.
4. Validate every input against an allow-list of development resource names.
5. Give the tool role only the three required read permissions.

**Checkpoint:** Each tool returns structured JSON for `orders-api`, refuses unknown resources, and has no write permission.

## Step 5 - Add runbook retrieval and the agent

**You do:**

1. Store only the synthetic runbook in an S3-backed knowledge base or another scoped retrieval store.
2. Build a single-agent workflow with Bedrock and the three deterministic tools.
3. Require the agent to call tools before asserting a fact about service health.
4. Require the response format: observed evidence, runbook reference, likely cause, safe next step, and confidence.
5. Capture tool errors, latency, and token use in CloudWatch.

**Checkpoint:** The agent diagnoses the synthetic incident correctly and does not invent evidence.

## Step 6 - Add a simple interface and evaluation set

**You do:**

1. Add a Streamlit page with one question box and a readable incident report.
2. Create ten test prompts: five correct incidents, three unknown-service attempts, one request for a secret, and one request to change a resource.
3. Record expected tool calls and expected refusals for every test.
4. Demonstrate that the agent refuses unsupported or unsafe requests.

**Current implementation:** `streamlit_app.py` supplies the local-only form. It runs one fixed workflow only after the engineer submits a question and displays the model-token usage for that request. The ten-prompt mocked evaluation set is implemented in `app/tests/test_evaluation_prompts.py`; a recorded demo remains to be co

**Checkpoint:** You can record a short demo from alert to evidence-based diagnosis without the agent changing AWS.
