# variables.tf
variable "project" {
  description = "A short project prefix used for naming."
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-2"
}

variable "vpc_cidr" {
  description = "VPC CIDR"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "Public subnet CIDR"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_a_cidr" {
  description = "Private subnet A CIDR"
  type        = string
  default     = "10.0.2.0/24"
}

variable "private_subnet_b_cidr" {
  description = "Private subnet B CIDR"
  type        = string
  default     = "10.0.3.0/24"
}

variable "allow_web_cidr" {
  description = "CIDR allowed to access Airflow web (port 8080). Leave empty string to disable."
  type        = string
  default     = ""
}

variable "instance_type" {
  description = "EC2 instance type for the Airflow controller"
  type        = string
  default     = "t3a.large"
}

variable "key_name" {
  description = "(Optional) EC2 key pair name if you want SSH (not required when using SSM)."
  type        = string
  default     = null
}

variable "data_bucket_name" {
  description = "S3 bucket name to store data (must be globally unique)."
  type        = string
}

variable "create_data_bucket" {
  description = "Whether to create the S3 data bucket."
  type        = bool
  default     = true
}

variable "data_bucket_lifecycle_days_glacier" {
  description = "Days before transitioning to GLACIER storage class"
  type        = number
  default     = 60
}
