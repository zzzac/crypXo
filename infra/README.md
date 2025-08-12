# README.md

## What this stack creates
- 1 VPC (10.0.0.0/16) with 1 public subnet + 2 private subnets across 2 AZs
- Internet Gateway, NAT Gateway (for private subnets to reach the internet)
- Route tables wired correctly (Public → IGW, Private → NAT)
- VPC Endpoints: S3 (Gateway), and Interface endpoints for SSM, EC2 Messages, SSM Messages, CloudWatch Logs
- EC2 instance for Airflow control plane (public subnet), **no inbound ports by default** (use SSM Session Manager)
- IAM Role & Instance Profile for EC2 with least-privilege S3 (scoped to your data bucket/prefix), CloudWatch Logs, and SSM access
- Optional S3 data lake bucket (versioned + basic lifecycle)

> Default region is `ap-southeast-2` (Sydney). You can change in `variables.tf`.

## How to use
```bash
terraform init
terraform plan -var "project=crypto-ai" -var "data_bucket_name=crypto-ai-data-lake-<your-unique-suffix>"
terraform apply -auto-approve -var "project=crypto-ai" -var "data_bucket_name=crypto-ai-data-lake-<your-unique-suffix>"
```

After apply:
- Find the EC2 instance named `airflow-controller` in the console.
- Connect with **Session Manager** (no SSH needed).
- The instance user data has Docker installed. You can place your Airflow docker-compose later (we'll add in a follow-up).

## Optional: open Airflow web temporarily
Set `allow_web_cidr` to your IP in CIDR (e.g., `1.2.3.4/32`) and re-apply. This opens port 8080 to that CIDR.

---

# versions.tf
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

# providers.tf
provider "aws" {
  region = var.region
}

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

# locals.tf
locals {
  name_prefix = var.project
  tags = {
    Project = var.project
    Owner   = "${var.project}-platform"
    Stack   = "infra-minimal"
  }
}

# vpc.tf
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = merge(local.tags, { Name = "${local.name_prefix}-vpc" })
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags   = merge(local.tags, { Name = "${local.name_prefix}-igw" })
}

data "aws_availability_zones" "available" {}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr
  map_public_ip_on_launch = true
  availability_zone       = data.aws_availability_zones.available.names[0]
  tags = merge(local.tags, { Name = "${local.name_prefix}-public-az1", Tier = "public" })
}

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_a_cidr
  availability_zone = data.aws_availability_zones.available.names[0]
  tags = merge(local.tags, { Name = "${local.name_prefix}-private-az1", Tier = "private" })
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_b_cidr
  availability_zone = data.aws_availability_zones.available.names[1]
  tags = merge(local.tags, { Name = "${local.name_prefix}-private-az2", Tier = "private" })
}

resource "aws_eip" "nat_eip" {
  domain = "vpc"
  tags   = merge(local.tags, { Name = "${local.name_prefix}-nat-eip" })
}

resource "aws_nat_gateway" "nat" {
  allocation_id = aws_eip.nat_eip.id
  subnet_id     = aws_subnet.public.id
  tags          = merge(local.tags, { Name = "${local.name_prefix}-nat" })
  depends_on    = [aws_internet_gateway.igw]
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  tags   = merge(local.tags, { Name = "${local.name_prefix}-rtb-public" })
}

resource "aws_route" "public_inet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.igw.id
}

resource "aws_route_table_association" "public_assoc" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private_a" {
  vpc_id = aws_vpc.main.id
  tags   = merge(local.tags, { Name = "${local.name_prefix}-rtb-private-a" })
}

resource "aws_route_table" "private_b" {
  vpc_id = aws_vpc.main.id
  tags   = merge(local.tags, { Name = "${local.name_prefix}-rtb-private-b" })
}

resource "aws_route" "private_a_nat" {
  route_table_id         = aws_route_table.private_a.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.nat.id
}

resource "aws_route" "private_b_nat" {
  route_table_id         = aws_route_table.private_b.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.nat.id
}

resource "aws_route_table_association" "private_a_assoc" {
  subnet_id      = aws_subnet.private_a.id
  route_table_id = aws_route_table.private_a.id
}

resource "aws_route_table_association" "private_b_assoc" {
  subnet_id      = aws_subnet.private_b.id
  route_table_id = aws_route_table.private_b.id
}

# endpoints.tf (VPC Endpoints)
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.public.id, aws_route_table.private_a.id, aws_route_table.private_b.id]
  tags              = merge(local.tags, { Name = "${local.name_prefix}-vpce-s3" })
}

locals {
  interface_endpoints = [
    "ssm",
    "ec2messages",
    "ssmmessages",
    "logs"
  ]
}

resource "aws_security_group" "endpoints" {
  name        = "${local.name_prefix}-vpce-sg"
  description = "SG for Interface Endpoints"
  vpc_id      = aws_vpc.main.id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = merge(local.tags, { Name = "${local.name_prefix}-vpce-sg" })
}

