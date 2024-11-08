locals {
  vpc_env = var.is_pr ? "ft" : var.env
}

data "aws_vpc" "vpc" {
  tags = {
    Name = "${local.vpc_env}-vpc-lambda"
  }
}

data "aws_subnets" "subnets" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.vpc.id]
  }

  tags = {
    private = "True"
  }
}

data "aws_security_group" "security_group" {
  vpc_id = data.aws_vpc.vpc.id
  name   = "ft-vpc-lambda-sg"
}
