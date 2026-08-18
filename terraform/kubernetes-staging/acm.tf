resource "aws_acm_certificate" "staging_api" {
  domain_name       = var.staging_api_hostname
  validation_method = "DNS"
  tags              = local.common_tags

  lifecycle {
    create_before_destroy = true
  }
}
