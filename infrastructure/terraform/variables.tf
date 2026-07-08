################################################################################
# Terraform input variables for the Privacy Platform GCP infrastructure.
################################################################################

variable "project_id" {
  description = "The GCP project ID where resources will be deployed"
  type        = string

  validation {
    condition     = length(var.project_id) > 0
    error_message = "The project_id must not be empty."
  }
}

variable "region" {
  description = "The GCP region for resource deployment"
  type        = string
  default     = "us-central1"

  validation {
    condition     = can(regex("^[a-z]+-[a-z]+\\d+$", var.region))
    error_message = "The region must be a valid GCP region format (e.g., us-central1)."
  }
}

variable "bucket_name" {
  description = "The name of the GCS bucket for file uploads"
  type        = string
  default     = "privacy-platform-uploads"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9._-]{2,220}[a-z0-9]$", var.bucket_name))
    error_message = "Bucket name must be globally unique and follow GCS naming conventions."
  }
}

variable "environment" {
  description = "Deployment environment (development, staging, production)"
  type        = string
  default     = "development"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}
