# Active scope: Phase 1

## The project we are building now

An engineer asks why the synthetic `orders-api` service is unhealthy. The copilot gathers evidence from CloudWatch and a small set of safe AWS metadata, retrieves the matching runbook, and explains what the engineer should check next.

## The first incident scenario

`orders-api` is a small Lambda-backed API. A deliberately bad development deployment causes an error alarm and a predictable error message in CloudWatch Logs.

The copilot should answer questions such as:

- “Why is `orders-api` failing in development?”
- “What evidence supports that conclusion?”
- “Which runbook step applies?”
- “What safe manual fix should I make?”

## Definition of done

The Phase 1 demo is complete when the agent:

1. Calls approved read-only tools for alarm state, log evidence, and safe function metadata.
2. Finds and cites the applicable synthetic runbook.
3. States observed evidence separately from its inference.
4. Recommends a reversible manual action.
5. Does not expose sensitive data or make any AWS change.

## Explicitly deferred

- EKS, Kubernetes, OpenShift, containers, Helm, and GitOps.
- Automatic remediation, pull requests, CI/CD, and production deployment.
- DynamoDB incident history, multi-agent routing, and external MCP integrations.
- Customer, water-utility, medical, or other real operational data.
