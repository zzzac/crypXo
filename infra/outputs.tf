# outputs.tf
output "vpc_id" {
  value       = aws_vpc.main.id
  description = "VPC ID"
}

output "public_subnet_id" {
  value       = aws_subnet.public.id
  description = "Public subnet ID"
}

output "private_subnet_ids" {
  value       = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  description = "Private subnet IDs"
}

output "airflow_instance_id" {
  value       = aws_instance.airflow.id
  description = "Airflow EC2 instance ID"
}

output "airflow_public_ip" {
  value       = aws_instance.airflow.public_ip
  description = "Airflow EC2 public IP (only useful if you open 8080 or use SSH)."
}

output "data_bucket_name" {
  value       = var.create_data_bucket ? aws_s3_bucket.data[0].bucket : var.data_bucket_name
  description = "S3 data bucket name"
}
