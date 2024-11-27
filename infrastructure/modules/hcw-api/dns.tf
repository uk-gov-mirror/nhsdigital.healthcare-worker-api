data "aws_route53_zone" "zone" {
  name = "${var.subdomain}.healthcare-worker.care-identity-service2.nhs.uk"
}


