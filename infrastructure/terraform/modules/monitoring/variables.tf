variable "name_prefix" { type = string }
variable "aws_region" { type = string }
variable "alarm_email" { type = string; default = "" }
variable "enable_encryption" { type = bool; default = true }
variable "ecs_cluster_name" { type = string; default = "" }
variable "alb_arn" { type = string; default = "" }
variable "db_instance_id" { type = string; default = "" }
variable "elasticache_cluster_id" { type = string; default = "" }
variable "create_composite_alarms" { type = bool; default = false }
variable "error_log_group_name" { type = string; default = "" }
variable "error_threshold" { type = number; default = 10 }
variable "tags" { type = map(string); default = {} }
