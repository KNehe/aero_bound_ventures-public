resource "aws_security_group" "redis" {
  name        = "${local.name}-redis"
  description = "Allow Redis traffic from the EKS cluster"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "Redis from EKS"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_eks_cluster.staging.vpc_config[0].cluster_security_group_id]
  }


  tags = local.common_tags
}

resource "aws_elasticache_subnet_group" "staging" {
  name       = "${local.name}-redis"
  subnet_ids = data.aws_subnets.default.ids
}

resource "aws_elasticache_replication_group" "staging" {
  replication_group_id = "${local.name}-redis"
  description          = "Redis for the staging backend"

  engine                     = "redis"
  engine_version             = "7.1"
  node_type                  = "cache.t4g.micro"
  port                       = 6379
  num_cache_clusters         = 1
  subnet_group_name          = aws_elasticache_subnet_group.staging.name
  security_group_ids         = [aws_security_group.redis.id]
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  automatic_failover_enabled = false
  multi_az_enabled           = false
  apply_immediately          = true
  snapshot_retention_limit   = 1

  tags = local.common_tags
}
