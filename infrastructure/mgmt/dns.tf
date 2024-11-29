resource "aws_route53_zone" "hosted_zone" {
  name = "healthcare-worker.care-identity-service2.nhs.uk"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_route53_record" "dev" {
  zone_id = aws_route53_zone.hosted_zone.zone_id
  name    = "dev.healthcare-worker.care-identity-service2.nhs.uk"
  type    = "NS"
  ttl     = "30"
  records = ["ns-1858.awsdns-40.co.uk.", "ns-638.awsdns-15.net.", "ns-428.awsdns-53.com.", "ns-1345.awsdns-40.org."]
}
