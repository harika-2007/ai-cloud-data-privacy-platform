################################################################################
# Terraform output values for the Privacy Platform GCP infrastructure.
################################################################################

output "project_id" {
  description = "The GCP project ID where resources are deployed"
  value       = var.project_id
}

output "bucket_name" {
  description = "The name of the GCS bucket for file uploads"
  value       = google_storage_bucket.uploads.name
}

output "bucket_url" {
  description = "The gs:// URL for the uploads bucket"
  value       = "gs://${google_storage_bucket.uploads.name}"
}

output "bucket_self_link" {
  description = "The self-link URI for the uploads bucket"
  value       = google_storage_bucket.uploads.self_link
}

output "pubsub_topics" {
  description = "Map of Pub/Sub topic names to their IDs"
  value = {
    scan_events   = google_pubsub_topic.scan_events.id
    scan_completed = google_pubsub_topic.scan_completed.id
    alert_events  = google_pubsub_topic.alert_events.id
    report_events = google_pubsub_topic.report_events.id
  }
}

output "scan_runner_service_account" {
  description = "Email of the scan runner Cloud Function service account"
  value       = google_service_account.scan_runner.email
}

output "app_backend_service_account" {
  description = "Email of the application backend service account"
  value       = google_service_account.app_backend.email
}

output "region" {
  description = "The GCP region where resources are deployed"
  value       = var.region
}

output "environment" {
  description = "The deployment environment"
  value       = var.environment
}
