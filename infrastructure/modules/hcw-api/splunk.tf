data "aws_secretsmanager_secret_version" "hec_token_current" {
  secret_id = var.hec_token_secret_id
}

resource "aws_kms_key" "encryption_key" {
  enable_key_rotation = true
}

resource "aws_s3_bucket" "failed_logs_bucket" {
  bucket = "nhse-iam-hcw-failed-logs-${var.env}"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "failed_logs_bucket_encryption" {
  bucket = aws_s3_bucket.failed_logs_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.encryption_key.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_versioning" "failed_logs_versioning" {
  bucket = aws_s3_bucket.failed_logs_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "failed_logs_access_block" {
  bucket = aws_s3_bucket.failed_logs_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "failed_logs_bucket_policy" {
  bucket = aws_s3_bucket.failed_logs_bucket.id

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "failed-logs-bucket-policy"
    Statement = [
      {
        Sid    = "HTTPSOnly"
        Effect = "Deny"
        Principal = {
          "AWS" : "*"
        }
        Action = "s3:*"
        Resource = [
          aws_s3_bucket.failed_logs_bucket.arn,
          "${aws_s3_bucket.failed_logs_bucket.arn}/*",
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      },
    ]
  })
}

resource "aws_iam_role" "firehose_role" {
  name = "firehose-role-${var.env}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Principal = {
        Service = "firehose.amazonaws.com"
      },
      Action = "sts:AssumeRole",
      Effect = "Allow"
    }]
  })
}

resource "aws_iam_policy" "firehose_policy" {
  name = "firehose-policy-${var.env}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow",
      Action = [
        "s3:AbortMultipartUpload",
        "s3:GetBucketLocation",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:ListBucketMultipartUploads",
        "s3:PutObject"
      ],
      Resource = ["${aws_s3_bucket.failed_logs_bucket.arn}/*", aws_s3_bucket.failed_logs_bucket.arn]
      }, {
      Effect   = "Allow"
      Action   = "logs:PutLogEvents"
      Resource = ["arn:aws:logs:eu-west-2:${var.account_id}:log-group:/aws/kinesisfirehose/logs-firehose-stream-${var.env}:log-stream:*"]
      }, {
      Effect = "Allow",
      Action = [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:DescribeKey"
      ],
      Resource = "*"
      }, {
      Effect   = "Allow"
      Action   = ["lambda:InvokeFunction", "lambda:GetFunctionConfiguration"]
      Resource = "${aws_lambda_function.log_transformer.arn}:$LATEST"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "firehose_policy_attachment" {
  role       = aws_iam_role.firehose_role.name
  policy_arn = aws_iam_policy.firehose_policy.arn
}

resource "aws_kinesis_firehose_delivery_stream" "splunk_logs_delivery" {
  name        = "logs-firehose-stream-${var.env}"
  destination = "splunk"

  splunk_configuration {
    hec_endpoint               = "https://hec.splunk.aws.digital.nhs.uk/services/collector/raw"
    hec_token                  = data.aws_secretsmanager_secret_version.hec_token_current.secret_string
    hec_acknowledgment_timeout = 600
    hec_endpoint_type          = "Raw"
    s3_backup_mode             = "FailedEventsOnly"

    s3_configuration {
      bucket_arn         = aws_s3_bucket.failed_logs_bucket.arn
      role_arn           = aws_iam_role.firehose_role.arn
      buffering_size     = 10
      buffering_interval = 400
      compression_format = "UNCOMPRESSED"
    }

    processing_configuration {
      enabled = "true"

      processors {
        type = "Lambda"

        parameters {
          parameter_name  = "LambdaArn"
          parameter_value = "${aws_lambda_function.log_transformer.arn}:$LATEST"
        }

        parameters {
          parameter_name  = "RoleArn"
          parameter_value = aws_iam_role.log_transformer_role.arn
        }
      }
    }
  }
}

resource "aws_iam_role" "cloudwatch_deliver_logs_role" {
  name = "firehose-deliver-role-${var.env}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Principal = {
        Service = "logs.amazonaws.com"
      },
      Action = "sts:AssumeRole",
      Effect = "Allow"
    }]
  })
}

resource "aws_iam_policy" "cloudwatch_deliver_logs_policy" {
  name = "firehose-deliver-policy-${var.env}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow",
      Action = "firehose:PutRecord",
      Resource = [
        aws_kinesis_firehose_delivery_stream.splunk_logs_delivery.arn,
        "${aws_kinesis_firehose_delivery_stream.splunk_logs_delivery.arn}/*"
      ]
      }, {
      Effect = "Allow",
      Action = [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:DescribeKey"
      ],
      Resource = aws_kms_key.encryption_key.arn
    }]
  })
}

resource "aws_iam_role_policy_attachment" "cloudwatch_deliver_logs_attachment" {
  role       = aws_iam_role.cloudwatch_deliver_logs_role.name
  policy_arn = aws_iam_policy.cloudwatch_deliver_logs_policy.arn
}

resource "aws_cloudwatch_log_subscription_filter" "cloudwatch_log_filter" {
  name            = "cloudwatch-log-filter-${var.env}"
  role_arn        = aws_iam_role.cloudwatch_deliver_logs_role.arn
  destination_arn = aws_kinesis_firehose_delivery_stream.splunk_logs_delivery.arn
  log_group_name  = "/aws/lambda/hcw-app-${var.env}"
  filter_pattern  = ""

  depends_on = [aws_lambda_function.hcw-app]
}

data "archive_file" "splunk_transform" {
  type        = "zip"
  source_file = "${path.module}/splunk_transform_lambda.py"
  output_path = "${path.module}/splunk_transform_lambda.zip"
}

resource "aws_lambda_function" "log_transformer" {
  function_name = "log-transformer-${var.env}"
  role          = aws_iam_role.log_transformer_role.arn

  runtime = "python3.12"
  handler = "splunk_transform_lambda.lambda_handler"

  filename         = "${path.module}/splunk_transform_lambda.zip"
  source_code_hash = data.archive_file.splunk_transform.output_sha512

  timeout = "600"

  depends_on = [aws_cloudwatch_log_group.log_transformer_log_group]
}

resource "aws_cloudwatch_log_group" "log_transformer_log_group" {
  name              = "/aws/lambda/log-transformer-${var.env}"
  retention_in_days = var.log_group_retention
}

resource "aws_iam_role" "log_transformer_role" {
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Principal = {
        Service = ["lambda.amazonaws.com", "firehose.amazonaws.com"]
      },
      Action = "sts:AssumeRole",
      Effect = "Allow"
    }]
  })
}

resource "aws_iam_policy" "log_transformer_policy" {
  name = "lambda-transform-policy-${var.env}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "arn:aws:logs:eu-west-2:${var.account_id}:log-group:/aws/lambda/log-transformer-${var.env}:*"
      },
      {
        Effect   = "Allow"
        Action   = ["lambda:InvokeFunction", "lambda:GetFunctionConfiguration"]
        Resource = "${aws_lambda_function.log_transformer.arn}:$LATEST"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "log_transformer_policy_attach" {
  role       = aws_iam_role.log_transformer_role.name
  policy_arn = aws_iam_policy.log_transformer_policy.arn
}

resource "aws_s3_bucket_logging" "failed_logs_bucket_logging" {
  bucket        = aws_s3_bucket.failed_logs_bucket.id
  target_bucket = var.access_logs_bucket_id
  target_prefix = "access-logs/"
}
