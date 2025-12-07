variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for ALB"
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for ECS tasks"
  type        = list(string)
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

# ECS Cluster
variable "enable_container_insights" {
  description = "Enable Container Insights for ECS cluster"
  type        = bool
  default     = true
}

# ECR Configuration
variable "create_ecr_repository" {
  description = "Create ECR repository"
  type        = bool
  default     = true
}

variable "ecr_scan_on_push" {
  description = "Enable image scanning on push"
  type        = bool
  default     = true
}

variable "ecr_image_tag_mutability" {
  description = "Image tag mutability (MUTABLE or IMMUTABLE)"
  type        = string
  default     = "MUTABLE"
}

variable "ecr_image_count_limit" {
  description = "Number of images to keep"
  type        = number
  default     = 10
}

variable "ecr_untagged_image_days" {
  description = "Days to keep untagged images"
  type        = number
  default     = 7
}

# ALB Configuration
variable "alb_internal" {
  description = "Make ALB internal"
  type        = bool
  default     = false
}

variable "alb_deletion_protection" {
  description = "Enable ALB deletion protection"
  type        = bool
  default     = true
}

variable "alb_allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access ALB"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "alb_access_logs_bucket" {
  description = "S3 bucket for ALB access logs"
  type        = string
  default     = ""
}

variable "alb_access_logs_prefix" {
  description = "Prefix for ALB access logs"
  type        = string
  default     = "alb"
}

variable "alb_ssl_policy" {
  description = "SSL policy for HTTPS listener"
  type        = string
  default     = "ELBSecurityPolicy-TLS13-1-2-2021-06"
}

variable "certificate_arn" {
  description = "ARN of SSL certificate for HTTPS"
  type        = string
  default     = ""
}

# Task Definition
variable "task_cpu" {
  description = "CPU units for task (256, 512, 1024, 2048, 4096)"
  type        = number
  default     = 512
}

variable "task_memory" {
  description = "Memory for task in MiB"
  type        = number
  default     = 1024
}

variable "container_name" {
  description = "Container name"
  type        = string
  default     = "app"
}

variable "container_image" {
  description = "Container image"
  type        = string
}

variable "container_port" {
  description = "Container port"
  type        = number
  default     = 8000
}

variable "cpu_architecture" {
  description = "CPU architecture (X86_64 or ARM64)"
  type        = string
  default     = "X86_64"
}

variable "fargate_platform_version" {
  description = "Fargate platform version"
  type        = string
  default     = "LATEST"
}

variable "readonly_root_filesystem" {
  description = "Make root filesystem read-only"
  type        = bool
  default     = false
}

# Environment Variables & Secrets
variable "environment_variables" {
  description = "Environment variables for container"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "secrets" {
  description = "Secrets from Secrets Manager or SSM for container"
  type = list(object({
    name      = string
    valueFrom = string
  }))
  default = []
}

variable "secret_arns" {
  description = "ARNs of secrets the task can access"
  type        = list(string)
  default     = []
}

# Container Health Check
variable "container_health_check_command" {
  description = "Container health check command"
  type        = list(string)
  default     = ["CMD-SHELL", "exit 0"]
}

variable "container_health_check_interval" {
  description = "Health check interval in seconds"
  type        = number
  default     = 30
}

variable "container_health_check_timeout" {
  description = "Health check timeout in seconds"
  type        = number
  default     = 5
}

variable "container_health_check_retries" {
  description = "Health check retries"
  type        = number
  default     = 3
}

variable "container_health_check_start_period" {
  description = "Health check start period in seconds"
  type        = number
  default     = 60
}

# Service Configuration
variable "desired_count" {
  description = "Desired number of tasks"
  type        = number
  default     = 1
}

variable "deployment_maximum_percent" {
  description = "Maximum deployment percent"
  type        = number
  default     = 200
}

variable "deployment_minimum_healthy_percent" {
  description = "Minimum healthy deployment percent"
  type        = number
  default     = 100
}

variable "enable_deployment_circuit_breaker" {
  description = "Enable deployment circuit breaker"
  type        = bool
  default     = true
}

variable "enable_deployment_rollback" {
  description = "Enable automatic rollback on deployment failure"
  type        = bool
  default     = true
}

variable "enable_execute_command" {
  description = "Enable ECS Exec for debugging"
  type        = bool
  default     = false
}

variable "health_check_grace_period" {
  description = "Health check grace period in seconds"
  type        = number
  default     = 60
}

# Target Group
variable "health_check_path" {
  description = "Health check path"
  type        = string
  default     = "/health"
}

variable "health_check_healthy_threshold" {
  description = "Healthy threshold"
  type        = number
  default     = 2
}

variable "health_check_unhealthy_threshold" {
  description = "Unhealthy threshold"
  type        = number
  default     = 3
}

variable "health_check_timeout" {
  description = "Health check timeout"
  type        = number
  default     = 5
}

variable "health_check_interval" {
  description = "Health check interval"
  type        = number
  default     = 30
}

variable "health_check_matcher" {
  description = "Health check response code matcher"
  type        = string
  default     = "200"
}

variable "deregistration_delay" {
  description = "Deregistration delay in seconds"
  type        = number
  default     = 30
}

variable "enable_sticky_sessions" {
  description = "Enable sticky sessions"
  type        = bool
  default     = false
}

variable "cookie_duration" {
  description = "Sticky session cookie duration in seconds"
  type        = number
  default     = 86400
}

# Auto Scaling
variable "enable_autoscaling" {
  description = "Enable auto scaling"
  type        = bool
  default     = true
}

variable "autoscaling_min_capacity" {
  description = "Minimum number of tasks"
  type        = number
  default     = 1
}

variable "autoscaling_max_capacity" {
  description = "Maximum number of tasks"
  type        = number
  default     = 10
}

variable "autoscaling_cpu_target" {
  description = "Target CPU utilization for auto scaling"
  type        = number
  default     = 70
}

variable "autoscaling_memory_target" {
  description = "Target memory utilization for auto scaling"
  type        = number
  default     = 80
}

variable "autoscaling_requests_target" {
  description = "Target request count per task (0 to disable)"
  type        = number
  default     = 0
}

variable "autoscaling_scale_in_cooldown" {
  description = "Scale in cooldown in seconds"
  type        = number
  default     = 300
}

variable "autoscaling_scale_out_cooldown" {
  description = "Scale out cooldown in seconds"
  type        = number
  default     = 60
}

# IAM
variable "task_role_policy_json" {
  description = "JSON policy for task role"
  type        = string
  default     = "{\"Version\":\"2012-10-17\",\"Statement\":[]}"
}

# Security
variable "enable_encryption" {
  description = "Enable encryption"
  type        = bool
  default     = true
}

variable "kms_deletion_window" {
  description = "KMS key deletion window in days"
  type        = number
  default     = 10
}

variable "enable_key_rotation" {
  description = "Enable KMS key rotation"
  type        = bool
  default     = true
}

# Logging
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

# Tags
variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
