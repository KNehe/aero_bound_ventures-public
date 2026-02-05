variable "instance_name" {
  description = "Value of the EC2 instance's Name tag."
  type        = string
  default     = "aero-bound_ventures"
}

variable "instance_type" {
  description = "The EC2 instance's type."
  type        = string
  default     = "t3.micro"
}

variable "key_pair_name" {
  description = "Name of the AWS key pair for SSH access"
  type        = string
  default     = ""
}

variable "repo_url" {
  description = "The repository path (org/repo format, e.g., KNehe/aero_bound_ventures)"
  type        = string
  default     = "KNehe/aero_bound_ventures"
}

variable "gh_pat" {
  description = "GitHub Personal Access Token"
  type        = string
  sensitive   = true
}

variable "mail_username" {
  type      = string
  sensitive = true
}

variable "mail_password" {
  type      = string
  sensitive = true
}

variable "mail_from" {
  type      = string
  sensitive = true
}

variable "mail_port" {
  type      = string
  sensitive = true
}

variable "mail_server" {
  type      = string
  sensitive = true
}

variable "access_token_expire_minutes" {
  type      = string
  sensitive = true
}

variable "secret_key" {
  type      = string
  sensitive = true
}

variable "algorithm" {
  type      = string
  sensitive = true
}

variable "amadeus_api_key" {
  type      = string
  sensitive = true
}

variable "amadeus_api_secret" {
  type      = string
  sensitive = true
}

variable "amadeus_base_url" {
  type      = string
  sensitive = true
}

variable "database_url" {
  type      = string
  sensitive = true
}

# Pesapal Payment Gateway
variable "pesapal_consumer_key" {
  type      = string
  sensitive = true
}

variable "pesapal_consumer_secret" {
  type      = string
  sensitive = true
}

variable "pesapal_base_url" {
  type      = string
  default   = "https://pay.pesapal.com/v3"
}

variable "pesapal_ipn_id" {
  type      = string
  sensitive = true
}

# Cloudinary
variable "cloudinary_url" {
  type      = string
  sensitive = true
}

# Redis
variable "redis_url" {
  type    = string
  default = "redis://redis:6379"
}

# Google OAuth
variable "google_client_id" {
  type      = string
  sensitive = true
  default   = ""
}

variable "google_client_secret" {
  type      = string
  sensitive = true
  default   = ""
}

variable "google_redirect_uri" {
  type    = string
  default = ""
}

# CORS and Frontend
variable "cors_origins" {
  type    = string
  default = "http://localhost:3000"
}

variable "frontend_url" {
  type    = string
  default = "http://localhost:3000"
}

# Environment
variable "environment" {
  type    = string
  default = "production"
}