# Step-by-step build plan

Do one phase at a time. Do not create AWS resources or continue to the next phase until the prior checkpoint is complete.

## Phase 0 - Decide the safe MVP

**Goal:** Build a development-only, read-only incident-triage copilot.

**First use cases:**

1. Explain why a Pod is in `CrashLoopBackOff`.
2. Explain why a Deployment rollout is stuck.
3. Explain why an HPA is not scaling a workload.
4. Summarize a CloudWatch or Prometheus alert with cited evidence.

**Out of scope:** autonomous remediation, production cluster access, arbitrary shell execution, and access to Secret values.

**Checkpoint:** You can state the four use cases and the four out-of-scope items in your own words.

## Phase 1 - Prepare a safe AWS lab

**You do:**

1. Use a separate AWS learning account or an isolated sandbox environment.
2. Enable MFA and use IAM Identity Center or temporary credentials; do not create long-lived access keys for application code.
3. Create a small monthly AWS Budget with email alerts.
4. Install and authenticate the AWS CLI, Terraform, Docker, `kubectl`, and Git.
5. Confirm the intended AWS Region supports EKS and Bedrock AgentCore before provisioning.

**Checkpoint:** `aws sts get-caller-identity` succeeds using temporary credentials, and your budget alert exists.

## Phase 2 - Create the EKS development platform

**You do:**

1. Write Terraform for a VPC, private subnets, EKS, managed node group, ECR, CloudWatch logging, and IAM roles.
2. Keep the cluster small and tag every resource with `Project=eks-platform-operations-copilot` and `Environment=dev`.
3. Configure `kubectl` for the development cluster.
4. Create a `demo-apps` namespace and a non-admin Kubernetes ServiceAccount for diagnostics.
5. Create separate RBAC roles for viewing Pods/Deployments/Events/HPA/logs and for proposing changes. Do not grant `cluster-admin`.

**Checkpoint:** You can deploy a basic web service, inspect it with `kubectl`, and prove that the diagnostic ServiceAccount cannot read a Secret or modify a Deployment.

## Phase 3 - Add intentionally broken training workloads

**You do:**

1. Deploy a healthy sample API.
2. Add one deliberately broken version with a missing ConfigMap key.
3. Add a second scenario with an incorrect readiness probe.
4. Add a third scenario with missing resource requests so the HPA cannot make a useful scaling decision.
5. Write a short runbook for each scenario: symptoms, evidence to gather, root cause, safe fix, and validation step.

**Checkpoint:** You can diagnose each scenario manually with `kubectl get`, `kubectl describe`, `kubectl logs`, and metrics.

## Phase 4 - Build deterministic read-only diagnostic tools

**You do:**

1. Implement small tools with strict input schemas: `get_workload_status`, `get_recent_events`, `get_container_logs`, `get_resource_config`, and `get_hpa_status`.
2. Return structured JSON, not prose.
3. Enforce namespace allow-lists in both code and Kubernetes RBAC.
4. Redact sensitive values before output and never call the Kubernetes Secret API.
5. Unit-test tool validation, denied namespaces, missing resources, and error messages.

**Checkpoint:** A tool can return facts for `demo-apps`, refuses another namespace, and cannot mutate a workload.

## Phase 5 - Add runbook retrieval and the AI agent

**You do:**

1. Put only synthetic, non-sensitive runbooks into an S3-backed knowledge base.
2. Build the agent in Amazon Bedrock AgentCore.
3. Give the agent a system instruction that requires it to call tools for cluster facts, separate evidence from inference, cite the relevant runbook, and state uncertainty.
4. Connect the agent only to the Phase 4 tools.
5. Record traces, latency, tool errors, and token use in CloudWatch.

**Checkpoint:** For each broken workload, the agent identifies the correct evidence and recommends the documented fix without inventing cluster data.

## Phase 6 - Add the controlled GitOps proposal path

**You do:**

1. Store Kubernetes manifests or Helm/Kustomize configuration in Git.
2. Give the agent a tool that can create a branch and draft a pull request, but cannot merge it.
3. Require the agent to show a manifest diff and validation plan before it may draft a PR.
4. Use a GitOps controller or manual reviewed deployment to apply merged changes to development only.
5. Document rollback and post-change validation steps.

**Checkpoint:** A human can review a proposed fix, merge it, see the development workload recover, and revert it if necessary.

## Phase 7 - Turn it into a portfolio project

**You do:**

1. Add an architecture diagram and a one-page threat model.
2. Add a permissions matrix that shows what every identity can and cannot do.
3. Create an evaluation set of at least 20 incident prompts, expected evidence, expected tool calls, and pass/fail criteria.
4. Create a CloudWatch dashboard for agent latency, failures, tool use, and estimated cost.
5. Record a three-minute demo: incident, evidence, recommendation, pull request, approval, recovery.

**Checkpoint:** A hiring manager can understand the problem, safety model, architecture, and result without opening the source code.
