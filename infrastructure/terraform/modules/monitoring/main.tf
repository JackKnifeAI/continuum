# SNS Topic for Alarms
resource "aws_sns_topic" "alarms" {
  name              = "${var.name_prefix}-alarms"
  kms_master_key_id = var.enable_encryption ? aws_kms_key.sns[0].id : null
  tags              = var.tags
}

resource "aws_sns_topic_subscription" "alarms_email" {
  count     = var.alarm_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# KMS Key for SNS encryption
resource "aws_kms_key" "sns" {
  count                   = var.enable_encryption ? 1 : 0
  description             = "KMS key for ${var.name_prefix} SNS encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true
  tags                    = var.tags
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.name_prefix}-dashboard"
  dashboard_body = jsonencode({
    widgets = concat(
      var.ecs_cluster_name != "" ? [
        {
          type = "metric"
          properties = {
            metrics = [
              ["AWS/ECS", "CPUUtilization", { stat = "Average", period = 300 }],
              [".", "MemoryUtilization", { stat = "Average", period = 300 }]
            ]
            period = 300
            region = var.aws_region
            title  = "ECS Metrics"
          }
        }
      ] : [],
      var.alb_arn != "" ? [
        {
          type = "metric"
          properties = {
            metrics = [
              ["AWS/ApplicationELB", "TargetResponseTime", { stat = "Average", period = 60 }],
              [".", "RequestCount", { stat = "Sum", period = 60 }],
              [".", "HTTPCode_Target_2XX_Count", { stat = "Sum", period = 60 }],
              [".", "HTTPCode_Target_5XX_Count", { stat = "Sum", period = 60 }]
            ]
            period = 60
            region = var.aws_region
            title  = "ALB Metrics"
          }
        }
      ] : [],
      var.db_instance_id != "" ? [
        {
          type = "metric"
          properties = {
            metrics = [
              ["AWS/RDS", "CPUUtilization", { stat = "Average" }],
              [".", "DatabaseConnections", { stat = "Average" }],
              [".", "FreeStorageSpace", { stat = "Average" }]
            ]
            region = var.aws_region
            title  = "RDS Metrics"
          }
        }
      ] : [],
      var.elasticache_cluster_id != "" ? [
        {
          type = "metric"
          properties = {
            metrics = [
              ["AWS/ElastiCache", "CPUUtilization", { stat = "Average" }],
              [".", "DatabaseMemoryUsagePercentage", { stat = "Average" }],
              [".", "CurrConnections", { stat = "Average" }]
            ]
            region = var.aws_region
            title  = "ElastiCache Metrics"
          }
        }
      ] : []
    )
  })
}

# Composite Alarms
resource "aws_cloudwatch_composite_alarm" "critical" {
  count             = var.create_composite_alarms ? 1 : 0
  alarm_name        = "${var.name_prefix}-critical-alarm"
  alarm_description = "Critical alarm triggered when multiple component alarms fire"
  actions_enabled   = true
  alarm_actions     = [aws_sns_topic.alarms.arn]

  alarm_rule = "ALARM(${var.name_prefix}-db-cpu-utilization) OR ALARM(${var.name_prefix}-cache-cpu-utilization)"

  tags = var.tags
}

# CloudWatch Log Metric Filters
resource "aws_cloudwatch_log_metric_filter" "errors" {
  count          = var.error_log_group_name != "" ? 1 : 0
  name           = "${var.name_prefix}-error-count"
  log_group_name = var.error_log_group_name
  pattern        = "[ERROR]"

  metric_transformation {
    name      = "ErrorCount"
    namespace = var.name_prefix
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "log_errors" {
  count               = var.error_log_group_name != "" ? 1 : 0
  alarm_name          = "${var.name_prefix}-log-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ErrorCount"
  namespace           = var.name_prefix
  period              = "300"
  statistic           = "Sum"
  threshold           = var.error_threshold
  alarm_description   = "Triggered when error count exceeds threshold"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  tags                = var.tags
}
