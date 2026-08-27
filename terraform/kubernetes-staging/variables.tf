variable "aws_region" {
  description = "AWS region for the staging Kubernetes platform."
  type        = string
  default     = "us-east-2"
}

variable "project_name" {
  description = "Short name used for backend infrastructure."
  type        = string
  default     = "aero-backend"
}

variable "environment" {
  description = "Environment represented by this Terraform root."
  type        = string
  default     = "staging"
}

variable "github_repository" {
  description = "GitHub repository allowed to deploy the backend."
  type        = string
  default     = "KNehe/aero_bound_ventures"
}

variable "kubernetes_namespace" {
  description = "Kubernetes namespace GitHub Actions may deploy into."
  type        = string
  default     = "aero-staging"
}

variable "staging_api_hostname" {
  description = "Public hostname for the staging API."
  type        = string
  default     = "api-staging.aeroboundventures.com"
}

variable "staging_grafana_hostname" {
  description = "Public hostname for the staging Grafana dashboard."
  type        = string
  default     = "grafana-staging.aeroboundventures.com"
}
