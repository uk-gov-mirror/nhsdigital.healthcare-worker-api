output "subnet_ids" {
  value = aws_subnet.private.*.id
}

output "security_group_id" {
  value = aws_security_group.vpc_lambda.id
}

output "hec_token_secret_id" {
  value = aws_secretsmanager_secret.hec_token.id
}
output "acm_certificate" {
  value = {
    cert = {
      arn                       = aws_acm_certificate.cert.arn
      domain_name               = aws_acm_certificate.cert.domain_name
      domain_validation_options = aws_acm_certificate.cert.domain_validation_options
    }
  }
}
