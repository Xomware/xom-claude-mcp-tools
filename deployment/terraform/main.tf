terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "xom-terraform-state"
    key            = "mcp-tools/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-lock"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = "xom-mcp-tools"
      ManagedBy   = "terraform"
    }
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "xom-mcp-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/xom-mcp"
  retention_in_days = 7

  tags = {
    Name = "xom-mcp-logs"
  }
}

# ECR Repository for each MCP
resource "aws_ecr_repository" "mcp_repos" {
  for_each = toset(["github-mcp", "slack-mcp", "database-mcp", "xomware-api-mcp"])

  name                 = "xom/${each.value}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "xom-${each.value}"
  }
}

# RDS PostgreSQL Database
resource "aws_db_instance" "postgres" {
  deletion_protection       = true
  allocated_storage         = var.db_storage
  storage_type              = "gp3"
  engine                    = "postgres"
  engine_version            = "15.3"
  instance_class            = var.db_instance_class
  db_name                   = "xomware"
  username                  = "xomware"
  password                  = random_password.db_password.result
  parameter_group_name      = aws_db_parameter_group.postgres.name
  skip_final_snapshot       = false
  final_snapshot_identifier = "xom-mcp-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"

  multi_az = var.db_multi_az

  tags = {
    Name = "xom-mcp-db"
  }
}

# DB Parameter Group
resource "aws_db_parameter_group" "postgres" {
  family = "postgres15"
  name   = "xom-mcp-postgres"

  parameter {
    name  = "log_statement"
    value = "all"
  }

  tags = {
    Name = "xom-mcp-postgres-params"
  }
}

# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "xom-mcp-db-subnet"
  subnet_ids = var.database_subnets

  tags = {
    Name = "xom-mcp-db-subnet-group"
  }
}

# Security Group for RDS
resource "aws_security_group" "rds" {
  name        = "xom-mcp-rds-sg"
  description = "Security group for RDS database"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "xom-mcp-rds-sg"
  }
}

# Security Group for ECS Tasks
resource "aws_security_group" "ecs_tasks" {
  name        = "xom-mcp-ecs-tasks-sg"
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 8000
    to_port         = 8099
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "xom-mcp-ecs-tasks-sg"
  }
}

# Security Group for ALB
resource "aws_security_group" "alb" {
  name        = "xom-mcp-alb-sg"
  description = "Security group for ALB"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "xom-mcp-alb-sg"
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "xom-mcp-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.alb_subnets

  tags = {
    Name = "xom-mcp-alb"
  }
}

# ALB Target Group
resource "aws_lb_target_group" "mcp" {
  name        = "xom-mcp-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 3
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }

  tags = {
    Name = "xom-mcp-tg"
  }
}

# ALB Listener
resource "aws_lb_listener" "mcp" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.mcp.arn
  }
}

# Random password for RDS
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Secrets Manager for DB Password
resource "aws_secretsmanager_secret" "db_password" {
  name = "xom-mcp/db-password"

  tags = {
    Name = "xom-mcp-db-password"
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
}

# Output values
output "rds_endpoint" {
  description = "RDS database endpoint"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = false
}

output "rds_database_name" {
  description = "RDS database name"
  value       = aws_db_instance.postgres.db_name
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.main.dns_name
}

output "ecr_repository_urls" {
  description = "ECR repository URLs"
  value = {
    for name, repo in aws_ecr_repository.mcp_repos : name => repo.repository_url
  }
}
