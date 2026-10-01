# Deployment evidence and repeatable verification

## What this proves

The Phase 1 development environment was deployed to AWS in `us-west-2` and checked on **2026-10-01**. The deployed environment contains:

- the synthetic `orders-api` Lambda;
- its CloudWatch log group and missing-configuration metric alarm;
- a private, versioned S3 runbook object; and
- no alarm actions or automatic remediation.

The final recovery check returned a healthy Lambda response and the alarm state was `OK` at `2026-10-01 15:43:30 America/Los_Angeles`.

This is intentionally a sanitized record. It does not include account IDs, credentials, access keys, session tokens, Terraform state, secret values, or a complete bucket name. The repository's `.gitignore` excludes local credential and Terraform-state files.

## How to verify it again

Run these commands from the repository root while signed in with authorized AWS credentials. They make read-only AWS API calls, except the Lambda invoke below, which executes the project's harmless development health check.

```powershell
terraform -chdir=infra output

$functionName = terraform -chdir=infra output -raw orders_api_function_name
$alarmName = terraform -chdir=infra output -raw orders_api_missing_config_alarm_name

aws lambda get-function --function-name $functionName --region us-west-2
aws cloudwatch describe-alarms --alarm-names $alarmName --region us-west-2
aws lambda invoke --function-name $functionName --region us-west-2 response.json
Get-Content response.json
Remove-Item response.json
```

Expected health-check body:

```json
{
  "service": "orders-api",
  "status": "healthy",
  "environment": "development"
}
```

Do not commit `response.json`, Terraform state, `terraform.tfvars`, `.env` files, AWS CLI credential files, console exports, or screenshots that show an account ID.

## Stronger public proof after Phase 1 is complete

For a portfolio reviewer, the Terraform, tests, and this reproducible verification path are useful evidence, but they cannot independently prove who deployed a resource. The strongest next step is a GitHub Actions workflow that uses GitHub-to-AWS OIDC (not long-lived access keys) to run a read-only verification job. Its visible workflow run can show the deploy revision and checks without exposing credentials.

Before making a public post, add two sanitized screenshots to `docs/images/`:

1. Lambda console showing the function name, Region, and successful test response, with the account ID obscured.
2. CloudWatch alarm history showing the deliberate `ALARM` event and return to `OK`, again with the account ID obscured.

Those screenshots support the story; they are not a substitute for access controls, Terraform code, or reproducible checks.
