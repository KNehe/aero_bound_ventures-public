resource "aws_acm_certificate" "staging_api" {
  domain_name       = var.staging_api_hostname
  validation_method = "DNS"
  tags              = local.common_tags

  lifecycle {
    create_before_destroy = true
  }
}

# Keep the active API-only certificate until this combined replacement is
# validated and attached to the shared staging ALB.
resource "aws_acm_certificate" "staging_services" {
  domain_name               = var.staging_api_hostname
  subject_alternative_names = [var.staging_grafana_hostname]
  validation_method         = "DNS"
  tags                      = local.common_tags

  lifecycle {
    create_before_destroy = true
  }
}
