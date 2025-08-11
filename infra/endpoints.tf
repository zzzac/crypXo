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
