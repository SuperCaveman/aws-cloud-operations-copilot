# Plain-language system flow

## One-sentence explanation

The copilot acts like a junior on-call engineer: it gathers the same evidence a person would gather, checks the written runbook, and explains the likely problem. It cannot fix anything by itself.

## This part does this, then sends it to this part

| Part | This part does this | Then it sends |
|---|---|---|
| Engineer | Asks why `orders-api` is unhealthy. | The question to the web interface. |
| Streamlit web interface | Displays the question and the final report. | The question to the agent. |
| Agent | Decides which approved facts it needs before answering. | Requests to read-only AWS tools and the runbook search. |
| Alarm tool | Reads whether the relevant CloudWatch alarm is `OK`, `ALARM`, or `INSUFFICIENT_DATA`, plus the reason. | Structured alarm facts to the agent. |
| Log tool | Retrieves a short, redacted set of recent error lines from the correct CloudWatch log group. | Structured log evidence to the agent. |
| Metadata tool | Retrieves only safe metadata, such as the Lambda runtime, memory, timeout, state, and last update time. | Structured deployment facts to the agent. |
| Runbook retrieval | Finds the documentation section that matches the error. | The relevant runbook passage and source reference to the agent. |
| Agent | Separates facts from inference, explains the likely cause, and recommends a manual next step. | A cited incident report to the engineer. |
| Engineer | Reviews the result and makes any change manually. | A normal reviewed AWS change outside the agent. |

## Example incident

1. The development `orders-api` Lambda receives a request.
2. It cannot find a required non-secret configuration value and logs a predictable application error.
3. A CloudWatch alarm enters `ALARM`.
4. The engineer asks: **“Why is orders-api failing?”**
5. The agent calls the alarm tool, log tool, metadata tool, and runbook search.
6. It responds:
   - **Observed:** The alarm changed at a specific time, and the last three error lines show the missing configuration key.
   - **Runbook:** The deployment-validation runbook says to verify the named non-secret configuration value before re-deploying.
   - **Likely cause:** The development deployment omitted that configuration value.
   - **Safe next step:** An engineer should update the development configuration through the normal deployment process, then confirm the alarm returns to `OK`.
   - **Confidence:** High, because the alarm, log evidence, and runbook agree.

## What is AI, and what is not?

| Work | Owner | Why |
|---|---|---|
| Read alarms, logs, and metadata | Deterministic AWS tools | Facts must be repeatable. |
| Retrieve a runbook | Search/retrieval | The response needs documented operating guidance. |
| Decide what evidence to request and explain it | AI agent | Investigation and explanation require judgment. |
| Change AWS configuration | Human engineer | Changes require explicit review and accountable approval. |

## Safety rule

The safety boundary is enforced by IAM. The agent uses a role that can read only the named development resources. It cannot invoke write APIs, retrieve secret values, or use arbitrary shell commands.
