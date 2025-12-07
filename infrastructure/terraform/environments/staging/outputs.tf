output "alb_dns_name" { value = module.compute.alb_dns_name }
output "ecr_repository_url" { value = module.compute.ecr_repository_url }
output "database_endpoint" { value = module.database.db_instance_endpoint; sensitive = true }
output "redis_endpoint" { value = module.cache.primary_endpoint_address }
output "application_url" { value = var.domain_name != "" ? "https://staging.${var.domain_name}" : "https://${module.compute.alb_dns_name}" }
