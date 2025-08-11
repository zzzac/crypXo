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
