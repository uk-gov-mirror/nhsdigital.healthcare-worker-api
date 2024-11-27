resource "aws_route53_zone" "hosted_zone" {
  name = "${var.subdomain}.healthcare-worker.care-identity-service2.nhs.uk"
}

resource "aws_s3_bucket" "truststore" {
  bucket = "hcw-truststore-${var.subdomain}"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "truststore_versioning" {
  bucket = aws_s3_bucket.truststore.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_policy" "build_artifacts_bucket_policy" {
  bucket = aws_s3_bucket.truststore.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureConnections"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource  = "${aws_s3_bucket.truststore.arn}/*"
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
    }]
  })
}

resource "aws_s3_bucket_public_access_block" "block_public_access" {
  bucket = aws_s3_bucket.truststore.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_api_gateway_domain_name" "domain" {
  domain_name              = aws_route53_zone.hosted_zone.name
  regional_certificate_arn = aws_acm_certificate_validation.cert_validation.certificate_arn

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  mutual_tls_authentication {
    truststore_uri = "s3://hcw-truststore-${var.subdomain}/gw_mtls_truststore.pem"
  }

  security_policy = "TLS_1_2"
}

resource "aws_route53_record" "gw_route" {
  zone_id = aws_route53_zone.hosted_zone.zone_id
  name    = aws_api_gateway_domain_name.domain.domain_name
  type    = "A"

  alias {
    evaluate_target_health = false
    name                   = aws_api_gateway_domain_name.domain.regional_domain_name
    zone_id                = aws_api_gateway_domain_name.domain.regional_zone_id
  }
}

resource "aws_acm_certificate" "cert" {
  domain_name       = aws_route53_zone.hosted_zone.name
  validation_method = "DNS"
}

resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.cert.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = aws_route53_zone.hosted_zone.zone_id
}

resource "aws_acm_certificate_validation" "cert_validation" {
  certificate_arn         = aws_acm_certificate.cert.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}
