output "replication_group_id" {
  description = "ElastiCache replication group ID"
  value       = aws_elasticache_replication_group.main.id
}

output "replication_group_arn" {
  description = "ElastiCache replication group ARN"
  value       = aws_elasticache_replication_group.main.arn
}

output "primary_endpoint_address" {
  description = "Primary endpoint address"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "reader_endpoint_address" {
  description = "Reader endpoint address"
  value       = aws_elasticache_replication_group.main.reader_endpoint_address
}

output "configuration_endpoint_address" {
  description = "Configuration endpoint address (for cluster mode)"
  value       = aws_elasticache_replication_group.main.configuration_endpoint_address
}

output "port" {
  description = "Redis port"
  value       = 6379
}

output "security_group_id" {
  description = "Security group ID for cache"
  value       = aws_security_group.cache.id
}

output "subnet_group_name" {
  description = "Cache subnet group name"
  value       = aws_elasticache_subnet_group.main.name
}

output "parameter_group_name" {
  description = "Cache parameter group name"
  value       = aws_elasticache_parameter_group.main.name
}

output "kms_key_id" {
  description = "KMS key ID for cache encryption"
  value       = var.enable_encryption ? aws_kms_key.cache[0].id : null
}

output "kms_key_arn" {
  description = "KMS key ARN for cache encryption"
  value       = var.enable_encryption ? aws_kms_key.cache[0].arn : null
}

output "member_clusters" {
  description = "List of member cluster IDs"
  value       = aws_elasticache_replication_group.main.member_clusters
}
