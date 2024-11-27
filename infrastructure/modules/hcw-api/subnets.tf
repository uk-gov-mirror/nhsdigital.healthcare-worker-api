data "aws_vpc" "vpc" {
  tags = {
    Name = "${var.vpc_env}-vpc-lambda"
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
  name   = "${var.vpc_env}-vpc-lambda-sg"
}
