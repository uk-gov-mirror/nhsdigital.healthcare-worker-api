resource "aws_network_acl" "hcw_private_acl" {
  vpc_id     = aws_vpc.lambda.id
  subnet_ids = aws_subnet.private.*.id
  tags = {
    Name = "${var.env}-hcw-private-acl"
  }
}

# HTTPS inside VPC
resource "aws_network_acl_rule" "private_to_https_out" {
  network_acl_id = aws_network_acl.hcw_private_acl.id
  rule_number    = 100
  rule_action    = "allow"
  egress         = true
  protocol       = "tcp"
  cidr_block     = var.vpc_cidr_block
  from_port      = 443
  to_port        = 443
}

# Ephemeral ports
resource "aws_network_acl_rule" "private_to_ephemeral_out" {
  network_acl_id = aws_network_acl.hcw_private_acl.id
  rule_number    = 120
  rule_action    = "allow"
  egress         = true
  protocol       = "tcp"
  cidr_block     = var.vpc_cidr_block
  from_port      = 1024
  to_port        = 65535
}

# HTTPS in VPC
resource "aws_network_acl_rule" "private_https_in_from_vpc" {
  network_acl_id = aws_network_acl.hcw_private_acl.id
  rule_number    = 100
  rule_action    = "allow"
  egress         = false
  protocol       = "tcp"
  cidr_block     = var.vpc_cidr_block
  from_port      = 443
  to_port        = 443
}

# LDAPS from local
resource "aws_network_acl_rule" "private_ldaps_in_from_local" {
  network_acl_id = aws_network_acl.hcw_private_acl.id
  rule_number    = 110
  rule_action    = "allow"
  egress         = false
  protocol       = "tcp"
  cidr_block     = var.vpc_cidr_block
  from_port      = 636
  to_port        = 636
}
