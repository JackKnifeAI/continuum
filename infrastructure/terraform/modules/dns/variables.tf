variable "name_prefix" { type = string }
variable "domain_name" { type = string }
variable "subdomain" { type = string; default = "" }
variable "create_hosted_zone" { type = bool; default = false }
variable "hosted_zone_id" { type = string; default = "" }
variable "alb_dns_name" { type = string; default = "" }
variable "alb_zone_id" { type = string; default = "" }
variable "enable_ipv6" { type = bool; default = true }
variable "evaluate_target_health" { type = bool; default = true }
variable "create_health_check" { type = bool; default = false }
variable "health_check_path" { type = string; default = "/health" }
variable "health_check_failure_threshold" { type = number; default = 3 }
variable "health_check_interval" { type = number; default = 30 }
variable "alarm_actions" { type = list(string); default = [] }
variable "tags" { type = map(string); default = {} }
