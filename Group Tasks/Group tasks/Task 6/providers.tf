terraform {
  required_version = ">= 1.9.8, < 2.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.100.0"
    }
  }
}

# Empty-state offline plans use non-secret placeholders and make no AWS lookups.
# This is not a deployment or an authenticated infrastructure availability check.
provider "aws" {
  region                      = var.region
  access_key                  = var.offline_plan ? "offline-not-a-real-access-key" : null
  secret_key                  = var.offline_plan ? "offline-not-a-real-secret-key" : null
  skip_credentials_validation = var.offline_plan
  skip_requesting_account_id  = var.offline_plan
  skip_metadata_api_check     = var.offline_plan
  skip_region_validation      = var.offline_plan
  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
