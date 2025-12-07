terraform {
  required_version = ">= 1.6.0"

  backend "s3" {
    # Configure backend with:
    # terraform init -backend-config="bucket=continuum-terraform-state-dev"
    # bucket         = "continuum-terraform-state-dev"
    # key            = "dev/terraform.tfstate"
    # region         = "us-east-1"
    # encrypt        = true
    # dynamodb_table = "continuum-terraform-locks"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

locals {
  environment = "dev"
  common_tags = {
    Project     = "CONTINUUM"
    Environment = local.environment
    ManagedBy   = "Terraform"
    Repository  = "https://github.com/yourusername/continuum"
  }
  name_prefix = "continuum-${local.environment}"
}

# Networking
module "networking" {
  source = "../../modules/networking"

  name_prefix            = local.name_prefix
  vpc_cidr               = var.vpc_cidr
  availability_zones     = slice(data.aws_availability_zones.available.names, 0, 1)
  public_subnet_cidrs    = [cidrsubnet(var.vpc_cidr, 4, 0)]
  private_subnet_cidrs   = [cidrsubnet(var.vpc_cidr, 4, 1)]
  database_subnet_cidrs  = [cidrsubnet(var.vpc_cidr, 4, 2)]
  enable_nat_gateway     = true
  single_nat_gateway     = true
  enable_flow_logs       = false
  enable_vpc_endpoints   = false
  aws_region             = var.aws_region
  tags                   = local.common_tags
}

# Database
module "database" {
  source = "../../modules/database"

  name_prefix               = local.name_prefix
  vpc_id                    = module.networking.vpc_id
  database_subnet_ids       = module.networking.database_subnet_ids
  allowed_security_groups   = [module.compute.ecs_tasks_security_group_id]
  instance_class            = "db.t4g.micro"
  allocated_storage         = 20
  max_allocated_storage     = 50
  multi_az                  = false
  backup_retention_period   = 3
  skip_final_snapshot       = true
  deletion_protection       = false
  performance_insights_enabled = false
  monitoring_interval       = 0
  tags                      = local.common_tags
}

# Cache
module "cache" {
  source = "../../modules/cache"

  name_prefix                = local.name_prefix
  vpc_id                     = module.networking.vpc_id
  database_subnet_ids        = module.networking.database_subnet_ids
  allowed_security_groups    = [module.compute.ecs_tasks_security_group_id]
  node_type                  = "cache.t4g.micro"
  num_cache_nodes            = 1
  automatic_failover_enabled = false
  multi_az_enabled           = false
  snapshot_retention_limit   = 3
  skip_final_snapshot        = true
  tags                       = local.common_tags
}

# Compute
module "compute" {
  source = "../../modules/compute"

  name_prefix         = local.name_prefix
  vpc_id              = module.networking.vpc_id
  public_subnet_ids   = module.networking.public_subnet_ids
  private_subnet_ids  = module.networking.private_subnet_ids
  aws_region          = var.aws_region

  # Task configuration
  task_cpu            = 512
  task_memory         = 1024
  container_image     = var.container_image
  container_port      = 8000
  desired_count       = 1

  # Auto-scaling
  enable_autoscaling         = true
  autoscaling_min_capacity   = 1
  autoscaling_max_capacity   = 3
  autoscaling_cpu_target     = 70
  autoscaling_memory_target  = 80

  # ALB
  alb_deletion_protection = false
  certificate_arn         = var.certificate_arn

  # Environment variables
  environment_variables = [
    { name = "ENVIRONMENT", value = "dev" },
    { name = "DATABASE_HOST", value = module.database.db_instance_address },
    { name = "REDIS_HOST", value = module.cache.primary_endpoint_address }
  ]

  # Secrets
  secrets = [
    { name = "DATABASE_PASSWORD", valueFrom = module.database.db_password_secret_arn }
  ]
  secret_arns = [module.database.db_password_secret_arn]

  tags = local.common_tags
}

# Monitoring
module "monitoring" {
  source = "../../modules/monitoring"

  name_prefix            = local.name_prefix
  aws_region             = var.aws_region
  alarm_email            = var.alarm_email
  ecs_cluster_name       = module.compute.ecs_cluster_name
  alb_arn                = module.compute.alb_arn
  db_instance_id         = module.database.db_instance_id
  elasticache_cluster_id = module.cache.replication_group_id
  error_log_group_name   = module.compute.cloudwatch_log_group_name
  tags                   = local.common_tags
}

# DNS (optional)
module "dns" {
  source = "../../modules/dns"
  count  = var.domain_name != "" ? 1 : 0

  name_prefix       = local.name_prefix
  domain_name       = var.domain_name
  subdomain         = "dev"
  hosted_zone_id    = var.hosted_zone_id
  alb_dns_name      = module.compute.alb_dns_name
  alb_zone_id       = module.compute.alb_zone_id
  alarm_actions     = [module.monitoring.sns_topic_arn]
  tags              = local.common_tags
}

data "aws_availability_zones" "available" {
  state = "available"
}
