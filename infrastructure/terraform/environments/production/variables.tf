variable "aws_region" { type = string; default = "us-east-1" }
variable "vpc_cidr" { type = string; default = "10.2.0.0/16" }
variable "container_image" { type = string }
variable "certificate_arn" { type = string }
variable "alarm_email" { type = string }
variable "domain_name" { type = string }
variable "subdomain" { type = string; default = "" }
variable "hosted_zone_id" { type = string }
variable "cdn_domain_aliases" { type = list(string); default = [] }
variable "cdn_certificate_arn" { type = string }
variable "cdn_logging_bucket" { type = string; default = "" }
variable "waf_web_acl_arn" { type = string; default = "" }
