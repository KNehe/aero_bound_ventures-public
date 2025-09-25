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

variable "repo_url" {
  description = "The URL of the repository to clone"
  type        = string
  default     = "https://github.com/KNehe/aero_bound_ventures.git"
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