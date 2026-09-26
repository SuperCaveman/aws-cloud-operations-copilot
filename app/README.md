# Application

The first implementation is intentionally small:

1. A synthetic `orders-api` Lambda that demonstrates one known failure.
2. Three deterministic, read-only diagnostic tools.
3. One Bedrock-powered agent workflow.
4. A Streamlit page that displays the agent's evidence-based incident report.

No multi-agent design, external MCP server, Kubernetes integration, or automatic remediation belongs in Phase 1.
