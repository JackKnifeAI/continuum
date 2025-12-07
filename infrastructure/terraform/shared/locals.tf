locals {
  # Common tags for all resources
  common_tags = {
    Project     = "CONTINUUM"
    ManagedBy   = "Terraform"
    Repository  = "https://github.com/yourusername/continuum"
    Environment = var.environment
  }

  # Naming convention
  name_prefix = "continuum-${var.environment}"

  # Regional configuration
  primary_region   = var.aws_region
  secondary_region = var.secondary_region

  # Environment-specific configurations
  is_production = var.environment == "production"
  is_staging    = var.environment == "staging"
  is_dev        = var.environment == "dev"

  # Multi-AZ settings
  enable_multi_az = local.is_production || local.is_staging

  # Backup retention
  backup_retention_days = local.is_production ? 30 : (local.is_staging ? 14 : 7)

  # Log retention
  log_retention_days = local.is_production ? 30 : (local.is_staging ? 14 : 7)

  # Alert configurations
  enable_enhanced_monitoring = local.is_production || local.is_staging
  enable_performance_insights = local.is_production

  # Cost optimization
  enable_deletion_protection = local.is_production
  enable_backup = true

  # Network configuration
  vpc_cidr = var.vpc_cidr
  azs      = slice(data.aws_availability_zones.available.names, 0, local.enable_multi_az ? 3 : 1)

  # Subnet CIDRs (calculated from VPC CIDR)
  public_subnet_cidrs = [
    for i in range(length(local.azs)) :
    cidrsubnet(local.vpc_cidr, 4, i)
  ]

  private_subnet_cidrs = [
    for i in range(length(local.azs)) :
    cidrsubnet(local.vpc_cidr, 4, i + length(local.azs))
  ]

  database_subnet_cidrs = [
    for i in range(length(local.azs)) :
    cidrsubnet(local.vpc_cidr, 4, i + (2 * length(local.azs)))
  ]

  # Database configuration
  db_instance_class = var.db_instance_class != "" ? var.db_instance_class : (
    local.is_production ? "db.r6g.large" :
    local.is_staging ? "db.t4g.medium" :
    "db.t4g.micro"
  )

  db_allocated_storage = local.is_production ? 100 : (local.is_staging ? 50 : 20)
  db_max_allocated_storage = local.is_production ? 1000 : (local.is_staging ? 200 : 100)

  # Cache configuration
  cache_node_type = var.cache_node_type != "" ? var.cache_node_type : (
    local.is_production ? "cache.r6g.large" :
    local.is_staging ? "cache.t4g.medium" :
    "cache.t4g.micro"
  )

  cache_num_nodes = local.is_production ? 3 : (local.is_staging ? 2 : 1)

  # ECS configuration
  ecs_task_cpu = local.is_production ? 2048 : (local.is_staging ? 1024 : 512)
  ecs_task_memory = local.is_production ? 4096 : (local.is_staging ? 2048 : 1024)
  ecs_desired_count = local.is_production ? 3 : (local.is_staging ? 2 : 1)
  ecs_max_capacity = local.is_production ? 10 : (local.is_staging ? 5 : 2)

  # CloudFront configuration
  enable_waf = local.is_production || local.is_staging
  enable_geo_restriction = false

  # Monitoring configuration
  alarm_email = var.alarm_email
  enable_detailed_monitoring = local.is_production

  # Security
  enable_encryption = true
  kms_key_rotation = local.is_production
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}
