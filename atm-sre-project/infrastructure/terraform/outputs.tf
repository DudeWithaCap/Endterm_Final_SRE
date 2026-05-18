output "app_server_public_ip" {
  description = "Public IP of the application server"
  value       = aws_eip.app_server.public_ip
}

output "app_server_private_ip" {
  description = "Private IP of the application server"
  value       = aws_instance.app_server.private_ip
}

output "db_server_private_ip" {
  description = "Private IP of the database server"
  value       = aws_instance.db_server.private_ip
}

output "monitoring_server_public_ip" {
  description = "Public IP of the monitoring server"
  value       = aws_eip.monitoring_server.public_ip
}

output "gateway_url" {
  description = "API Gateway URL"
  value       = "http://${aws_eip.app_server.public_ip}:8000"
}

output "frontend_url" {
  description = "Frontend URL"
  value       = "http://${aws_eip.app_server.public_ip}:3000"
}

output "grafana_url" {
  description = "Grafana URL"
  value       = "http://${aws_eip.monitoring_server.public_ip}:3001"
}

output "prometheus_url" {
  description = "Prometheus URL"
  value       = "http://${aws_eip.monitoring_server.public_ip}:9090"
}