resource "aws_vpc_endpoint" "interfaces" {
  for_each = toset(local.interface_endpoints)

  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.${each.key}"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  security_group_ids  = [aws_security_group.endpoints.id]
  subnet_ids          = [aws_subnet.private_a.id, aws_subnet.private_b.id]

  tags = merge(local.tags, { Name = "${local.name_prefix}-vpce-${each.key}" })
}

# s3.tf (optional data bucket)
resource "aws_s3_bucket" "data" {
  count = var.create_data_bucket ? 1 : 0
  bucket = var.data_bucket_name
  force_destroy = false
  tags = merge(local.tags, { Name = var.data_bucket_name })
}

resource "aws_s3_bucket_public_access_block" "data" {
  count                     = var.create_data_bucket ? 1 : 0
  bucket                    = aws_s3_bucket.data[0].id
  block_public_acls         = true
  block_public_policy       = true
  ignore_public_acls        = true
  restrict_public_buckets   = true
}

resource "aws_s3_bucket_versioning" "data" {
  count  = var.create_data_bucket ? 1 : 0
  bucket = aws_s3_bucket.data[0].id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "data" {
  count  = var.create_data_bucket ? 1 : 0
  bucket = aws_s3_bucket.data[0].id

  rule {
    id     = "to-glacier"
    status = "Enabled"

    transition {
      days          = var.data_bucket_lifecycle_days_glacier
      storage_class = "GLACIER"
    }
  }
}

# iam.tf (EC2 role w/ SSM + Logs + scoped S3)
data "aws_iam_policy_document" "assume_ec2" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ec2_role" {
  name               = "${local.name_prefix}-ec2-role"
  assume_role_policy = data.aws_iam_policy_document.assume_ec2.json
  tags               = local.tags
}

# Managed policy for SSM
resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# CloudWatch Logs basic access
resource "aws_iam_role_policy_attachment" "cw_logs" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

# Scoped S3 access to the specific bucket
data "aws_iam_policy_document" "s3_scoped" {
  statement {
    sid     = "S3ListBucket"
    actions = ["s3:ListBucket"]
    resources = [
      var.create_data_bucket ? aws_s3_bucket.data[0].arn : "arn:aws:s3:::${var.data_bucket_name}"
    ]
  }
  statement {
    sid = "S3RWOnPrefix"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucketMultipartUploads",
      "s3:AbortMultipartUpload"
    ]
    resources = [
      var.create_data_bucket ? "${aws_s3_bucket.data[0].arn}/*" : "arn:aws:s3:::${var.data_bucket_name}/*"
    ]
  }
}

resource "aws_iam_policy" "s3_scoped" {
  name   = "${local.name_prefix}-s3-scoped"
  policy = data.aws_iam_policy_document.s3_scoped.json
}

resource "aws_iam_role_policy_attachment" "s3_attach" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.s3_scoped.arn
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${local.name_prefix}-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

# security.tf
resource "aws_security_group" "airflow" {
  name        = "${local.name_prefix}-airflow-sg"
  description = "Airflow controller SG"
  vpc_id      = aws_vpc.main.id

  # No inbound by default (SSM only). Add optional 8080 if allow_web_cidr is set
  dynamic "ingress" {
    for_each = var.allow_web_cidr == "" ? [] : [1]
    content {
      description = "Airflow Web"
      from_port   = 8080
      to_port     = 8080
      protocol    = "tcp"
      cidr_blocks = [var.allow_web_cidr]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, { Name = "${local.name_prefix}-airflow-sg" })
}

# ec2_airflow.tf
# Use Amazon Linux 2023 x86_64 for broad compatibility
data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["137112412989"] # Amazon
  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

resource "aws_instance" "airflow" {
  ami                         = data.aws_ami.al2023.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public.id
  associate_public_ip_address = true
  iam_instance_profile        = aws_iam_instance_profile.ec2_profile.name
  vpc_security_group_ids      = [aws_security_group.airflow.id]
  key_name                    = var.key_name

  user_data = <<-EOF
              #!/bin/bash
              set -eux
              yum update -y
              # install docker & compose plugin
              amazon-linux-extras enable docker || true
              yum install -y docker git
              usermod -aG docker ec2-user
              systemctl enable docker
              systemctl start docker
              # docker compose plugin
              curl -L "https://github.com/docker/compose/releases/download/2.27.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
              chmod +x /usr/local/bin/docker-compose
              ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose || true

              # placeholders for future steps
              mkdir -p /opt/airflow && chown -R ec2-user:ec2-user /opt/airflow
              echo "Docker installed. Place your docker-compose.yml under /opt/airflow" > /etc/motd
              EOF

  tags = merge(local.tags, { Name = "airflow-controller" })
}

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
