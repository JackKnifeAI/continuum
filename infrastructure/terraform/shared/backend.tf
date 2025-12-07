# Backend configuration for Terraform state
# This should be configured per environment

terraform {
  backend "s3" {
    # bucket         = "continuum-terraform-state-${var.environment}"
    # key            = "terraform.tfstate"
    # region         = "us-east-1"
    # encrypt        = true
    # dynamodb_table = "continuum-terraform-locks"
    #
    # Uncomment and configure the above when ready to use remote state
    # For initial setup, use local state with:
    # terraform init
  }
}

# DynamoDB table for state locking (create this manually first)
# resource "aws_dynamodb_table" "terraform_locks" {
#   name         = "continuum-terraform-locks"
#   billing_mode = "PAY_PER_REQUEST"
#   hash_key     = "LockID"
#
#   attribute {
#     name = "LockID"
#     type = "S"
#   }
#
#   tags = {
#     Name        = "Terraform State Locks"
#     Project     = "CONTINUUM"
#     ManagedBy   = "Terraform"
#   }
# }

# S3 bucket for state storage (create this manually first)
# resource "aws_s3_bucket" "terraform_state" {
#   bucket = "continuum-terraform-state-${var.environment}"
#
#   tags = {
#     Name        = "Terraform State Storage"
#     Project     = "CONTINUUM"
#     Environment = var.environment
#     ManagedBy   = "Terraform"
#   }
# }
#
# resource "aws_s3_bucket_versioning" "terraform_state" {
#   bucket = aws_s3_bucket.terraform_state.id
#
#   versioning_configuration {
#     status = "Enabled"
#   }
# }
#
# resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
#   bucket = aws_s3_bucket.terraform_state.id
#
#   rule {
#     apply_server_side_encryption_by_default {
#       sse_algorithm = "AES256"
#     }
#   }
# }
#
# resource "aws_s3_bucket_public_access_block" "terraform_state" {
#   bucket = aws_s3_bucket.terraform_state.id
#
#   block_public_acls       = true
#   block_public_policy     = true
#   ignore_public_acls      = true
#   restrict_public_buckets = true
# }
