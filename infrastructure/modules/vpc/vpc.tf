locals {
  # This logic splits up the provided VPC CIDR block into subnet ranges. The subnets_cidr_blocks function inputs
  # define the size of the resulting subnet ranges based on the original prefix value.
  # So cidrsubnets(0.0.0.0/24, 2, 2, 2) results in three subnets of size /26
  # These locals work out the largest possible subnet size assuming that we want 2 subnets per AZ and for them all
  # to evenly sized.
  number_of_AZs               = length(data.aws_availability_zones.available.names)
  subnets_newbits_value       = ceil(log(local.number_of_AZs * 2, 2))
  subnets_newbits_list        = tolist([for az in range(local.number_of_AZs * 2) : local.subnets_newbits_value])
  subnets_cidr_blocks         = cidrsubnets(var.vpc_cidr_block, local.subnets_newbits_list...)
  vpc_processor_function_name = "${var.env}-vpc-flow-log-transformer"
}

resource "aws_vpc" "lambda" {
  enable_dns_support   = true
  enable_dns_hostnames = true
  cidr_block           = var.vpc_cidr_block
  tags = {
    Name = "${var.env}-vpc-lambda"
  }
}

resource "aws_cloudwatch_log_group" "vpc_flow_log" {
  name              = "${var.env}-vpc-flow-logs"
  retention_in_days = var.log_group_retention
  tags = {
    Name = "${var.env}-vpc-flow-logs"
  }
}

resource "aws_flow_log" "lambda_vpc" {
  log_destination      = aws_cloudwatch_log_group.vpc_flow_log.arn
  log_destination_type = "cloud-watch-logs"
  traffic_type         = "ALL"
  vpc_id               = aws_vpc.lambda.id
  iam_role_arn         = aws_iam_role.vpc_flow_log_cloudwatch.arn

  tags = {
    Name = "${var.env}-lambda-vpc-flow-logs"
  }
}

resource "aws_iam_role" "vpc_flow_log_cloudwatch" {
  name               = "${var.env}-vpc-flow-log-role"
  assume_role_policy = data.aws_iam_policy_document.flow_log_cloudwatch_assume_role.json

  tags = {
    Name = "${var.env}-vpc-flow-log-role"
  }
}

resource "aws_iam_role_policy" "vpc_flow_logs_policy" {
  name = "${var.env}-vpc-flow-logs-policy"
  role = aws_iam_role.vpc_flow_log_cloudwatch.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ]
      Resource = [
        aws_cloudwatch_log_group.vpc_flow_log.arn,
        "${aws_cloudwatch_log_group.vpc_flow_log.arn}:log-stream:*"
      ]
    }]
  })
}

resource "aws_vpc_endpoint" "vpc_lambda_to_secretsmanager" {
  vpc_id              = aws_vpc.lambda.id
  service_name        = "com.amazonaws.eu-west-2.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private.*.id
  security_group_ids  = [aws_security_group.endpoint.id]
  private_dns_enabled = true

  tags = {
    Name = "${var.env}-vpc-lambda-to-secretsmanager"
  }
}

data "aws_iam_policy_document" "flow_log_cloudwatch_assume_role" {
  statement {
    principals {
      type        = "Service"
      identifiers = ["vpc-flow-logs.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_ec2_transit_gateway_vpc_attachment" "vpn_transit_gateway_attachment" {
  subnet_ids         = aws_subnet.private.*.id
  transit_gateway_id = var.transit_gateway_id
  vpc_id             = aws_vpc.lambda.id
}

resource "aws_secretsmanager_secret" "ldap_credentials" {
  name = "ldap_credentials"
}
