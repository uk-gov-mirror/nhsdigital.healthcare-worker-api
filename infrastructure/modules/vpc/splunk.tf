// Saves hec token as secret for fetching by appropriate envs
resource "aws_secretsmanager_secret" "hec_token" {
  name = "hec_token"
}
