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

