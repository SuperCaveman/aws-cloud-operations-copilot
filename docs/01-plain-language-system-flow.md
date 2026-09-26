# Plain-language system flow

## One-sentence explanation

The copilot watches a development Kubernetes cluster, gathers the same evidence a platform engineer would gather during an incident, explains what it found, and prepares a safe proposed fix for a human to review.

## The parts and what each one does

| Part | Plain-language job | What it sends next |
|---|---|---|
| Engineer | Asks a question or receives an alert. | A question such as “Why is checkout-api failing?” |
| Web UI | Gives the engineer a safe place to ask questions and view the answer. | The question and the engineer identity to the agent. |
| Identity layer | Confirms who the engineer is and which cluster/environment they may view. | An authenticated request with the engineer's role. |
| AgentCore agent | Decides which approved, read-only diagnostic tools are needed. It does not receive cluster-admin access. | Tool requests, such as “get pod events” or “read the checkout-api runbook.” |
| Diagnostic tools | Call the Kubernetes API and monitoring systems using narrowly scoped permissions. | Structured facts: status, events, logs, metrics, and errors. |
| Runbook knowledge base | Finds relevant operating procedures and standards. | The exact runbook passages used in the response. |
| AgentCore agent | Combines the facts and runbook passages into an evidence-based explanation. | An incident report and, optionally, a proposed Git change. |
| Git repository | Stores a proposed manifest/Helm/Kustomize change in a branch. | A pull request for human review. |
| Human reviewer | Checks the evidence and proposed change. | Approval or rejection. |
| GitOps deployment system | Applies an approved, merged change to the **development** cluster. | The updated desired cluster state. |

## Example: a pod keeps restarting

1. A developer notices that `checkout-api` is repeatedly restarting.
2. They ask: **“Why is checkout-api restarting in dev?”**
3. The identity layer confirms that they are allowed to view the development namespace.
4. The agent calls only approved read-only tools:
   - get the Deployment and Pod status;
   - get recent Kubernetes events;
   - retrieve the container logs from the failing pod;
   - retrieve CPU/memory requests, limits, and HPA status;
   - search the runbook for `CrashLoopBackOff`.
5. The tools return structured facts. For example: the readiness probe is returning `503`, events show a missing configuration key, and the logs show the application stopped during startup.
6. The agent writes a report:
   - **Observed:** the pod is in `CrashLoopBackOff`.
   - **Evidence:** the specific event, log message, and configuration reference.
   - **Likely cause:** a missing non-secret configuration value.
   - **Recommendation:** add the documented ConfigMap key and verify the readiness endpoint.
   - **Confidence:** medium or high, depending on the evidence.
7. If asked, the agent creates a branch containing a proposed manifest change. It does **not** merge it.
8. A human reviews the pull request. Only a normal GitOps review and merge can change the development cluster.

## What is AI doing, and what is ordinary automation doing?

| Work | Owner | Reason |
|---|---|---|
| Read resource objects, events, logs, and metrics | Ordinary deterministic tools | The answer must be factual and repeatable. |
| Search runbooks | Retrieval system | The answer needs the organization's documented guidance. |
| Decide which diagnostics to request and explain their meaning | AI agent | This is the ambiguous, investigative part of incident triage. |
| Produce a proposed patch and incident summary | AI agent | It can accelerate drafting, but a person must judge correctness. |
| Apply a change to the cluster | GitOps system after human approval | Cluster changes must be controlled, auditable, and reversible. |

## Safety rule

Permissions, not prompts, enforce safety. The agent's Kubernetes identity is read-only, cannot read Secret values, and has access only to a development namespace in the first release.
