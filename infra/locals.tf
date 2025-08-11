# locals.tf
locals {
  name_prefix = var.project
  tags = {
    Project = var.project
    Owner   = "${var.project}-platform"
    Stack   = "infra-minimal"
  }
}
