data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

resource "aws_ec2_tag" "public_load_balancer_subnets" {
  for_each = toset(data.aws_subnets.default.ids)

  resource_id = each.value
  key         = "kubernetes.io/role/elb"
  value       = "1"

  depends_on = [aws_eks_cluster.staging]
}

locals {
  name = "${var.project_name}-${var.environment}"

  staging_alb_ingress_class_http_manifest = templatefile(
    "${path.module}/alb-ingress-class.yaml.tftpl",
    { certificate_arn = "" }
  )

  staging_alb_ingress_class_https_manifest = templatefile(
    "${path.module}/alb-ingress-class.yaml.tftpl",
    { certificate_arn = aws_acm_certificate.staging_services.arn }
  )

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
