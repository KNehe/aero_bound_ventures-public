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

output "staging_api_certificate_arn" {
  description = "ACM certificate ARN for the staging API hostname."
  value       = aws_acm_certificate.staging_api.arn
}

output "staging_api_certificate_status" {
  description = "Current ACM validation status for the staging API certificate."
  value       = aws_acm_certificate.staging_api.status
}

output "staging_api_certificate_validation_record_name" {
  description = "CNAME name required by the DNS provider for ACM validation."
  value       = one(aws_acm_certificate.staging_api.domain_validation_options).resource_record_name
}

output "staging_api_certificate_validation_record_type" {
  description = "Record type required by the DNS provider for ACM validation."
  value       = one(aws_acm_certificate.staging_api.domain_validation_options).resource_record_type
}

output "staging_api_certificate_validation_record_value" {
  description = "CNAME value required by the DNS provider for ACM validation."
  value       = one(aws_acm_certificate.staging_api.domain_validation_options).resource_record_value
}

output "staging_alb_ingress_class_http_manifest" {
  description = "EKS Auto Mode ALB class configuration used before HTTPS activation."
  value       = local.staging_alb_ingress_class_http_manifest
}

output "staging_alb_ingress_class_https_manifest" {
  description = "EKS Auto Mode ALB class configuration used after HTTPS activation."
  value       = local.staging_alb_ingress_class_https_manifest
}
