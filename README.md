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

## What the agent automates

1. Collects facts from approved, read-only tools: alarm state, recent bounded error logs, and safe deployment metadata.
2. Finds the relevant runbook passage.
3. Produces an incident summary that separates observed evidence from its likely-cause inference.
4. Recommends a safe manual next step for the engineer.

The agent never changes a Lambda function, reads secrets, runs arbitrary commands, or uses production credentials.

## Start here

- [Active scope](docs/00-active-scope.md)
- [Plain-language system flow](docs/01-plain-language-system-flow.md)
- [Step-by-step build plan](docs/02-step-by-step-build.md)
- [Tool and permission contracts](docs/03-tool-and-permission-contracts.md)

## Repository map

```text
app/     Future agent, read-only tool, and Streamlit code
docs/    Scope, plain-language design, build plan, and safeguards
infra/   Future Terraform for the minimal AWS development environment
```
