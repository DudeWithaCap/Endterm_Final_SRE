terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "local" {}
}

provider "aws" {
  region     = var.aws_region
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key

  # LocalStack endpoints — remove this block entirely for real AWS
  endpoints {
    ec2 = var.localstack_endpoint
    iam = var.localstack_endpoint
    sts = var.localstack_endpoint
  }

  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
}

locals {
  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ── Key Pair ──────────────────────────────────────────────────────────────────

resource "aws_key_pair" "main" {
  key_name   = var.key_pair_name
  public_key = file("~/.ssh/id_rsa.pub")
  tags       = local.tags
}

# ── Security Groups ───────────────────────────────────────────────────────────

resource "aws_security_group" "public" {
  name        = "${var.project_name}-sg-public"
  description = "HTTP and SSH from internet"
  vpc_id      = var.vpc_id

  ingress { from_port = var.port_ssh;      to_port = var.port_ssh;      protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"]; description = "SSH" }
  ingress { from_port = var.port_http;     to_port = var.port_http;     protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"]; description = "HTTP" }
  ingress { from_port = var.port_gateway;  to_port = var.port_gateway;  protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"]; description = "API Gateway" }
  ingress { from_port = var.port_frontend; to_port = var.port_frontend; protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"]; description = "Frontend" }
  ingress { from_port = var.port_grafana;  to_port = var.port_grafana;  protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"]; description = "Grafana" }
  egress  { from_port = 0;                 to_port = 0;                 protocol = "-1";  cidr_blocks = ["0.0.0.0/0"] }

  tags = merge(local.tags, { Name = "${var.project_name}-sg-public" })
}

resource "aws_security_group" "internal" {
  name        = "${var.project_name}-sg-internal"
  description = "All traffic within VPC"
  vpc_id      = var.vpc_id

  ingress { from_port = 0; to_port = 0; protocol = "-1"; cidr_blocks = [var.vpc_cidr] }
  egress  { from_port = 0; to_port = 0; protocol = "-1"; cidr_blocks = ["0.0.0.0/0"] }

  tags = merge(local.tags, { Name = "${var.project_name}-sg-internal" })
}

resource "aws_security_group" "databases" {
  name        = "${var.project_name}-sg-databases"
  description = "DB ports from VPC only"
  vpc_id      = var.vpc_id

  ingress { from_port = var.port_postgres; to_port = var.port_postgres; protocol = "tcp"; cidr_blocks = [var.vpc_cidr]; description = "PostgreSQL" }
  ingress { from_port = var.port_mongo;    to_port = var.port_mongo;    protocol = "tcp"; cidr_blocks = [var.vpc_cidr]; description = "MongoDB" }
  ingress { from_port = var.port_redis;    to_port = var.port_redis;    protocol = "tcp"; cidr_blocks = [var.vpc_cidr]; description = "Redis" }
  ingress { from_port = var.port_ssh;      to_port = var.port_ssh;      protocol = "tcp"; cidr_blocks = [var.vpc_cidr]; description = "SSH" }
  egress  { from_port = 0;                 to_port = 0;                 protocol = "-1";  cidr_blocks = ["0.0.0.0/0"] }

  tags = merge(local.tags, { Name = "${var.project_name}-sg-databases" })
}

resource "aws_security_group" "monitoring" {
  name        = "${var.project_name}-sg-monitoring"
  description = "Prometheus and Grafana"
  vpc_id      = var.vpc_id

  ingress { from_port = var.port_prometheus; to_port = var.port_prometheus; protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"]; description = "Prometheus" }
  ingress { from_port = var.port_grafana;    to_port = var.port_grafana;    protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"]; description = "Grafana" }
  ingress { from_port = var.port_ssh;        to_port = var.port_ssh;        protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"]; description = "SSH" }
  egress  { from_port = 0;                   to_port = 0;                   protocol = "-1";  cidr_blocks = ["0.0.0.0/0"] }

  tags = merge(local.tags, { Name = "${var.project_name}-sg-monitoring" })
}

# ── EC2 Instances ─────────────────────────────────────────────────────────────

resource "aws_instance" "app_server" {
  ami                    = var.ami_id
  instance_type          = var.app_instance_type
  subnet_id              = var.public_subnet_id
  key_name               = aws_key_pair.main.key_name
  vpc_security_group_ids = [aws_security_group.public.id, aws_security_group.internal.id]

  root_block_device { volume_size = 20; volume_type = "gp3" }
  user_data = "#!/bin/bash\napt-get update -y && apt-get install -y curl git"

  tags = merge(local.tags, { Name = "${var.project_name}-app-server", Role = "app" })
}

resource "aws_instance" "db_server" {
  ami                    = var.ami_id
  instance_type          = var.db_instance_type
  subnet_id              = var.private_subnet_id
  key_name               = aws_key_pair.main.key_name
  vpc_security_group_ids = [aws_security_group.databases.id, aws_security_group.internal.id]

  root_block_device { volume_size = 30; volume_type = "gp3" }

  tags = merge(local.tags, { Name = "${var.project_name}-db-server", Role = "database" })
}

resource "aws_instance" "monitoring_server" {
  ami                    = var.ami_id
  instance_type          = var.monitoring_instance_type
  subnet_id              = var.public_subnet_id
  key_name               = aws_key_pair.main.key_name
  vpc_security_group_ids = [aws_security_group.monitoring.id, aws_security_group.internal.id]

  root_block_device { volume_size = 15; volume_type = "gp3" }

  tags = merge(local.tags, { Name = "${var.project_name}-monitoring-server", Role = "monitoring" })
}

# ── Elastic IPs ───────────────────────────────────────────────────────────────

resource "aws_eip" "app_server" {
  instance = aws_instance.app_server.id
  domain   = "vpc"
  tags     = merge(local.tags, { Name = "${var.project_name}-app-eip" })
}

resource "aws_eip" "monitoring_server" {
  instance = aws_instance.monitoring_server.id
  domain   = "vpc"
  tags     = merge(local.tags, { Name = "${var.project_name}-monitoring-eip" })
}
