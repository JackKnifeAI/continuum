# KMS Key for Secrets
resource "aws_kms_key" "secrets" {
  count                   = var.enable_encryption ? 1 : 0
  description             = "KMS key for ${var.name_prefix} secrets"
  deletion_window_in_days = var.kms_deletion_window
  enable_key_rotation     = var.enable_key_rotation
  tags                    = var.tags
}

resource "aws_kms_alias" "secrets" {
  count         = var.enable_encryption ? 1 : 0
  name          = "alias/${var.name_prefix}-secrets"
  target_key_id = aws_kms_key.secrets[0].key_id
}

# Application Secrets
resource "aws_secretsmanager_secret" "app_secrets" {
  for_each                = var.secrets
  name                    = "${var.name_prefix}-${each.key}"
  description             = each.value.description
  kms_key_id              = var.enable_encryption ? aws_kms_key.secrets[0].id : null
  recovery_window_in_days = var.recovery_window_days
  tags                    = var.tags
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  for_each      = var.secrets
  secret_id     = aws_secretsmanager_secret.app_secrets[each.key].id
  secret_string = jsonencode(each.value.value)
}

# IAM Policy for secret access
resource "aws_iam_policy" "secrets_access" {
  count       = var.create_access_policy ? 1 : 0
  name        = "${var.name_prefix}-secrets-access"
  description = "Policy to access ${var.name_prefix} secrets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [for s in aws_secretsmanager_secret.app_secrets : s.arn]
      },
      var.enable_encryption ? {
        Effect = "Allow"
        Action = ["kms:Decrypt"]
        Resource = [aws_kms_key.secrets[0].arn]
      } : null
    ]
  })
}
