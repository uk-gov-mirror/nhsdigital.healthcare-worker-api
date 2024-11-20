data "aws_s3_bucket" "app_deployment" {
  bucket = "nhse-iam-hcw-build-artifacts-mgmt"
}

data "aws_s3_object" "app_deployment_zip" {
  bucket = data.aws_s3_bucket.app_deployment.id
  key    = var.s3_filename
}

data "aws_secretsmanager_secret" "ldap_server_cert" {
  name = "ldap_server_cert"
}

data "aws_secretsmanager_secret" "mtls_client_key" {
  name = "mtls_client_key"
}

data "aws_secretsmanager_secret" "mtls_client_cert" {
  name = "mtls_client_cert"
}

data "aws_secretsmanager_secret" "ldap_password" {
  name = "ldap_password"
}

resource "aws_lambda_function" "hcw-app" {
  function_name = "hcw-app-${var.env}"
  role          = aws_iam_role.lambda_app_role.arn

  runtime = "python3.12"

  s3_bucket = data.aws_s3_bucket.app_deployment.id
  s3_key    = var.s3_filename
  handler   = "main.lambda_handler"
  timeout   = 30

  source_code_hash = data.aws_s3_object.app_deployment_zip.etag

  publish = true

  vpc_config {
    security_group_ids = [data.aws_security_group.security_group.id]
    subnet_ids         = data.aws_subnets.subnets.ids
  }

  environment {
    variables = {
      LDAP_SERVER_CERT_ID = data.aws_secretsmanager_secret.ldap_server_cert.arn
      MTLS_CLIENT_KEY_ID  = data.aws_secretsmanager_secret.mtls_client_key.arn
      MTLS_CLIENT_CERT_ID = data.aws_secretsmanager_secret.mtls_client_cert.arn
      LDAP_PASSWORD_ID    = data.aws_secretsmanager_secret.ldap_password.arn
      LDAP_USERNAME       = "uid=cim-identity-bind-account,ou=admins,o=nhs"
      LDAP_GATEWAY_URL    = var.ldap_gateway_url
    }
  }
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
          data.aws_secretsmanager_secret.ldap_server_cert.arn,
          data.aws_secretsmanager_secret.mtls_client_key.arn,
          data.aws_secretsmanager_secret.mtls_client_cert.arn,
          data.aws_secretsmanager_secret.ldap_password.arn
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
