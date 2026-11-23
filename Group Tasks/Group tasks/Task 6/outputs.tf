output "application_endpoint" {
  description = "Future restricted HTTP endpoint, computed from the instance. Unknown during the offline plan; not a live URL."
  value       = "http://${aws_instance.app.public_ip}:8000"
}
output "instance_id" {
  description = "Future EC2 instance ID."
  value       = aws_instance.app.id
}
output "network_id" {
  description = "Future application VPC ID."
  value       = aws_vpc.app.id
}
output "log_group" {
  description = "Application log group name."
  value       = aws_cloudwatch_log_group.app.name
}
output "data_location" {
  description = "Application data and ChromaDB share a bind-mounted encrypted host volume."
  value       = "/opt/document-ai/data"
}
