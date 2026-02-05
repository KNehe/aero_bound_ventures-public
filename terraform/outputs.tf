
output "instance_hostname" {
  description = "Private DNS name of the EC2 instance."
  value       = aws_instance.app_server.private_dns
}

output "ec2_public_ip" {
  value = aws_eip.app_eip.public_ip
}

output "application_url" {
  description = "URL of the running application"
  value       = "http://${aws_eip.app_eip.public_ip}:8000"
}