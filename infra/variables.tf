variable "aws_region" {
  description = "AWS Region for the synthetic development environment."
  type        = string
  default     = "us-west-2"
}

variable "project_name" {
  description = "Short name used to identify the project's AWS resources."
  type        = string
  default     = "aws-cloud-operations-copilot"
}

variable "environment" {
  description = "The sole environment this Phase 1 configuration can create."
  type        = string
  default     = "development"

  validation {
    condition     = var.environment == "development"
    error_message = "Phase 1 is development-only. Set environment to development."
  }
}

variable "inject_missing_config" {
  description = "Manual demonstration switch. When true, the Lambda omits its non-secret development setting and produces the documented synthetic error."
  type        = bool
  default     = false
}
