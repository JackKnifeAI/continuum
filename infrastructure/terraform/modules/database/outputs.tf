output "db_instance_id" {
  description = "RDS instance ID"
  value       = aws_db_instance.main.id
}

output "db_instance_arn" {
  description = "RDS instance ARN"
  value       = aws_db_instance.main.arn
}

output "db_instance_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
}

output "db_instance_address" {
  description = "RDS instance address"
  value       = aws_db_instance.main.address
}

output "db_instance_port" {
  description = "RDS instance port"
  value       = aws_db_instance.main.port
}

output "db_instance_name" {
  description = "RDS database name"
  value       = aws_db_instance.main.db_name
}

output "db_master_username" {
  description = "RDS master username"
  value       = aws_db_instance.main.username
  sensitive   = true
}

output "db_security_group_id" {
  description = "Security group ID for database"
  value       = aws_security_group.database.id
}

output "db_subnet_group_name" {
  description = "DB subnet group name"
  value       = aws_db_subnet_group.main.name
}

output "db_parameter_group_name" {
  description = "DB parameter group name"
  value       = aws_db_parameter_group.main.name
}

output "db_password_secret_arn" {
  description = "ARN of the Secrets Manager secret containing database password"
  value       = aws_secretsmanager_secret.database_password.arn
}

output "db_password_secret_name" {
  description = "Name of the Secrets Manager secret containing database password"
  value       = aws_secretsmanager_secret.database_password.name
}

output "kms_key_id" {
  description = "KMS key ID for database encryption"
  value       = var.enable_encryption ? aws_kms_key.database[0].id : null
}

output "kms_key_arn" {
  description = "KMS key ARN for database encryption"
  value       = var.enable_encryption ? aws_kms_key.database[0].arn : null
}

output "read_replica_endpoints" {
  description = "Endpoints of read replicas"
  value       = aws_db_instance.read_replica[*].endpoint
}

output "read_replica_ids" {
  description = "IDs of read replicas"
  value       = aws_db_instance.read_replica[*].id
}

output "connection_string" {
  description = "Database connection string (without password)"
  value       = "postgresql://${aws_db_instance.main.username}@${aws_db_instance.main.address}:${aws_db_instance.main.port}/${aws_db_instance.main.db_name}"
  sensitive   = true
}
