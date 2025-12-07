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
  environment = "production"
  common_tags = { Project = "CONTINUUM"; Environment = local.environment; ManagedBy = "Terraform" }
  name_prefix = "continuum-${local.environment}"
}

module "networking" {
  source                 = "../../modules/networking"
  name_prefix            = local.name_prefix
  vpc_cidr               = var.vpc_cidr
  availability_zones     = slice(data.aws_availability_zones.available.names, 0, 3)
  public_subnet_cidrs    = [for i in range(3) : cidrsubnet(var.vpc_cidr, 4, i)]
  private_subnet_cidrs   = [for i in range(3) : cidrsubnet(var.vpc_cidr, 4, i + 3)]
  database_subnet_cidrs  = [for i in range(3) : cidrsubnet(var.vpc_cidr, 4, i + 6)]
  enable_nat_gateway     = true
  single_nat_gateway     = false
  enable_flow_logs       = true
  enable_vpc_endpoints   = true
  enable_network_acls    = true
  flow_logs_retention_days = 30
  aws_region             = var.aws_region
  tags                   = local.common_tags
}

module "database" {
  source                       = "../../modules/database"
  name_prefix                  = local.name_prefix
  vpc_id                       = module.networking.vpc_id
  database_subnet_ids          = module.networking.database_subnet_ids
  allowed_security_groups      = [module.compute.ecs_tasks_security_group_id]
  instance_class               = "db.r6g.large"
  allocated_storage            = 100
  max_allocated_storage        = 1000
  storage_type                 = "gp3"
  iops                         = 3000
  multi_az                     = true
  backup_retention_period      = 30
  skip_final_snapshot          = false
  deletion_protection          = true
  performance_insights_enabled = true
  monitoring_interval          = 60
  read_replica_count           = 2
  create_cloudwatch_alarms     = true
  tags                         = local.common_tags
}

module "cache" {
  source                     = "../../modules/cache"
  name_prefix                = local.name_prefix
  vpc_id                     = module.networking.vpc_id
  database_subnet_ids        = module.networking.database_subnet_ids
  allowed_security_groups    = [module.compute.ecs_tasks_security_group_id]
  node_type                  = "cache.r6g.large"
  cluster_mode_enabled       = true
  num_node_groups            = 3
  replicas_per_node_group    = 2
  automatic_failover_enabled = true
  multi_az_enabled           = true
  snapshot_retention_limit   = 30
  transit_encryption_enabled = true
  create_cloudwatch_alarms   = true
  tags                       = local.common_tags
}

module "compute" {
  source                     = "../../modules/compute"
  name_prefix                = local.name_prefix
  vpc_id                     = module.networking.vpc_id
  public_subnet_ids          = module.networking.public_subnet_ids
  private_subnet_ids         = module.networking.private_subnet_ids
  aws_region                 = var.aws_region
  task_cpu                   = 2048
  task_memory                = 4096
  container_image            = var.container_image
  desired_count              = 3
  enable_autoscaling         = true
  autoscaling_min_capacity   = 3
  autoscaling_max_capacity   = 10
  autoscaling_cpu_target     = 70
  autoscaling_memory_target  = 80
  alb_deletion_protection    = true
  certificate_arn            = var.certificate_arn
  enable_container_insights  = true
  environment_variables      = [
    { name = "ENVIRONMENT", value = "production" },
    { name = "DATABASE_HOST", value = module.database.db_instance_address },
    { name = "REDIS_HOST", value = module.cache.configuration_endpoint_address }
  ]
  secrets                    = [{ name = "DATABASE_PASSWORD", valueFrom = module.database.db_password_secret_arn }]
  secret_arns                = [module.database.db_password_secret_arn]
  tags                       = local.common_tags
}

module "cdn" {
  source              = "../../modules/cdn"
  name_prefix         = local.name_prefix
  origin_domain_name  = module.compute.alb_dns_name
  domain_aliases      = var.cdn_domain_aliases
  acm_certificate_arn = var.cdn_certificate_arn
  web_acl_arn         = var.waf_web_acl_arn
  price_class         = "PriceClass_All"
  logging_bucket      = var.cdn_logging_bucket
  tags                = local.common_tags
}

module "monitoring" {
  source                    = "../../modules/monitoring"
  name_prefix               = local.name_prefix
  aws_region                = var.aws_region
  alarm_email               = var.alarm_email
  ecs_cluster_name          = module.compute.ecs_cluster_name
  alb_arn                   = module.compute.alb_arn
  db_instance_id            = module.database.db_instance_id
  elasticache_cluster_id    = module.cache.replication_group_id
  create_composite_alarms   = true
  error_log_group_name      = module.compute.cloudwatch_log_group_name
  tags                      = local.common_tags
}

module "dns" {
  source                        = "../../modules/dns"
  name_prefix                   = local.name_prefix
  domain_name                   = var.domain_name
  subdomain                     = var.subdomain
  hosted_zone_id                = var.hosted_zone_id
  alb_dns_name                  = module.compute.alb_dns_name
  alb_zone_id                   = module.compute.alb_zone_id
  create_health_check           = true
  health_check_failure_threshold = 3
  alarm_actions                 = [module.monitoring.sns_topic_arn]
  tags                          = local.common_tags
}

data "aws_availability_zones" "available" { state = "available" }
