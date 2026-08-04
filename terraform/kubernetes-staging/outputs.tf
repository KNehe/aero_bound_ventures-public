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
