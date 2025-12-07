variable "aws_region" { type = string; default = "us-east-1" }
variable "vpc_cidr" { type = string; default = "10.1.0.0/16" }
variable "container_image" { type = string }
variable "certificate_arn" { type = string }
variable "alarm_email" { type = string }
variable "domain_name" { type = string; default = "" }
variable "hosted_zone_id" { type = string; default = "" }
