resource "aws_subnet" "public" {
  count                   = length(data.aws_availability_zones.available.names)
  vpc_id                  = aws_vpc.lambda.id
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  cidr_block              = local.subnets_cidr_blocks[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name    = "${var.env}-hcw-public-${data.aws_availability_zones.available.names[count.index]}"
    private = "False"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.lambda.id

  tags = {
    Name = "${var.env}-hcw-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  count          = length(data.aws_availability_zones.available.names)
  subnet_id      = element(aws_subnet.public.*.id, count.index)
  route_table_id = aws_route_table.public.id
}
