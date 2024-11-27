resource "aws_vpc" "nft_vpc" {
  cidr_block = "10.21.0.0/24"

  tags = {
    Name = "nft-vpc"
  }
}

resource "aws_subnet" "nft_subnet" {
  vpc_id     = aws_vpc.nft_vpc.id
  cidr_block = "10.21.0.0/26"
}

resource "aws_internet_gateway" "internet_gateway" {
  vpc_id = aws_vpc.nft_vpc.id
}

resource "aws_route_table" "nft_vpc_route" {
  vpc_id = aws_vpc.nft_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.internet_gateway.id
  }
}

resource "aws_route_table_association" "nft_route_association" {
  subnet_id      = aws_subnet.nft_subnet.id
  route_table_id = aws_route_table.nft_vpc_route.id
}

resource "aws_security_group" "nft_security_group" {
  vpc_id = aws_vpc.nft_vpc.id

  tags = {
    Name = "nft_security_group"
  }
}

resource "aws_vpc_security_group_ingress_rule" "allow_ssh" {
  security_group_id = aws_security_group.nft_security_group.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 22
  ip_protocol       = "tcp"
  to_port           = 22
}

resource "aws_vpc_security_group_egress_rule" "allow_https" {
  security_group_id = aws_security_group.nft_security_group.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  ip_protocol       = "tcp"
  to_port           = 443
}

resource "aws_network_acl" "nft_acl" {
  vpc_id = aws_vpc.nft_vpc.id

  ingress {
    protocol   = "tcp"
    rule_no    = 200
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 22
    to_port    = 22
  }

  egress {
    protocol   = "tcp"
    rule_no    = 200
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 22
    to_port    = 22
  }
}

resource "aws_iam_role" "nft_ec2_role" {
  name = "${var.env}-nft-ec2-role"
  path = "/"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_policy" "nft_ec2_role_policy" {
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "s3:*"
      Effect = "Allow"
      Resource = [
        aws_s3_bucket.nft_test_results.arn,
        "${aws_s3_bucket.nft_test_results.arn}/*"
      ]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "role_attachment" {
  role       = aws_iam_role.nft_ec2_role.name
  policy_arn = aws_iam_policy.nft_ec2_role_policy.arn
}

resource "aws_iam_instance_profile" "role_profile" {
  name = "${var.env}-nft-instance-profile"
  role = aws_iam_role.nft_ec2_role.name
}

resource "aws_s3_bucket" "nft_test_results" {
  bucket = "${var.env}-nft-test-results"

}

resource "aws_s3_bucket_public_access_block" "block_nft_public_access" {
  bucket = aws_s3_bucket.nft_test_results.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "nft_bucket_policy" {
  bucket = aws_s3_bucket.nft_test_results.bucket

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "HTTPSOnly"
        Effect = "Deny"
        Action = "s3:*"
        Principal = {
          AWS = "*"
        }
        Resource = [
          aws_s3_bucket.nft_test_results.arn,
          "${aws_s3_bucket.nft_test_results.arn}/*",
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

