# EKS Platform Operations Copilot

A safe, AWS-native AI assistant for diagnosing Kubernetes workload incidents and proposing GitOps fixes.

This is **not** a cluster-admin bot. The agent can collect evidence, explain likely causes, retrieve relevant runbooks, and create a proposed change. A human must approve and merge every cluster change.

## Why this project

The portfolio goal is to demonstrate all three layers of modern platform engineering:

1. **Kubernetes administration** - workloads, RBAC, autoscaling, networking, and observability.
2. **AWS platform engineering** - EKS, IAM, VPC, CloudWatch, ECR, Terraform, and Bedrock AgentCore.
3. **Safe agent engineering** - tool contracts, least privilege, evidence-based answers, evaluations, audit trails, and human approval.

## What the agent automates

- Collects read-only workload evidence: pod status, deployment details, Kubernetes events, logs, resource requests/limits, and HPA state.
- Retrieves applicable runbook sections and cluster standards.
- Correlates that evidence with CloudWatch or Prometheus alerts.
- Produces an incident summary with the evidence it used, likely causes, confidence, and recommended next steps.
- Drafts a Kubernetes manifest or Helm/Kustomize change in a Git branch for human review.

## What the agent never automates in the first release

- `kubectl apply`, delete, restart, scale, drain, or upgrade operations.
- Reading Secret values or placing credentials in prompts, logs, or Git.
- Merging pull requests or deploying to any cluster.
- Direct production access.

Read [the plain-language system flow](docs/01-plain-language-system-flow.md) before building anything.

## Repository map

```text
app/     Future agent and read-only diagnostic-tool code
docs/    System explanation, safeguards, and step-by-step build plan
infra/   Future Terraform for AWS and EKS resources
```

## Build order

1. Establish an isolated AWS lab and budget controls.
2. Create a small EKS development cluster with Terraform.
3. Deploy deliberately unhealthy sample workloads.
4. Create read-only Kubernetes diagnostic tools.
5. Add Bedrock AgentCore and a runbook knowledge base.
6. Add evaluations, dashboards, and a GitOps proposal workflow.

The complete checklist is in [docs/02-step-by-step-build.md](docs/02-step-by-step-build.md).
