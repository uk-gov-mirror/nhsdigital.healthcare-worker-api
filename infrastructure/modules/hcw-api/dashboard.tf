resource "aws_cloudwatch_dashboard" "env_dashboard" {
  dashboard_name = "${var.env}-dashboard"
  dashboard_body = templatefile("${path.module}/dashboard.json", {
    env = var.env
  })
}
