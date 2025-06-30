resource "aws_iam_role" "api_gateway_proxy_role" {
  name = "api-gateway-proxy-role-${var.env}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_policy" "api_gateway_proxy_policy" {
  name = "api-gateway-proxy-policy-${var.env}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "lambda:InvokeFunction"
        Resource = [
          aws_lambda_function.hcw-app.arn,
          "${aws_lambda_function.hcw-app.arn}:*"
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        "Resource" : "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "api_gateway_proxy_policy_attach" {
  role       = aws_iam_role.api_gateway_proxy_role.name
  policy_arn = aws_iam_policy.api_gateway_proxy_policy.arn
}

resource "aws_api_gateway_rest_api" "app_api" {
  name = "hcw-api-${var.env}"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  disable_execute_api_endpoint = true
}

resource "aws_api_gateway_method" "root_get" {
  authorization = "NONE"
  http_method   = "GET"
  resource_id   = aws_api_gateway_rest_api.app_api.root_resource_id
  rest_api_id   = aws_api_gateway_rest_api.app_api.id
}

resource "aws_api_gateway_integration" "root_get_lambda_integration" {
  http_method = aws_api_gateway_method.root_get.http_method
  resource_id = aws_api_gateway_rest_api.app_api.root_resource_id
  rest_api_id = aws_api_gateway_rest_api.app_api.id

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_alias.live.invoke_arn
}

resource "aws_api_gateway_resource" "practitioner" {
  parent_id   = aws_api_gateway_rest_api.app_api.root_resource_id
  path_part   = "Practitioner"
  rest_api_id = aws_api_gateway_rest_api.app_api.id
}

resource "aws_api_gateway_method" "practitioner_get" {
  authorization = "NONE"
  http_method   = "GET"
  resource_id   = aws_api_gateway_resource.practitioner.id
  rest_api_id   = aws_api_gateway_rest_api.app_api.id
}

resource "aws_api_gateway_integration" "practitioner_get_lambda_integration" {
  http_method = aws_api_gateway_method.practitioner_get.http_method
  resource_id = aws_api_gateway_resource.practitioner.id
  rest_api_id = aws_api_gateway_rest_api.app_api.id

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_alias.live.invoke_arn
}

resource "aws_api_gateway_resource" "practitioner_role" {
  parent_id   = aws_api_gateway_rest_api.app_api.root_resource_id
  path_part   = "PractitionerRole"
  rest_api_id = aws_api_gateway_rest_api.app_api.id
}

resource "aws_api_gateway_method" "practitioner_role_get" {
  authorization = "NONE"
  http_method   = "GET"
  resource_id   = aws_api_gateway_resource.practitioner_role.id
  rest_api_id   = aws_api_gateway_rest_api.app_api.id
}

resource "aws_api_gateway_integration" "practitioner_role_get_lambda_integration" {
  http_method = aws_api_gateway_method.practitioner_role_get.http_method
  resource_id = aws_api_gateway_resource.practitioner_role.id
  rest_api_id = aws_api_gateway_rest_api.app_api.id

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_alias.live.invoke_arn
}

resource "aws_api_gateway_method_settings" "api_settings" {
  rest_api_id = aws_api_gateway_rest_api.app_api.id
  stage_name  = aws_api_gateway_stage.live.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled = true
    logging_level   = "INFO"
  }
}

resource "aws_api_gateway_deployment" "live" {
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.practitioner,
      aws_api_gateway_method.practitioner_get,
      aws_api_gateway_method.practitioner_role_get,
      aws_api_gateway_method.root_get,
      aws_api_gateway_integration.practitioner_get_lambda_integration
    ]))
  }
  rest_api_id = aws_api_gateway_rest_api.app_api.id

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "live" {
  deployment_id = aws_api_gateway_deployment.live.id
  rest_api_id   = aws_api_gateway_rest_api.app_api.id
  stage_name    = "live"

  access_log_settings {
    destination_arn = "arn:aws:logs:eu-west-2:${var.account_id}:log-group:/API-Gateway-Access-Logs_${aws_api_gateway_rest_api.app_api.id}/live"
    format          = "{ \"requestId\":\"$context.requestId\", \"extendedRequestId\":\"$context.extendedRequestId\",\"ip\": \"$context.identity.sourceIp\", \"caller\":\"$context.identity.caller\", \"user\":\"$context.identity.user\", \"requestTime\":\"$context.requestTime\", \"httpMethod\":\"$context.httpMethod\", \"resourcePath\":\"$context.resourcePath\", \"status\":\"$context.status\", \"protocol\":\"$context.protocol\", \"responseLength\":\"$context.responseLength\" }"
  }
}

resource "aws_lambda_permission" "apigw_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.hcw-app.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_api_gateway_rest_api.app_api.execution_arn}/*/*/*"
  qualifier  = aws_lambda_alias.live.name
}

resource "aws_cloudwatch_log_group" "gateway_log_group" {
  name = "API-Gateway-Execution-Logs_${aws_api_gateway_rest_api.app_api.id}/${aws_api_gateway_stage.live.stage_name}"
}

resource "aws_api_gateway_base_path_mapping" "domain_name_mapping" {
  count = var.subdomain != "" ? 1 : 0

  api_id      = aws_api_gateway_rest_api.app_api.id
  stage_name  = aws_api_gateway_stage.live.stage_name
  domain_name = local.api_gateway_domain
  base_path   = var.is_pr ? var.env : ""
}
