# Tool and permission contracts

## Design principle

Tools return facts. The agent explains the facts. No tool can perform a write operation, invoke arbitrary AWS APIs, read secrets, or access production.

## Initial tool set

| Tool | Allowed input | Returns | Must not do |
|---|---|---|---|
| `get_alarm_state` | The allow-listed `orders-api` development alarm name | Alarm state, state reason, timestamp, metric summary | Enable/disable/update/delete alarms |
| `get_recent_error_logs` | The allow-listed development log group and a short time range | Bounded, redacted error lines and timestamps | Query other log groups, retrieve unbounded logs, return sensitive values |
| `get_safe_function_metadata` | The allow-listed `orders-api` function name | Runtime, memory, timeout, state, last-update time | Return environment variables, code, tags, or policy documents |
| `search_runbook` | Incident description | Cited synthetic runbook passage | Search private or production documents |

## IAM boundary

The diagnostic-tool role receives only the narrowly needed read actions for the named development alarm, log group, and Lambda metadata. It receives no permissions for:

- Lambda update, invoke, delete, alias, or environment-variable actions.
- CloudWatch alarm changes or log deletion.
- IAM, S3 object reads outside the runbook prefix, DynamoDB, EKS, Secrets Manager, Systems Manager Parameter Store, or shell access.

## Required agent response

Every answer must include:

1. **Observed evidence** - direct tool results.
2. **Runbook reference** - the retrieved operating guidance.
3. **Likely cause** - clearly labeled inference, not a fact.
4. **Safe next step** - a manual, reversible engineer action.
5. **Confidence and limits** - what the evidence does and does not prove.

## Required refusals

The agent must refuse requests to:

- change, restart, invoke, delete, scale, or deploy AWS resources;
- reveal credentials, secret values, environment variables, or private data;
- query non-allow-listed or production resources;
- run arbitrary CLI, shell, or code-execution commands.
