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

  tags = {
    Name = "${var.env}-vpc-lambda-sg"
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

resource "aws_security_group" "ldap_endpoint" {
  name        = "${var.env}-vpc-ldap-endpoint-sg"
  description = "security group for the ldap vpc endpoint inside the vpc"
  vpc_id      = aws_vpc.lambda.id

  egress {
    from_port   = 636
    to_port     = 636
    protocol    = "tcp"
    security_groups = [aws_security_group.vpc_lambda.id]
    description = "LDAPS calls to SDS"
  }

  tags = {
    Name = "${var.env}-vpc-ldap-endpoint-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}
