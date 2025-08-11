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

