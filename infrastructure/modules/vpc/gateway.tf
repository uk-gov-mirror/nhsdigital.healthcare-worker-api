# This is a setting on the API Gateway over the entire account. It allows us to log individual requests, although
# that's needs to be explicitly enabled on each gateway instance when we want to use it.
resource "aws_api_gateway_account" "gateway_account" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_global.arn
}

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["apigateway.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "api_gateway_global" {
  name               = "api_gateway_cloudwatch_global"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

data "aws_iam_policy_document" "cloudwatch" {
  statement {
    effect = "Allow"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams",
      "logs:PutLogEvents",
      "logs:GetLogEvents",
      "logs:FilterLogEvents",
    ]

    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "cloudwatch" {
  name   = "default"
  role   = aws_iam_role.api_gateway_global.id
  policy = data.aws_iam_policy_document.cloudwatch.json
}
