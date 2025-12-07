variable "name_prefix" { type = string }
variable "enable_encryption" { type = bool; default = true }
variable "kms_deletion_window" { type = number; default = 10 }
variable "enable_key_rotation" { type = bool; default = true }
variable "recovery_window_days" { type = number; default = 7 }
variable "create_access_policy" { type = bool; default = true }
variable "secrets" {
  description = "Map of secrets to create"
  type = map(object({
    description = string
    value       = map(string)
  }))
  default = {}
}
variable "tags" { type = map(string); default = {} }
