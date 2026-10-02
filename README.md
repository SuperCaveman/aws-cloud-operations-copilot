# AWS Cloud Operations Copilot

A safe, AWS-native AI assistant that investigates application incidents using CloudWatch evidence and operating runbooks.

## Active scope: Phase 1 only

This repository intentionally stays close to the study material:

- Amazon Bedrock model invocation
- LangGraph-style agent orchestration
- AWS Lambda tools
- CloudWatch logs and alarms
- S3-backed runbooks / retrieval
- A simple Streamlit interface
- IAM least privilege and human review

The project investigates a synthetic failing service named `orders-api`. It does not modify AWS resources, deploy changes, or touch production.

Kubernetes/EKS, OpenShift, GitOps, pull-request automation, and industrial/utility integrations are future extensions. They are **not part of Phase 1**.

## How the architecture works

```text
Engineer question
    -> LangGraph workflow
    -> three fixed, read-only AWS checks (alarm, logs, safe Lambda metadata)
    -> one fixed S3 runbook
    -> evidence safety gate
       -> no active incident / recovery may be underway: deterministic report
       -> active documented incident: one bounded Amazon Bedrock explanation
    -> engineer reviews a safe manual next step
```

The agent never changes a Lambda function, reads secrets, runs arbitrary commands, or uses production credentials.

## Decision guide: each part, why it exists, and what it sends next

| Part | Decision | Why this choice | What it sends to the next part |
|---|---|---|---|
| Synthetic `orders-api` Lambda | Model one known development-only missing-configuration failure. | A repeatable incident is safer and easier to explain than a vague demo. | A health response or a documented error log. |
| CloudWatch Logs and alarm | Use the error log as evidence and an alarm as the incident signal. | These are normal AWS operational signals; they make the AI answer evidence-based. | Bounded matching log events and the alarm state. |
| Read-only diagnostic tools | Allow only `orders-api`, its one alarm, one log group, and safe Lambda metadata. | The model cannot select an arbitrary AWS resource or call a write API. | Structured facts, with common secret-looking log values redacted. |
| S3 runbook retrieval | Read exactly one versioned, private runbook object. | Operating guidance stays outside the prompt and cannot be replaced by a caller-selected document. | Runbook text and an S3 source reference. |
| LangGraph workflow | Enforce the sequence: evidence first, runbook second, answer last. | The workflow is code, so its order and branches can be tested. | An incident classification and the bounded context for a report. |
| Evidence safety gate | Call Bedrock only if the alarm is `ALARM`, a matching recent error exists, and the Lambda has not changed since that error. | It avoids a model inventing an incident from old or healthy evidence and avoids needless model cost. | Either a deterministic status report or the active-incident evidence bundle. |
| Amazon Bedrock / Nova Lite | Generate one short explanation only for the active, documented incident. | AI is useful for explaining evidence and runbook guidance, not for changing infrastructure. | A report with facts, inference, safe next step, and limits. |
| Human engineer | Reviews and performs any recovery through the normal deployment process. | Accountable approval remains with a person. | A verified health check and CloudWatch recovery signal. |

## What the copilot automates

1. Collects facts from approved, read-only tools: alarm state, recent bounded error logs, and safe deployment metadata.
2. Retrieves the applicable runbook.
3. Determines whether there is an active incident, no incident, or a recently changed service that may already be recovering.
4. Produces an incident summary that separates observed evidence from its likely-cause inference only when the evidence qualifies.
5. Recommends a safe manual next step for the engineer.

It does **not** automate remediation. That boundary is deliberate.

## Start here

- [Active scope](docs/00-active-scope.md)
- [Plain-language system flow](docs/01-plain-language-system-flow.md)
- [Step-by-step build plan](docs/02-step-by-step-build.md)
- [Tool and permission contracts](docs/03-tool-and-permission-contracts.md)
- [Deployed AWS evidence and repeatable verification](docs/05-deployment-evidence.md)
- [LinkedIn post draft for the finished Phase 1 demo](docs/06-linkedin-post-draft.md)
- [Offline prompt evaluation plan](docs/07-evaluation-plan.md)

## Repository map

```text
app/     Lambda, read-only diagnostic tools, LangGraph workflow, and local Streamlit code
docs/    Scope, architecture, safeguards, deployment evidence, and presentation material
infra/   Terraform for the minimal AWS development environment
```
# aws-cloud-operations-copilot
A safe AWS Bedrock-powered incident investigation copilot
