variable "name_prefix" { type = string }
variable "origin_domain_name" { type = string }
variable "origin_id" { type = string; default = "primary" }
variable "create_oac" { type = bool; default = false }
variable "enable_ipv6" { type = bool; default = true }
variable "default_root_object" { type = string; default = "index.html" }
variable "price_class" { type = string; default = "PriceClass_100" }
variable "domain_aliases" { type = list(string); default = [] }
variable "web_acl_arn" { type = string; default = "" }
variable "origin_protocol_policy" { type = string; default = "https-only" }
variable "origin_ssl_protocols" { type = list(string); default = ["TLSv1.2"] }
variable "custom_header_value" { type = string; default = "" }
variable "allowed_methods" { type = list(string); default = ["GET", "HEAD", "OPTIONS"] }
variable "cached_methods" { type = list(string); default = ["GET", "HEAD"] }
variable "forward_query_string" { type = bool; default = true }
variable "forward_headers" { type = list(string); default = ["Host"] }
variable "forward_cookies" { type = string; default = "none" }
variable "viewer_protocol_policy" { type = string; default = "redirect-to-https" }
variable "min_ttl" { type = number; default = 0 }
variable "default_ttl" { type = number; default = 3600 }
variable "max_ttl" { type = number; default = 86400 }
variable "enable_compression" { type = bool; default = true }
variable "response_headers_policy_id" { type = string; default = "" }
variable "geo_restriction_type" { type = string; default = "none" }
variable "geo_restriction_locations" { type = list(string); default = [] }
variable "acm_certificate_arn" { type = string; default = "" }
variable "minimum_protocol_version" { type = string; default = "TLSv1.2_2021" }
variable "logging_bucket" { type = string; default = "" }
variable "logging_prefix" { type = string; default = "cdn/" }
variable "tags" { type = map(string); default = {} }
