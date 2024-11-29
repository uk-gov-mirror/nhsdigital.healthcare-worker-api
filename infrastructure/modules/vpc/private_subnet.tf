resource "aws_subnet" "private" {
  count             = length(data.aws_availability_zones.available.names)
  vpc_id            = aws_vpc.lambda.id
  availability_zone = data.aws_availability_zones.available.names[count.index]
  cidr_block        = local.subnets_cidr_blocks[count.index + 3]

  tags = {
    Name    = "${var.env}-hcw-private-${data.aws_availability_zones.available.names[count.index]}"
    private = "True"
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.lambda.id

  tags = {
    Name = "${var.env}-hcw-private-rt"
  }
}

resource "aws_route_table_association" "private" {
  count          = length(data.aws_availability_zones.available.names)
  subnet_id      = element(aws_subnet.private.*.id, count.index)
  route_table_id = aws_route_table.private.id
}

resource "aws_route" "ldap_gateway" {
  route_table_id = aws_route_table.private.id

  transit_gateway_id     = var.transit_gateway_id
  destination_cidr_block = var.ldap_gateway_cidr_block
}
