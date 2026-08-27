output "eks_cluster_name" {
  description = "Name of the staging EKS Auto Mode cluster."
  value       = aws_eks_cluster.staging.name
}

output "ecr_repository_url" {
  description = "ECR repository used for backend images."
  value       = aws_ecr_repository.backend.repository_url
}

output "redis_primary_endpoint" {
  description = "TLS-enabled Redis endpoint used by staging workloads."
  value       = aws_elasticache_replication_group.staging.primary_endpoint_address
}

output "github_actions_deploy_role_arn" {
  description = "Role assumed by the staging deployment workflow."
  value       = aws_iam_role.github_actions_deploy.arn
}

output "staging_api_hostname" {
  description = "Public hostname reserved for the staging API."
  value       = var.staging_api_hostname
}

output "staging_grafana_hostname" {
  description = "Public hostname reserved for the staging Grafana dashboard."
  value       = var.staging_grafana_hostname
}

output "staging_https_certificate_arn" {
  description = "ACM certificate ARN shared by the staging API and Grafana."
  value       = aws_acm_certificate.staging_services.arn
}

output "staging_https_certificate_status" {
  description = "Current validation status of the shared staging certificate."
  value       = aws_acm_certificate.staging_services.status
}

output "staging_certificate_validation_records" {
  description = "DNS records required to validate every staging certificate hostname."
  value = {
    for option in aws_acm_certificate.staging_services.domain_validation_options :
    option.domain_name => {
      name  = option.resource_record_name
      type  = option.resource_record_type
      value = option.resource_record_value
    }
  }
}

output "staging_alb_ingress_class_http_manifest" {
  description = "EKS Auto Mode ALB class configuration used before HTTPS activation."
  value       = local.staging_alb_ingress_class_http_manifest
}

output "staging_alb_ingress_class_https_manifest" {
  description = "EKS Auto Mode ALB class configuration used after HTTPS activation."
  value       = local.staging_alb_ingress_class_https_manifest
}
