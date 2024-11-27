resource "aws_ec2_transit_gateway" "transit_gateway" {
  tags = {
    Name = "cim_vpn_transit_gateway"
  }
}

resource "aws_customer_gateway" "hcw_customer_gateway_south" {
  bgp_asn    = var.bgp_asn
  ip_address = "20.49.131.117"
  type       = "ipsec.1"

  tags = {
    "Name" = "hcw-cis2-customer-gateway-south"
  }
}

resource "aws_customer_gateway" "hcw_customer_gateway_west" {
  bgp_asn    = var.bgp_asn
  ip_address = "20.49.132.44"
  type       = "ipsec.1"

  tags = {
    "Name" = "hcw-cis2-customer-gateway-west"
  }
}

resource "aws_cloudwatch_log_group" "west_tunnel1_log_group" {
  name = "vpn_west_tunnel1"
}

resource "aws_cloudwatch_log_group" "west_tunnel2_log_group" {
  name = "vpn_west_tunnel2"
}

resource "aws_cloudwatch_log_group" "south_tunnel1_log_group" {
  name = "vpn_south_tunnel1"
}

resource "aws_cloudwatch_log_group" "south_tunnel2_log_group" {
  name = "vpn_south_tunnel2"
}

resource "aws_vpn_connection" "hcw_vpn_connection_south" {
  customer_gateway_id = aws_customer_gateway.hcw_customer_gateway_south.id
  transit_gateway_id  = aws_ec2_transit_gateway.transit_gateway.id
  type                = "ipsec.1"

  tunnel1_inside_cidr        = "169.254.21.32/30"
  tunnel2_inside_cidr        = "169.254.22.32/30"
  tunnel1_startup_action     = "start"
  tunnel2_startup_action     = "start"
  tunnel1_dpd_timeout_action = "clear"
  tunnel2_dpd_timeout_action = "clear"

  tunnel1_log_options {
    cloudwatch_log_options {
      log_enabled       = true
      log_group_arn     = aws_cloudwatch_log_group.south_tunnel1_log_group.arn
      log_output_format = "json"
    }
  }

  tunnel2_log_options {
    cloudwatch_log_options {
      log_enabled       = true
      log_group_arn     = aws_cloudwatch_log_group.south_tunnel2_log_group.arn
      log_output_format = "json"
    }
  }

  tags = {
    "Name" = "hcw-cis2-vpn-connection-south"
  }
}

resource "aws_vpn_connection" "hcw_vpn_connection_west" {
  customer_gateway_id = aws_customer_gateway.hcw_customer_gateway_west.id
  transit_gateway_id  = aws_ec2_transit_gateway.transit_gateway.id
  type                = "ipsec.1"

  tunnel1_inside_cidr        = "169.254.21.36/30"
  tunnel2_inside_cidr        = "169.254.22.36/30"
  tunnel1_startup_action     = "start"
  tunnel2_startup_action     = "start"
  tunnel1_dpd_timeout_action = "clear"
  tunnel2_dpd_timeout_action = "clear"

  tunnel1_log_options {
    cloudwatch_log_options {
      log_enabled       = true
      log_group_arn     = aws_cloudwatch_log_group.west_tunnel1_log_group.arn
      log_output_format = "json"
    }
  }

  tunnel2_log_options {
    cloudwatch_log_options {
      log_enabled       = true
      log_group_arn     = aws_cloudwatch_log_group.west_tunnel2_log_group.arn
      log_output_format = "json"
    }
  }

  tags = {
    "Name" = "hcw-cis2-vpn-connection-west"
  }
}

resource "aws_ram_resource_share" "resource_share" {
  name = "share-transit-gateway"
}

resource "aws_ram_resource_association" "share_transit_gateway" {
  resource_arn       = aws_ec2_transit_gateway.transit_gateway.arn
  resource_share_arn = aws_ram_resource_share.resource_share.id
}

resource "aws_ram_principal_association" "dev_account" {
  principal          = "535002889321"
  resource_share_arn = aws_ram_resource_share.resource_share.id
}

resource "aws_ram_principal_association" "int_account" {
  principal          = "711387117641"
  resource_share_arn = aws_ram_resource_share.resource_share.id
}

resource "aws_ram_principal_association" "prod_account" {
  principal          = "266735814611"
  resource_share_arn = aws_ram_resource_share.resource_share.id
}
