variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where database will be created"
  type        = string
}

variable "database_subnet_ids" {
  description = "List of subnet IDs for database"
  type        = list(string)
}

variable "allowed_security_groups" {
  description = "Security groups allowed to access the database"
  type        = list(string)
  default     = []
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the database"
  type        = list(string)
  default     = []
}

# Instance Configuration
variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.micro"
}

variable "engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "16.1"
}

variable "major_engine_version" {
  description = "PostgreSQL major version for option group"
  type        = string
  default     = "16"
}

variable "parameter_group_family" {
  description = "Database parameter group family"
  type        = string
  default     = "postgres16"
}

# Storage Configuration
variable "allocated_storage" {
  description = "Initial allocated storage in GB"
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Maximum allocated storage for autoscaling in GB"
  type        = number
  default     = 100
}

variable "storage_type" {
  description = "Storage type (gp3, gp2, io1)"
  type        = string
  default     = "gp3"
}

variable "iops" {
  description = "Provisioned IOPS for io1 or gp3 storage"
  type        = number
  default     = 3000
}

# Database Configuration
variable "database_name" {
  description = "Name of the database to create"
  type        = string
  default     = "continuum"
}

variable "master_username" {
  description = "Master username for database"
  type        = string
  default     = "continuum_admin"
}

# Network Configuration
variable "publicly_accessible" {
  description = "Make database publicly accessible"
  type        = bool
  default     = false
}

variable "availability_zone" {
  description = "Availability zone for single-AZ deployment"
  type        = string
  default     = null
}

# High Availability
variable "multi_az" {
  description = "Enable Multi-AZ deployment"
  type        = bool
  default     = false
}

# Backup Configuration
variable "backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

variable "backup_window" {
  description = "Preferred backup window"
  type        = string
  default     = "03:00-04:00"
}

variable "maintenance_window" {
  description = "Preferred maintenance window"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

variable "skip_final_snapshot" {
  description = "Skip final snapshot on deletion"
  type        = bool
  default     = false
}

variable "delete_automated_backups" {
  description = "Delete automated backups when instance is deleted"
  type        = bool
  default     = true
}

# Monitoring Configuration
variable "enabled_cloudwatch_logs_exports" {
  description = "List of log types to export to CloudWatch"
  type        = list(string)
  default     = ["postgresql", "upgrade"]
}

variable "monitoring_interval" {
  description = "Enhanced monitoring interval in seconds (0, 1, 5, 10, 15, 30, 60)"
  type        = number
  default     = 60

  validation {
    condition     = contains([0, 1, 5, 10, 15, 30, 60], var.monitoring_interval)
    error_message = "Valid values for monitoring_interval are 0, 1, 5, 10, 15, 30, or 60."
  }
}

variable "performance_insights_enabled" {
  description = "Enable Performance Insights"
  type        = bool
  default     = false
}

variable "performance_insights_retention" {
  description = "Performance Insights retention period in days"
  type        = number
  default     = 7
}

# Security Configuration
variable "enable_encryption" {
  description = "Enable encryption at rest"
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

variable "deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = true
}

variable "secret_recovery_window" {
  description = "Secret recovery window in days"
  type        = number
  default     = 7
}

# Update Configuration
variable "auto_minor_version_upgrade" {
  description = "Enable auto minor version upgrades"
  type        = bool
  default     = true
}

variable "apply_immediately" {
  description = "Apply changes immediately or during maintenance window"
  type        = bool
  default     = false
}

# Parameter Group Settings
variable "shared_buffers" {
  description = "PostgreSQL shared_buffers parameter"
  type        = string
  default     = "{DBInstanceClassMemory/4096}"
}

variable "effective_cache_size" {
  description = "PostgreSQL effective_cache_size parameter"
  type        = string
  default     = "{DBInstanceClassMemory*3/4096}"
}

variable "maintenance_work_mem" {
  description = "PostgreSQL maintenance_work_mem parameter in KB"
  type        = string
  default     = "524288"
}

variable "work_mem" {
  description = "PostgreSQL work_mem parameter in KB"
  type        = string
  default     = "16384"
}

variable "max_connections" {
  description = "Maximum number of database connections"
  type        = string
  default     = "100"
}

variable "log_statement" {
  description = "PostgreSQL log_statement setting (none, ddl, mod, all)"
  type        = string
  default     = "none"
}

variable "log_min_duration_statement" {
  description = "Log queries taking longer than this many milliseconds"
  type        = string
  default     = "1000"
}

# Read Replica Configuration
variable "read_replica_count" {
  description = "Number of read replicas to create"
  type        = number
  default     = 0
}

variable "read_replica_instance_class" {
  description = "Instance class for read replicas (uses main instance class if not specified)"
  type        = string
  default     = ""
}

# CloudWatch Alarms
variable "create_cloudwatch_alarms" {
  description = "Create CloudWatch alarms for database metrics"
  type        = bool
  default     = true
}

variable "alarm_actions" {
  description = "List of ARNs to notify when alarms trigger"
  type        = list(string)
  default     = []
}

variable "cpu_alarm_threshold" {
  description = "CPU utilization threshold for alarm (percentage)"
  type        = number
  default     = 80
}

variable "storage_alarm_threshold" {
  description = "Free storage space threshold for alarm (bytes)"
  type        = number
  default     = 5368709120  # 5 GB in bytes
}

variable "memory_alarm_threshold" {
  description = "Freeable memory threshold for alarm (bytes)"
  type        = number
  default     = 268435456  # 256 MB in bytes
}

variable "connection_alarm_threshold" {
  description = "Database connections threshold for alarm"
  type        = number
  default     = 80
}

# Tags
variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
