output "secret_arns" { value = { for k, v in aws_secretsmanager_secret.app_secrets : k => v.arn } }
output "kms_key_id" { value = var.enable_encryption ? aws_kms_key.secrets[0].id : null }
output "kms_key_arn" { value = var.enable_encryption ? aws_kms_key.secrets[0].arn : null }
output "access_policy_arn" { value = var.create_access_policy ? aws_iam_policy.secrets_access[0].arn : null }
