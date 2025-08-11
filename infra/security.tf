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

