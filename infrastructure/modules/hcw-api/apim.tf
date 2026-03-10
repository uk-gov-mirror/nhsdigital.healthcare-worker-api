data "aws_secretsmanager_secret" "apim_account_private_key" {
  name = "apim-deploy-private-key"
}

locals {
  api_gateway_domain = "${var.subdomain}.healthcare-worker.care-identity-service2.nhs.uk"
  # Use raw API Gateway URL when no custom domain (empty subdomain)
  api_gateway_url = var.subdomain != "" ? (
    var.is_pr ? "https://${local.api_gateway_domain}/${var.env}" : "https://${local.api_gateway_domain}"
  ) : aws_api_gateway_stage.live.invoke_url
}

resource "null_resource" "apim_instance_deploy" {
  triggers = {
    # Hash all files under specification/ so that changes to example files also trigger redeployment.
    spec             = sha1(join("", [for f in sort(fileset("${path.root}/../specification", "**")) : sha1(file("${path.root}/../specification/${f}"))]))
    build_script     = sha1(file("${path.module}/apim_instance_deploy.sh"))
    env              = var.env
    apim_environment = var.apim_environment
    key_arn          = data.aws_secretsmanager_secret.apim_account_private_key.arn
    key              = data.aws_secretsmanager_secret.apim_account_private_key.last_changed_date
    api_gateway_url  = local.api_gateway_url
  }

  provisioner "local-exec" {
    command = "${path.module}/apim_instance_deploy.sh ${var.env} ${var.apim_environment} ${data.aws_secretsmanager_secret.apim_account_private_key.arn} ${local.api_gateway_url}"
  }
}
