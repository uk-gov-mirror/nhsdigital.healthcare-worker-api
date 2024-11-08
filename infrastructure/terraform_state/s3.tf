resource "aws_s3_bucket" "state" {
  bucket = "nhse-iam-hcw-terraform-state"
}

resource "aws_s3_bucket_policy" "state_bucket_policy" {
  bucket = aws_s3_bucket.state.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyInsecureConnections"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource  = "${aws_s3_bucket.state.arn}/*"
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
      Resource = "${aws_s3_bucket.state.arn}/*"
      }, {
      Effect = "Allow"
      Principal = {
        AWS = [
          "arn:aws:iam::711387117641:root",
          "arn:aws:iam::535002889321:root"
        ]
      }
      Action   = ["s3:ListBucket", "s3:GetBucket*"]
      Resource = aws_s3_bucket.state.arn
    }]
  })
}
