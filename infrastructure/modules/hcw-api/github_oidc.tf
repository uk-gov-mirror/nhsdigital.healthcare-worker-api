# GitHub Actions OIDC - allows the "Publish Spec to UAT" workflow to assume a role
# and read the proxygen private key from Secrets Manager.
# Only created in ft (dev account) since UAT publishing is done from there.

resource "aws_iam_openid_connect_provider" "github_actions" {
  count = var.env == "ft" ? 1 : 0

  url = "https://token.actions.githubusercontent.com"

  client_id_list = ["sts.amazonaws.com"]

  # GitHub's OIDC thumbprint - this is a well-known value
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

resource "aws_iam_role" "github_actions_publish_spec" {
  count = var.env == "ft" ? 1 : 0

  name = "GitHubActionsPublishSpecRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github_actions[0].arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:NHSDigital/healthcare-worker-api:*"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "github_actions_read_proxygen_key" {
  count = var.env == "ft" ? 1 : 0

  name = "ReadProxygenPrivateKey"
  role = aws_iam_role.github_actions_publish_spec[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          data.aws_secretsmanager_secret.apim_account_private_key.arn,
          "arn:aws:secretsmanager:eu-west-2:${var.account_id}:secret:apim-spec-publish-private-key*"
        ]
      }
    ]
  })
}
