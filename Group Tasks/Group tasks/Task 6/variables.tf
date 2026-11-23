variable "project" {
  description = "Short project name used in resource names."
  type        = string
  default     = "document-ai"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,20}$", var.project))
    error_message = "Use 3-21 lowercase letters, digits or hyphens, starting with a letter."
  }
}
variable "environment" {
  description = "Deployment stage."
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Use dev, staging or prod."
  }
}
variable "region" {
  description = "AWS region; AMI and SSM parameters must be in this region."
  type        = string
  default     = "eu-west-1"
}
variable "offline_plan" {
  description = "True only for no-account, empty-state planning. Never apply in this mode."
  type        = bool
  default     = true
}
variable "ami_id" {
  description = "Future x86_64 Amazon Linux 2023 AMI; placeholder is for offline planning only."
  type        = string
  default     = "ami-00000000000000000"
  validation {
    condition     = can(regex("^ami-[a-f0-9]{17}$", var.ami_id))
    error_message = "Supply a long-form AMI ID."
  }
}
variable "instance_type" {
  description = "CPU host for single-process FastAPI, OCR, embeddings and INT8 STT. Size by actual workload."
  type        = string
  default     = "t3.large"
  validation {
    condition     = contains(["t3.large", "t3.xlarge", "m6i.large", "m6i.xlarge"], var.instance_type)
    error_message = "Choose an allowed x86_64 instance with at least 8 GiB RAM."
  }
}
variable "allowed_cidr" {
  description = "Trusted client's public IPv4 range. The documentation-only default cannot serve a real client."
  type        = string
  default     = "203.0.113.10/32"
  validation {
    condition     = can(cidrnetmask(var.allowed_cidr)) && !contains(["0.0.0.0/0", "0.0.0.0/1", "128.0.0.0/1"], var.allowed_cidr)
    error_message = "Use a restricted IPv4 CIDR, not unrestricted Internet ingress."
  }
}
variable "app_image" {
  description = "Future published Docker image. Build Task 5 Dockerfile and publish before deployment."
  type        = string
  default     = "ghcr.io/example/document-ai:latest"
  validation {
    condition     = can(regex("^[A-Za-z0-9./_:@-]+$", var.app_image)) && length(var.app_image) > 8
    error_message = "Supply a Docker image reference without whitespace or shell syntax."
  }
}
variable "openrouter_parameter_arn" {
  description = "Existing SSM SecureString parameter ARN holding the OpenRouter key. Secret value never enters Terraform."
  type        = string
  default     = "arn:aws:ssm:eu-west-1:000000000000:parameter/document-ai/openrouter"
  validation {
    condition     = can(regex("^arn:aws:ssm:[a-z0-9-]+:[0-9]{12}:parameter/[A-Za-z0-9/_-]+$", var.openrouter_parameter_arn))
    error_message = "Supply a valid SSM parameter ARN."
  }
}
variable "api_token_parameter_arn" {
  description = "Existing SSM SecureString parameter ARN for the application bearer token."
  type        = string
  default     = "arn:aws:ssm:eu-west-1:000000000000:parameter/document-ai/api-token"
  validation {
    condition     = can(regex("^arn:aws:ssm:[a-z0-9-]+:[0-9]{12}:parameter/[A-Za-z0-9/_-]+$", var.api_token_parameter_arn))
    error_message = "Supply a valid SSM parameter ARN."
  }
}
variable "disk_gib" {
  description = "Encrypted gp3 root volume; retained on instance termination, requiring later manual cleanup."
  type        = number
  default     = 50
  validation {
    condition     = var.disk_gib >= 30 && var.disk_gib <= 200 && floor(var.disk_gib) == var.disk_gib
    error_message = "Choose an integer from 30 to 200 GiB."
  }
}
