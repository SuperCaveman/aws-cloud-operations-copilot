# `orders-api`: missing development configuration

## Purpose

This is the single safe incident that Phase 1 teaches the copilot to investigate. It is synthetic: it uses no customer data, makes no production change, and is recoverable by restoring one non-secret development setting through the normal deployment process.

## Service and environment

| Item | Value |
|---|---|
| Service | `orders-api` |
| Environment | Development only |
| Compute | AWS Lambda |
| Required non-secret setting | `ORDERS_API_ENVIRONMENT` |
| Expected value | `development` |

## Normal behavior

When `ORDERS_API_ENVIRONMENT=development` is present, `orders-api` accepts its test request and returns a successful response. It emits an informational log line that includes `orders-api health check passed`.

## Synthetic failure

When the required setting is absent, the Lambda writes this exact error message and returns a controlled error response:

```text
ERROR orders-api configuration check failed: required non-secret setting ORDERS_API_ENVIRONMENT is not configured
```

The Phase 1 CloudWatch alarm is based on this known error pattern. It is scoped only to the `orders-api` development log group.

## What the engineer should observe

1. The development `orders-api` alarm is in `ALARM` after the error is logged.
2. Recent error logs contain the exact configuration-check message.
3. Safe Lambda metadata identifies the expected development function and its last update time. It must not expose environment-variable values.

## Manual diagnosis and recovery

1. Confirm the CloudWatch alarm state and its reason.
2. Read the bounded error-log excerpt for the development `orders-api` log group.
3. Match the error message to this runbook.
4. In the normal, human-reviewed deployment configuration, restore `ORDERS_API_ENVIRONMENT=development` for the development function. Do not put a value in a prompt, log, or source file.
5. Deploy through the normal Terraform workflow.
6. Invoke the development health-check path manually and confirm a successful response.
7. Confirm the error message stops appearing and the CloudWatch alarm returns to `OK`.

## What the agent may say

The agent may state that the alarm and log message are consistent with the required non-secret development setting being omitted. It must label that as an inference and cite this runbook.

## What the agent must not do

- Read or reveal Lambda environment-variable values.
- Change the function configuration or invoke the function to repair it.
- Query another service, environment, or account.
- Claim recovery succeeded without fresh alarm and log evidence.
