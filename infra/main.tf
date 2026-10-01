locals {
  name_prefix              = "${var.project_name}-${var.environment}"
  orders_api_function_name = "${local.name_prefix}-orders-api"
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Purpose     = "synthetic-ai-agent-study-incident"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

data "archive_file" "orders_api" {
  type        = "zip"
  source_file = "${path.module}/../app/lambda_src/app.py"
  output_path = "${path.module}/build/orders-api.zip"
}

resource "aws_cloudwatch_log_group" "orders_api" {
  name              = "/aws/lambda/${local.orders_api_function_name}"
  retention_in_days = 7
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "orders_api_execution" {
  name               = "${local.orders_api_function_name}-execution"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "orders_api_logging" {
  statement {
    sid    = "WriteOnlyToOrdersApiLogStream"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.orders_api.arn}:*"]
  }
}

resource "aws_iam_role_policy" "orders_api_logging" {
  name   = "write-orders-api-development-logs"
  role   = aws_iam_role.orders_api_execution.id
  policy = data.aws_iam_policy_document.orders_api_logging.json
}

resource "aws_lambda_function" "orders_api" {
  function_name    = local.orders_api_function_name
  description      = "Synthetic development-only incident source for the AWS Cloud Operations Copilot study project."
  filename         = data.archive_file.orders_api.output_path
  source_code_hash = data.archive_file.orders_api.output_base64sha256
  role             = aws_iam_role.orders_api_execution.arn
  handler          = "app.lambda_handler"
  runtime          = "python3.14"
  architectures    = ["arm64"]
  memory_size      = 128
  timeout          = 10

  environment {
    variables = var.inject_missing_config ? {} : {
      ORDERS_API_ENVIRONMENT = var.environment
    }
  }

  depends_on = [aws_iam_role_policy.orders_api_logging]
}

resource "aws_cloudwatch_log_metric_filter" "orders_api_missing_config" {
  name           = "${local.orders_api_function_name}-missing-config"
  log_group_name = aws_cloudwatch_log_group.orders_api.name
  pattern        = "\"ERROR\" \"orders-api configuration check failed\""

  metric_transformation {
    name          = "OrdersApiMissingConfig"
    namespace     = "CloudOpsCopilot/Development"
    value         = "1"
    default_value = "0"
    unit          = "Count"
  }
}

resource "aws_cloudwatch_metric_alarm" "orders_api_missing_config" {
  alarm_name          = "${local.orders_api_function_name}-missing-config"
  alarm_description   = "Synthetic development-only alarm for the documented orders-api configuration failure. No notification or remediation action is attached."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = aws_cloudwatch_log_metric_filter.orders_api_missing_config.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.orders_api_missing_config.metric_transformation[0].namespace
  period              = 60
  statistic           = "Sum"
  threshold           = 1
  treat_missing_data  = "notBreaching"
  actions_enabled     = false
}
