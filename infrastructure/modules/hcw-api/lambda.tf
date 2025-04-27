data "aws_s3_bucket" "app_deployment" {
  bucket = "nhse-iam-hcw-build-artifacts-mgmt"
}

data "aws_s3_object" "app_deployment_zip" {
  bucket = data.aws_s3_bucket.app_deployment.id
  key    = var.s3_filename
}

data "aws_secretsmanager_secret" "ldap_credentials" {
  name = "ldap_credentials"
}

resource "aws_lambda_function" "hcw-app" {
  function_name = "hcw-app-${var.env}"
  role          = aws_iam_role.lambda_app_role.arn

  runtime = "python3.12"

  s3_bucket   = data.aws_s3_bucket.app_deployment.id
  s3_key      = var.s3_filename
  handler     = "main.lambda_handler"
  timeout     = 60
  memory_size = 128

  source_code_hash = data.aws_s3_object.app_deployment_zip.etag

  publish = true

  vpc_config {
    security_group_ids = [data.aws_security_group.security_group.id]
    subnet_ids         = data.aws_subnets.subnets.ids
  }

  environment {
    variables = {
      LDAP_CREDENTIALS_SECRET_ID = data.aws_secretsmanager_secret.ldap_credentials.arn
      LDAP_GATEWAY_URL           = var.ldap_gateway_url
      SANDBOX_MODE               = var.sandbox_mode
      BASE_URL                   = "https://${var.apim_environment}.api.service.nhs.uk/healthcare-worker"
    }
  }
}

resource "aws_lambda_provisioned_concurrency_config" "provisioned_capacity" {
  count = var.provisioned_capacity > 0 ? 1 : 0

  function_name                     = aws_lambda_function.hcw-app.function_name
  provisioned_concurrent_executions = var.provisioned_capacity
  qualifier                         = aws_lambda_alias.live.name
}

resource "aws_iam_role" "lambda_app_role" {
  name = "lambda-app-role-${var.env}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "lambda_app_policy" {
  name = "lambda-app-policy-${var.env}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:CreateNetworkInterface",
          "ec2:AttachNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface"
        ]
        Resource = "*"
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Resource" : "*"
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "secretsmanager:GetSecretValue"
        ],
        "Resource" : [
          data.aws_secretsmanager_secret.ldap_credentials.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_app_role_attach" {
  role       = aws_iam_role.lambda_app_role.name
  policy_arn = aws_iam_policy.lambda_app_policy.arn
}

resource "aws_lambda_alias" "live" {
  name             = "live"
  description      = "Currently live version for this environment"
  function_name    = aws_lambda_function.hcw-app.arn
  function_version = aws_lambda_function.hcw-app.version
}
