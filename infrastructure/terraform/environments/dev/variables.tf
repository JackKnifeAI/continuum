variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "container_image" {
  description = "Container image URL"
  type        = string
  default     = "nginx:latest"  # Replace with your actual image
}

variable "certificate_arn" {
  description = "ARN of SSL certificate for HTTPS (optional for dev)"
  type        = string
  default     = ""
}

variable "alarm_email" {
  description = "Email address for alarm notifications"
  type        = string
  default     = ""
}

variable "domain_name" {
  description = "Domain name for DNS (optional)"
  type        = string
  default     = ""
}

variable "hosted_zone_id" {
  description = "Route53 hosted zone ID (if using existing zone)"
  type        = string
  default     = ""
}
