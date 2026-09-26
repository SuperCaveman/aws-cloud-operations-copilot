# Tool and permission contracts

## Design principle

Every agent tool is a narrow API with a single job. The agent cannot send arbitrary `kubectl` commands, execute shell commands, or use credentials with broader permission than the tool requires.

## Initial tools

| Tool | Allowed input | Returns | Must not do |
|---|---|---|---|
| `get_workload_status` | Namespace and workload name | Deployment, ReplicaSet, Pod phase, restart count, conditions | Read Secrets, change replica count, restart Pods |
| `get_recent_events` | Allowed namespace and workload selector | Recent warning/normal events | Query arbitrary namespaces |
| `get_container_logs` | Allowed namespace, pod, container, short time window | Redacted bounded log excerpt | Stream logs forever or expose secrets |
| `get_resource_config` | Allowed namespace and workload name | Requests, limits, probes, mounted ConfigMap names | Return Secret data |
| `get_hpa_status` | Allowed namespace and HPA name | Current/desired replicas and observed metrics | Modify HPA configuration |
| `search_runbook` | Incident description | Cited runbook passages | Search private production documentation in the MVP |
| `draft_gitops_pr` | Validated manifest patch and explanation | Branch and draft PR URL | Merge, deploy, or edit any unapproved file |

## Identities

| Identity | Permission | Boundary |
|---|---|---|
| Engineer | Use the UI and view only their authorized environment | Authenticated by the identity layer |
| Agent runtime | Invoke the approved tools and retrieve runbooks | Cannot call Kubernetes directly with admin permissions |
| Diagnostic tool ServiceAccount | Read selected resource types only in `demo-apps` | No writes, no Secrets, no other namespaces |
| GitHub/Git provider bot | Create branches and draft PRs | No merge permission |
| GitOps controller | Applies reviewed Git changes to development | Uses its own deployment identity; the agent cannot impersonate it |

## Required answer format

Every incident response must distinguish:

1. **Observed evidence** - direct tool output.
2. **Likely cause** - clearly labeled inference.
3. **Recommended next step** - a safe, reversible action.
4. **Risk and confidence** - why the recommendation may be incomplete.
5. **References** - the tool results and runbook passages used.
