output "orders_api_function_name" {
  description = "The allow-listed synthetic Lambda function name for later read-only diagnostic tools."
  value       = aws_lambda_function.orders_api.function_name
}

output "orders_api_log_group_name" {
  description = "The allow-listed development log group for later read-only diagnostic tools."
  value       = aws_cloudwatch_log_group.orders_api.name
}

output "orders_api_missing_config_alarm_name" {
  description = "The allow-listed synthetic development alarm for later read-only diagnostic tools."
  value       = aws_cloudwatch_metric_alarm.orders_api_missing_config.alarm_name
}

output "runbook_bucket_name" {
  description = "Private, versioned S3 bucket containing only the synthetic Phase 1 runbook."
  value       = aws_s3_bucket.runbooks.bucket
}

output "orders_api_runbook_s3_uri" {
  description = "The single allow-listed runbook source for the Phase 1 agent."
  value       = "s3://${aws_s3_bucket.runbooks.bucket}/${aws_s3_object.orders_api_runbook.key}"
}
