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
}

locals {
  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
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
  vpc_id      = data.aws_vpc.default.id

  ingress { from_port = var.port_ssh;        to_port = var.port_ssh;        protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"]; description = "SSH" }
  ingress { from_port = var.port_http;       to_port = var.port_http;       protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"]; description = "HTTP" }
  ingress { from_port = var.port_gateway;    to_port = var.port_gateway;    protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"]; description = "API Gateway" }
  ingress { from_port = var.port_services_start; to_port = var.port_services_end; protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"]; description = "Microservices" }
  ingress { from_port = var.port_frontend;   to_port = var.port_frontend;   protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"]; description = "Frontend" }
  ingress { from_port = var.port_grafana;    to_port = var.port_grafana;    protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"]; description = "Grafana" }
  ingress { from_port = var.port_prometheus; to_port = var.port_prometheus; protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"]; description = "Prometheus" }
  egress  { from_port = 0;                   to_port = 0;                   protocol = "-1";  cidr_blocks = ["0.0.0.0/0"] }

  tags = merge(local.tags, { Name = "${var.project_name}-sg-public" })
}

resource "aws_security_group" "internal" {
  name        = "${var.project_name}-sg-internal"
  description = "All traffic within VPC"
  vpc_id      = data.aws_vpc.default.id

  ingress { from_port = 0; to_port = 0; protocol = "-1"; cidr_blocks = [data.aws_vpc.default.cidr_block] }
  egress  { from_port = 0; to_port = 0; protocol = "-1"; cidr_blocks = ["0.0.0.0/0"] }

  tags = merge(local.tags, { Name = "${var.project_name}-sg-internal" })
}

resource "aws_security_group" "databases" {
  name        = "${var.project_name}-sg-databases"
  description = "DB ports from VPC only"
  vpc_id      = data.aws_vpc.default.id

  ingress { from_port = var.port_postgres; to_port = var.port_postgres; protocol = "tcp"; cidr_blocks = [data.aws_vpc.default.cidr_block]; description = "PostgreSQL" }
  ingress { from_port = var.port_mongo;    to_port = var.port_mongo;    protocol = "tcp"; cidr_blocks = [data.aws_vpc.default.cidr_block]; description = "MongoDB" }
  ingress { from_port = var.port_redis;    to_port = var.port_redis;    protocol = "tcp"; cidr_blocks = [data.aws_vpc.default.cidr_block]; description = "Redis" }
  ingress { from_port = var.port_ssh;      to_port = var.port_ssh;      protocol = "tcp"; cidr_blocks = [data.aws_vpc.default.cidr_block]; description = "SSH" }
  egress  { from_port = 0;                 to_port = 0;                 protocol = "-1";  cidr_blocks = ["0.0.0.0/0"] }

  tags = merge(local.tags, { Name = "${var.project_name}-sg-databases" })
}

resource "aws_security_group" "monitoring" {
  name        = "${var.project_name}-sg-monitoring"
  description = "Prometheus and Grafana"
  vpc_id      = data.aws_vpc.default.id

  ingress { from_port = var.port_prometheus; to_port = var.port_prometheus; protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"]; description = "Prometheus" }
  ingress { from_port = var.port_grafana;    to_port = var.port_grafana;    protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"]; description = "Grafana" }
  ingress { from_port = var.port_ssh;        to_port = var.port_ssh;        protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"]; description = "SSH" }
  egress  { from_port = 0;                   to_port = 0;                   protocol = "-1";  cidr_blocks = ["0.0.0.0/0"] }

  tags = merge(local.tags, { Name = "${var.project_name}-sg-monitoring" })
}


resource "aws_instance" "app_server" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.app_instance_type
  subnet_id              = data.aws_subnets.default.ids[0]
  key_name               = aws_key_pair.main.key_name
  vpc_security_group_ids = [aws_security_group.public.id, aws_security_group.internal.id]

  root_block_device { volume_size = 20; volume_type = "gp3" }

  user_data = <<-EOF
    #!/bin/bash
    apt-get update -y
    apt-get install -y curl git
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker ubuntu
    mkdir -p /home/ubuntu/.kube
    chown ubuntu:ubuntu /home/ubuntu/.kube
  EOF

  tags = merge(local.tags, { Name = "${var.project_name}-app-server", Role = "app" })
}

resource "aws_instance" "db_server" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.db_instance_type
  subnet_id              = data.aws_subnets.default.ids[1]
  key_name               = aws_key_pair.main.key_name
  vpc_security_group_ids = [aws_security_group.databases.id, aws_security_group.internal.id]

  root_block_device { volume_size = 30; volume_type = "gp3" }

  tags = merge(local.tags, { Name = "${var.project_name}-db-server", Role = "database" })
}

resource "aws_instance" "monitoring_server" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.monitoring_instance_type
  subnet_id              = data.aws_subnets.default.ids[0]
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
