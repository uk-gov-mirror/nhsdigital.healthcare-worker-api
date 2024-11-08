output "apim_private_key_arn" {
  value = aws_secretsmanager_secret.apim_account_private_key.arn
}
