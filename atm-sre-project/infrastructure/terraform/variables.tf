# ── Provider / credentials ────────────────────────────────────────────────────

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "aws_access_key" {
  description = "AWS access key"
  type        = string
  sensitive   = true
}

variable "aws_secret_key" {
  description = "AWS secret key"
  type        = string
  sensitive   = true
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

# ── EC2 ───────────────────────────────────────────────────────────────────────

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

variable "port_services_start" {
  description = "First microservice port (auth 8001)"
  type        = number
  sensitive   = true
}

variable "port_services_end" {
  description = "Last microservice port (background-load 8006)"
  type        = number
  sensitive   = true
}
