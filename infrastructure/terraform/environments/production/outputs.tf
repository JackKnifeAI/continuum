output "alb_dns_name" { value = module.compute.alb_dns_name }
output "cdn_domain_name" { value = module.cdn.distribution_domain_name }
output "ecr_repository_url" { value = module.compute.ecr_repository_url }
output "database_endpoint" { value = module.database.db_instance_endpoint; sensitive = true }
output "database_read_replica_endpoints" { value = module.database.read_replica_endpoints; sensitive = true }
output "redis_endpoint" { value = module.cache.configuration_endpoint_address }
output "application_url" { value = "https://${var.domain_name}" }
output "cloudwatch_dashboard" { value = module.monitoring.dashboard_name }
