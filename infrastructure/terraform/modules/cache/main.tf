# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.name_prefix}-cache-subnet-group"
  subnet_ids = var.database_subnet_ids

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-cache-subnet-group"
    }
  )
}

# ElastiCache Parameter Group
resource "aws_elasticache_parameter_group" "main" {
  name   = "${var.name_prefix}-cache-params"
  family = var.parameter_group_family

  # Redis configuration
  parameter {
    name  = "maxmemory-policy"
    value = var.maxmemory_policy
  }

  parameter {
    name  = "timeout"
    value = var.timeout
  }

  parameter {
    name  = "tcp-keepalive"
    value = "300"
  }

  parameter {
    name  = "maxmemory-samples"
    value = "5"
  }

  # Enable notifications for keyspace events
  parameter {
    name  = "notify-keyspace-events"
    value = var.notify_keyspace_events
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-cache-params"
    }
  )
}

# Security Group for ElastiCache
resource "aws_security_group" "cache" {
  name        = "${var.name_prefix}-cache-sg"
  description = "Security group for Redis ElastiCache cluster"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = var.allowed_security_groups
    description     = "Redis from application"
  }

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
    description = "Redis from allowed CIDRs"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-cache-sg"
    }
  )
}

# KMS Key for encryption
resource "aws_kms_key" "cache" {
  count                   = var.enable_encryption ? 1 : 0
  description             = "KMS key for ${var.name_prefix} cache encryption"
  deletion_window_in_days = var.kms_deletion_window
  enable_key_rotation     = var.enable_key_rotation

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-cache-kms"
    }
  )
}

resource "aws_kms_alias" "cache" {
  count         = var.enable_encryption ? 1 : 0
  name          = "alias/${var.name_prefix}-cache"
  target_key_id = aws_kms_key.cache[0].key_id
}

# ElastiCache Replication Group (Redis Cluster)
resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = "${var.name_prefix}-cache"
  replication_group_description = "Redis cache for ${var.name_prefix}"
  engine                     = "redis"
  engine_version             = var.engine_version
  node_type                  = var.node_type
  port                       = 6379

  # Cluster configuration
  num_cache_clusters         = var.cluster_mode_enabled ? null : var.num_cache_nodes
  num_node_groups            = var.cluster_mode_enabled ? var.num_node_groups : null
  replicas_per_node_group    = var.cluster_mode_enabled ? var.replicas_per_node_group : null

  # Parameter group
  parameter_group_name = aws_elasticache_parameter_group.main.name

  # Network configuration
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.cache.id]

  # High availability
  automatic_failover_enabled = var.automatic_failover_enabled
  multi_az_enabled          = var.multi_az_enabled

  # Backup configuration
  snapshot_retention_limit = var.snapshot_retention_limit
  snapshot_window          = var.snapshot_window
  maintenance_window       = var.maintenance_window
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${var.name_prefix}-cache-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  # Encryption
  at_rest_encryption_enabled = var.enable_encryption
  kms_key_id                 = var.enable_encryption ? aws_kms_key.cache[0].arn : null
  transit_encryption_enabled = var.transit_encryption_enabled
  auth_token                 = var.transit_encryption_enabled && var.auth_token != "" ? var.auth_token : null

  # Logging
  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.slow_log[0].name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "slow-log"
  }

  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.engine_log[0].name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "engine-log"
  }

  # Updates
  auto_minor_version_upgrade = var.auto_minor_version_upgrade
  apply_immediately         = var.apply_immediately

  # Notifications
  notification_topic_arn = var.notification_topic_arn

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-cache"
    }
  )

  lifecycle {
    ignore_changes = [
      final_snapshot_identifier,
      num_cache_clusters  # Allow scaling without recreation
    ]
  }
}

# CloudWatch Log Groups for Redis logs
resource "aws_cloudwatch_log_group" "slow_log" {
  count             = 1
  name              = "/aws/elasticache/${var.name_prefix}-cache/slow-log"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "engine_log" {
  count             = 1
  name              = "/aws/elasticache/${var.name_prefix}-cache/engine-log"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# CloudWatch alarms for cache
resource "aws_cloudwatch_metric_alarm" "cache_cpu" {
  count               = var.create_cloudwatch_alarms ? 1 : 0
  alarm_name          = "${var.name_prefix}-cache-cpu-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = var.cpu_alarm_threshold
  alarm_description   = "This metric monitors ElastiCache CPU utilization"
  alarm_actions       = var.alarm_actions

  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.main.id
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "cache_memory" {
  count               = var.create_cloudwatch_alarms ? 1 : 0
  alarm_name          = "${var.name_prefix}-cache-memory-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = var.memory_alarm_threshold
  alarm_description   = "This metric monitors ElastiCache memory utilization"
  alarm_actions       = var.alarm_actions

  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.main.id
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "cache_evictions" {
  count               = var.create_cloudwatch_alarms ? 1 : 0
  alarm_name          = "${var.name_prefix}-cache-evictions"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Evictions"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Sum"
  threshold           = var.evictions_alarm_threshold
  alarm_description   = "This metric monitors ElastiCache evictions"
  alarm_actions       = var.alarm_actions

  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.main.id
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "cache_connections" {
  count               = var.create_cloudwatch_alarms ? 1 : 0
  alarm_name          = "${var.name_prefix}-cache-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CurrConnections"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = var.connections_alarm_threshold
  alarm_description   = "This metric monitors ElastiCache current connections"
  alarm_actions       = var.alarm_actions

  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.main.id
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "cache_replication_lag" {
  count               = var.create_cloudwatch_alarms && var.automatic_failover_enabled ? 1 : 0
  alarm_name          = "${var.name_prefix}-cache-replication-lag"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ReplicationLag"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = var.replication_lag_alarm_threshold
  alarm_description   = "This metric monitors ElastiCache replication lag"
  alarm_actions       = var.alarm_actions

  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.main.id
  }

  tags = var.tags
}
