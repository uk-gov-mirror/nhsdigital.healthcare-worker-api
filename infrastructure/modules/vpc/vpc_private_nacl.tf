resource "aws_network_acl" "hcw_private_acl" {
  vpc_id     = aws_vpc.lambda.id
  subnet_ids = aws_subnet.private.*.id
  tags = {
    Name = "${var.env}-hcw-private-acl"
  }
}

resource "aws_network_acl_rule" "private_to_all_http_out" {
  network_acl_id = aws_network_acl.hcw_private_acl.id
  rule_number    = 210
  rule_action    = "allow"
  egress         = true
  protocol       = "tcp"
  cidr_block     = "0.0.0.0/0"
  from_port      = 80
  to_port        = 80
}

resource "aws_network_acl_rule" "private_to_all_https_out" {
  network_acl_id = aws_network_acl.hcw_private_acl.id
  rule_number    = 211
  rule_action    = "allow"
  egress         = true
  protocol       = "tcp"
  cidr_block     = "0.0.0.0/0"
  from_port      = 443
  to_port        = 443
}

resource "aws_network_acl_rule" "private_to_all_ephemeral_in" {
  network_acl_id = aws_network_acl.hcw_private_acl.id
  rule_number    = 212
  rule_action    = "allow"
  egress         = false
  protocol       = "tcp"
  cidr_block     = "0.0.0.0/0"
  from_port      = 1024
  to_port        = 65535
}

resource "aws_network_acl_rule" "private_to_all_ephemeral_out" {
  network_acl_id = aws_network_acl.hcw_private_acl.id
  rule_number    = 213
  rule_action    = "allow"
  egress         = true
  protocol       = "tcp"
  cidr_block     = "0.0.0.0/0"
  from_port      = 1024
  to_port        = 65535
}

resource "aws_network_acl_rule" "private_https_in_from_vpc" {
  network_acl_id = aws_network_acl.hcw_private_acl.id
  rule_number    = 214
  rule_action    = "allow"
  egress         = false
  protocol       = "tcp"
  cidr_block     = var.vpc_cidr_block
  from_port      = 443
  to_port        = 443
}

resource "aws_network_acl_rule" "private_http_in_from_vpc" {
  network_acl_id = aws_network_acl.hcw_private_acl.id
  rule_number    = 215
  rule_action    = "allow"
  egress         = false
  protocol       = "tcp"
  cidr_block     = var.ldap_gateway_cidr_block
  from_port      = 80
  to_port        = 80
}

resource "aws_network_acl_rule" "private_ldaps_in_from_vpc" {
  network_acl_id = aws_network_acl.hcw_private_acl.id
  rule_number    = 100
  rule_action    = "allow"
  egress         = false
  protocol       = "tcp"
  cidr_block     = var.ldap_gateway_cidr_block
  from_port      = 636
  to_port        = 636
}

resource "aws_network_acl_rule" "vgw_http_route3_to_cia" {
  network_acl_id = aws_network_acl.hcw_private_acl.id
  rule_number    = 221
  rule_action    = "allow"
  egress         = true
  protocol       = "tcp"
  cidr_block     = var.ldap_gateway_cidr_block
  from_port      = 80
  to_port        = 80
}

resource "aws_network_acl_rule" "vgw_egr_route3_to_cia" {
  network_acl_id = aws_network_acl.hcw_private_acl.id
  rule_number    = 222
  rule_action    = "allow"
  egress         = true
  protocol       = "tcp"
  cidr_block     = var.ldap_gateway_cidr_block
  from_port      = 443
  to_port        = 443
}

resource "aws_network_acl_rule" "vgw_ldap_egr_route3_to_cia" {
  network_acl_id = aws_network_acl.hcw_private_acl.id
  rule_number    = 223
  rule_action    = "allow"
  egress         = true
  protocol       = "tcp"
  cidr_block     = var.ldap_gateway_cidr_block
  from_port      = 636
  to_port        = 636
}
