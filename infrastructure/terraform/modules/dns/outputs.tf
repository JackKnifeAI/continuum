output "hosted_zone_id" { value = var.create_hosted_zone ? aws_route53_zone.main[0].zone_id : var.hosted_zone_id }
output "hosted_zone_name_servers" { value = var.create_hosted_zone ? aws_route53_zone.main[0].name_servers : [] }
output "record_fqdn" { value = var.alb_dns_name != "" ? aws_route53_record.alb[0].fqdn : "" }
output "health_check_id" { value = var.create_health_check ? aws_route53_health_check.main[0].id : "" }
