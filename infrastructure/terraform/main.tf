################################################################################
# Terraform configuration for AI-Powered Privacy Platform GCP resources
#
# This configuration provisions the Google Cloud infrastructure needed by the
# Privacy Platform:
#   - Cloud Storage bucket for uploaded files
#   - Cloud DLP API enablement for PII detection
#   - Pub/Sub topics for asynchronous event-driven processing
#   - IAM roles and service accounts for secure cross-service access
################################################################################

terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0, < 7.0"
    }
  }

  # Uncomment and configure for production state management:
  # backend "gcs" {
  #   bucket = "privacy-platform-terraform-state"
  #   prefix = "terraform/state"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# --------------------------------------------------------------------------
# Cloud Storage bucket for file uploads
# --------------------------------------------------------------------------

resource "google_storage_bucket" "uploads" {
  name                        = var.bucket_name
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  force_destroy               = var.environment != "production"

  versioning {
    enabled = var.environment == "production"
  }

  lifecycle_rule {
    condition {
      age = var.environment == "production" ? 90 : 30
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    service     = "privacy-platform"
    managed-by  = "terraform"
  }
}

# --------------------------------------------------------------------------
# Enable required GCP APIs
# --------------------------------------------------------------------------

resource "google_project_service" "dlp" {
  service            = "dlp.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "pubsub" {
  service            = "pubsub.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloudfunctions" {
  service            = "cloudfunctions.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloudbuild" {
  service            = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "run" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

# --------------------------------------------------------------------------
# Pub/Sub topics for event-driven architecture
# --------------------------------------------------------------------------

resource "google_pubsub_topic" "scan_events" {
  name = "scan-events"

  labels = {
    environment = var.environment
    service     = "privacy-platform"
  }

  depends_on = [google_project_service.pubsub]
}

resource "google_pubsub_topic" "scan_completed" {
  name = "scan-completed"

  labels = {
    environment = var.environment
    service     = "privacy-platform"
  }

  depends_on = [google_project_service.pubsub]
}

resource "google_pubsub_topic" "alert_events" {
  name = "alert-events"

  labels = {
    environment = var.environment
    service     = "privacy-platform"
  }

  depends_on = [google_project_service.pubsub]
}

resource "google_pubsub_topic" "report_events" {
  name = "report-events"

  labels = {
    environment = var.environment
    service     = "privacy-platform"
  }

  depends_on = [google_project_service.pubsub]
}

# --------------------------------------------------------------------------
# Pub/Sub subscriptions for scan triggers
# --------------------------------------------------------------------------

resource "google_pubsub_subscription" "scan_trigger_sub" {
  name  = "scan-trigger-subscription"
  topic = google_pubsub_topic.scan_events.id

  ack_deadline_seconds = 60

  push_config {
    push_endpoint = "https://${var.region}-${var.project_id}.cloudfunctions.net/scan-trigger"
    oidc_token {
      service_account_email = google_service_account.scan_runner.email
    }
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  depends_on = [google_project_service.cloudfunctions]
}

# --------------------------------------------------------------------------
# Service account for the scan runner Cloud Function
# --------------------------------------------------------------------------

resource "google_service_account" "scan_runner" {
  account_id   = "privacy-scan-runner"
  display_name = "Privacy Platform Scan Runner"
  description  = "Service account for Cloud Function that orchestrates file scanning"
}

# --------------------------------------------------------------------------
# IAM roles for the scan runner service account
# --------------------------------------------------------------------------

resource "google_storage_bucket_iam_member" "scan_runner_storage_viewer" {
  bucket = google_storage_bucket.uploads.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.scan_runner.email}"
}

resource "google_pubsub_topic_iam_member" "scan_runner_publisher" {
  topic  = google_pubsub_topic.scan_completed.id
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_service_account.scan_runner.email}"
}

resource "google_pubsub_topic_iam_member" "scan_runner_alert_publisher" {
  topic  = google_pubsub_topic.alert_events.id
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_service_account.scan_runner.email}"
}

# --------------------------------------------------------------------------
# IAM roles for the application backend service account
# --------------------------------------------------------------------------

resource "google_service_account" "app_backend" {
  account_id   = "privacy-app-backend"
  display_name = "Privacy Platform Backend Service"
  description  = "Service account for the backend API service"
}

resource "google_storage_bucket_iam_member" "app_backend_storage_admin" {
  bucket = google_storage_bucket.uploads.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.app_backend.email}"
}

resource "google_pubsub_topic_iam_member" "app_backend_scan_publisher" {
  topic  = google_pubsub_topic.scan_events.id
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_service_account.app_backend.email}"
}

resource "google_project_iam_member" "app_backend_dlp_user" {
  project = var.project_id
  role    = "roles/dlp.user"
  member  = "serviceAccount:${google_service_account.app_backend.email}"

  depends_on = [google_project_service.dlp]
}
