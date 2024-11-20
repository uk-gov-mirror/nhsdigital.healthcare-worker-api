resource "aws_default_security_group" "default" {
  vpc_id = aws_vpc.lambda.id
}

resource "aws_security_group" "vpc_lambda" {
  name        = "${var.env}-vpc-lambda-sg"
  description = "security group for lambda inside the vpc"
  vpc_id      = aws_vpc.lambda.id

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr_block]
    description = "HTTPS API calls including AWS"
  }

  egress {
    from_port   = 636
    to_port     = 636
    protocol    = "tcp"
    cidr_blocks = [var.ldap_gateway_cidr_block]
    description = "LDAPS calls over VPN"
  }

  tags = {
    Name = "${var.env}-vpc-lambda-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "internet_access" {
  name        = "${var.env}-internet-access-sg"
  description = "security group for outbound access to the internet"
  vpc_id      = aws_vpc.lambda.id

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.env}-internet-access-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "endpoint" {
  name        = "${var.env}-vpc-endpoints-sg"
  description = "security group for the secretsmanager vpc endpoint inside the vpc"
  vpc_id      = aws_vpc.lambda.id

  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.vpc_lambda.id]
  }

  tags = {
    Name = "${var.env}-vpc-endpoints-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}
