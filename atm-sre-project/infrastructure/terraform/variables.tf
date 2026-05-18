# ── Provider / credentials ────────────────────────────────────────────────────

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "aws_access_key" {
  description = "AWS access key (use 'test' for LocalStack)"
  type        = string
  sensitive   = true
}

variable "aws_secret_key" {
  description = "AWS secret key (use 'test' for LocalStack)"
  type        = string
  sensitive   = true
}

variable "localstack_endpoint" {
  description = "LocalStack endpoint URL. Set to '' (empty) when targeting real AWS."
  type        = string
}

# ── Project ───────────────────────────────────────────────────────────────────

variable "project_name" {
  description = "Project name used for resource tagging"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev | staging | prod)"
  type        = string
}

# ── Networking — reference existing IDs, not managed here ─────────────────────

variable "vpc_id" {
  description = "ID of an existing VPC to place instances in"
  type        = string
}

variable "public_subnet_id" {
  description = "ID of an existing public subnet (app + monitoring servers)"
  type        = string
}

variable "private_subnet_id" {
  description = "ID of an existing private subnet (database server)"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR of the VPC — used to scope security group ingress rules"
  type        = string
}

# ── EC2 ───────────────────────────────────────────────────────────────────────

variable "ami_id" {
  description = "AMI ID for EC2 instances (Ubuntu 22.04 LTS)"
  type        = string
}

variable "app_instance_type" {
  description = "EC2 instance type for the application server"
  type        = string
}

variable "db_instance_type" {
  description = "EC2 instance type for the database server"
  type        = string
}

variable "monitoring_instance_type" {
  description = "EC2 instance type for the monitoring server"
  type        = string
}

variable "key_pair_name" {
  description = "EC2 key pair name for SSH access"
  type        = string
  sensitive   = true
}

# ── Ports ─────────────────────────────────────────────────────────────────────

variable "port_ssh" {
  description = "SSH port"
  type        = number
  sensitive   = true
}

variable "port_http" {
  description = "HTTP port"
  type        = number
  sensitive   = true
}

variable "port_gateway" {
  description = "API Gateway port"
  type        = number
  sensitive   = true
}

variable "port_frontend" {
  description = "Frontend port"
  type        = number
  sensitive   = true
}

variable "port_grafana" {
  description = "Grafana port"
  type        = number
  sensitive   = true
}

variable "port_prometheus" {
  description = "Prometheus port"
  type        = number
  sensitive   = true
}

variable "port_postgres" {
  description = "PostgreSQL port"
  type        = number
  sensitive   = true
}

variable "port_mongo" {
  description = "MongoDB port"
  type        = number
  sensitive   = true
}

variable "port_redis" {
  description = "Redis port"
  type        = number
  sensitive   = true
}
