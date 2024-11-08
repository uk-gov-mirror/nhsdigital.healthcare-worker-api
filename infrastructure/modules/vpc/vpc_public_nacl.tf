resource "aws_network_acl" "hcw_public_acl" {
  vpc_id     = aws_vpc.lambda.id
  subnet_ids = aws_subnet.public.*.id
  tags = {
    Name = "${var.env}-hcw-public-acl"
  }
}


resource "aws_network_acl_rule" "public_acl_ephemeral_all_in" {
  network_acl_id = aws_network_acl.hcw_public_acl.id
  rule_number    = 101
  rule_action    = "allow"
  egress         = false
  protocol       = "tcp"
  cidr_block     = "0.0.0.0/0"
  from_port      = 1024
  to_port        = 65535
}

resource "aws_network_acl_rule" "public_acl_http_all_out" {
  network_acl_id = aws_network_acl.hcw_public_acl.id
  rule_number    = 101
  rule_action    = "allow"
  egress         = true
  protocol       = "tcp"
  cidr_block     = "0.0.0.0/0"
  from_port      = 80
  to_port        = 80
}

resource "aws_network_acl_rule" "public_acl_https_in_out" {
  network_acl_id = aws_network_acl.hcw_public_acl.id
  rule_number    = 103
  rule_action    = "allow"
  egress         = true
  protocol       = "tcp"
  cidr_block     = "0.0.0.0/0"
  from_port      = 443
  to_port        = 443
}

resource "aws_network_acl_rule" "public_acl_https_in_from_vpc" {
  network_acl_id = aws_network_acl.hcw_public_acl.id
  rule_number    = 104
  rule_action    = "allow"
  egress         = false
  protocol       = "tcp"
  cidr_block     = var.vpc_cidr_block
  from_port      = 443
  to_port        = 443
}

resource "aws_network_acl_rule" "public_acl_http_in_from_vpc" {
  network_acl_id = aws_network_acl.hcw_public_acl.id
  rule_number    = 106
  rule_action    = "allow"
  egress         = false
  protocol       = "tcp"
  cidr_block     = var.vpc_cidr_block
  from_port      = 80
  to_port        = 80
}
