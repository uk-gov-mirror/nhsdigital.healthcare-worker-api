resource "aws_s3_bucket" "build_artifacts" {
  bucket = "nhse-iam-hcw-build-artifacts-${var.account}"
}

resource "aws_s3_bucket_versioning" "build_artifacts_versioning" {
  bucket = aws_s3_bucket.build_artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_policy" "build_artifacts_bucket_policy" {
  bucket = aws_s3_bucket.build_artifacts.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyInsecureConnections"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource  = "${aws_s3_bucket.build_artifacts.arn}/*"
      Condition = {
        Bool = {
          "aws:SecureTransport" = "false"
        }
      }
      }, {
      Effect = "Allow"
      Principal = {
        AWS = [
          "arn:aws:iam::711387117641:root",
          "arn:aws:iam::535002889321:root"
        ]
      }
      Action   = ["s3:Get*", "s3:Put*"]
      Resource = "${aws_s3_bucket.build_artifacts.arn}/*"
      }, {
      Effect = "Allow"
      Principal = {
        AWS = [
          "arn:aws:iam::711387117641:root",
          "arn:aws:iam::535002889321:root"
        ]
      }
      Action   = "s3:ListBucket"
      Resource = aws_s3_bucket.build_artifacts.arn
    }]
  })
}
