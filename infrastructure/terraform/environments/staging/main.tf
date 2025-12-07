terraform {
  required_version = ">= 1.6.0"
  backend "s3" {}
  required_providers {
    aws = { source = "hashicorp/aws"; version = "~> 5.0" }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags { tags = local.common_tags }
}

locals {
  environment = "staging"
  common_tags = { Project = "CONTINUUM"; Environment = local.environment; ManagedBy = "Terraform" }
  name_prefix = "continuum-${local.environment}"
}

module "networking" {
  source                 = "../../modules/networking"
  name_prefix            = local.name_prefix
  vpc_cidr               = var.vpc_cidr
  availability_zones     = slice(data.aws_availability_zones.available.names, 0, 2)
  public_subnet_cidrs    = [cidrsubnet(var.vpc_cidr, 4, 0), cidrsubnet(var.vpc_cidr, 4, 1)]
  private_subnet_cidrs   = [cidrsubnet(var.vpc_cidr, 4, 2), cidrsubnet(var.vpc_cidr, 4, 3)]
  database_subnet_cidrs  = [cidrsubnet(var.vpc_cidr, 4, 4), cidrsubnet(var.vpc_cidr, 4, 5)]
  enable_nat_gateway     = true
  single_nat_gateway     = false
  enable_flow_logs       = true
  enable_vpc_endpoints   = true
  aws_region             = var.aws_region
  tags                   = local.common_tags
}

module "database" {
  source                       = "../../modules/database"
  name_prefix                  = local.name_prefix
  vpc_id                       = module.networking.vpc_id
  database_subnet_ids          = module.networking.database_subnet_ids
  allowed_security_groups      = [module.compute.ecs_tasks_security_group_id]
  instance_class               = "db.t4g.medium"
  allocated_storage            = 50
  max_allocated_storage        = 200
  multi_az                     = true
  backup_retention_period      = 14
  skip_final_snapshot          = false
  deletion_protection          = true
  performance_insights_enabled = true
  monitoring_interval          = 60
  read_replica_count           = 1
  tags                         = local.common_tags
}

module "cache" {
  source                     = "../../modules/cache"
  name_prefix                = local.name_prefix
  vpc_id                     = module.networking.vpc_id
  database_subnet_ids        = module.networking.database_subnet_ids
  allowed_security_groups    = [module.compute.ecs_tasks_security_group_id]
  node_type                  = "cache.t4g.medium"
  num_cache_nodes            = 2
  automatic_failover_enabled = true
  multi_az_enabled           = true
  snapshot_retention_limit   = 14
  tags                       = local.common_tags
}

module "compute" {
  source                     = "../../modules/compute"
  name_prefix                = local.name_prefix
  vpc_id                     = module.networking.vpc_id
  public_subnet_ids          = module.networking.public_subnet_ids
  private_subnet_ids         = module.networking.private_subnet_ids
  aws_region                 = var.aws_region
  task_cpu                   = 1024
  task_memory                = 2048
  container_image            = var.container_image
  desired_count              = 2
  enable_autoscaling         = true
  autoscaling_min_capacity   = 2
  autoscaling_max_capacity   = 5
  certificate_arn            = var.certificate_arn
  environment_variables      = [
    { name = "ENVIRONMENT", value = "staging" },
    { name = "DATABASE_HOST", value = module.database.db_instance_address },
    { name = "REDIS_HOST", value = module.cache.primary_endpoint_address }
  ]
  secrets                    = [{ name = "DATABASE_PASSWORD", valueFrom = module.database.db_password_secret_arn }]
  secret_arns                = [module.database.db_password_secret_arn]
  tags                       = local.common_tags
}

module "monitoring" {
  source                 = "../../modules/monitoring"
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

module "dns" {
  source         = "../../modules/dns"
  count          = var.domain_name != "" ? 1 : 0
  name_prefix    = local.name_prefix
  domain_name    = var.domain_name
  subdomain      = "staging"
  hosted_zone_id = var.hosted_zone_id
  alb_dns_name   = module.compute.alb_dns_name
  alb_zone_id    = module.compute.alb_zone_id
  alarm_actions  = [module.monitoring.sns_topic_arn]
  tags           = local.common_tags
}

data "aws_availability_zones" "available" { state = "available" }
