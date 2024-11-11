resource "aws_cloudwatch_dashboard" "env_dashboard" {
  dashboard_name = "${var.env}-dashboard"

  dashboard_body = jsonencode({
    "variables" : [],
    "widgets" : [
      {
        "height" : 6,
        "width" : 6,
        "y" : 6,
        "x" : 0,
        "type" : "metric",
        "properties" : {
          "view" : "timeSeries",
          "stacked" : false,
          "metrics" : [
            ["AWS/ApiGateway", "Latency", "ApiName", "hcw-api-${var.env}", "Stage", "live"]
          ],
          "region" : "eu-west-2"
          "title" : "Request Latency"
        }
      },
      {
        "height" : 6,
        "width" : 6,
        "y" : 0,
        "x" : 0,
        "type" : "metric",
        "properties" : {
          "metrics" : [
            ["AWS/ApiGateway", "Count", "ApiName", "hcw-api-${var.env}", "Stage", "live", { region : "eu-west-2" }]
          ],
          "view" : "timeSeries",
          "stacked" : false,
          "region" : "eu-west-2",
          "period" : 300,
          "stat" : "Sum",
          "title" : "Requests"
        }
      },
      {
        "height" : 6,
        "width" : 6,
        "y" : 6,
        "x" : 6,
        "type" : "metric",
        "properties" : {
          "metrics" : [
            ["AWS/ApiGateway", "Count", "ApiName", "hcw-api-${var.env}", "Resource", "/Worker", "Stage", "live", "Method", "GET", { region : "eu-west-2" }],
            ["...", "/Practitioner", ".", ".", ".", ".", { region : "eu-west-2" }]
          ],
          "view" : "pie",
          "region" : "eu-west-2",
          "period" : 300,
          "stat" : "Sum",
          "title" : "Endpoints"
        }
      },
      {
        "height" : 6,
        "width" : 6,
        "y" : 0,
        "x" : 6,
        "type" : "metric",
        "properties" : {
          "metrics" : [
            [{ expression : "m1-m2-m3", label : "Successful Requests", id : "e1", region : "eu-west-2" }],
            ["AWS/ApiGateway", "Count", "ApiName", "hcw-api-${var.env}", "Stage", "live", { region : "eu-west-2", id : "m1", visible : false }],
            [".", "5XXError", ".", ".", ".", ".", { region : "eu-west-2", id : "m2" }],
            [".", "4XXError", ".", ".", ".", ".", { region : "eu-west-2", id : "m3" }]
          ],
          "view" : "pie",
          "region" : "eu-west-2",
          "period" : 300,
          "stat" : "Sum",
          "title" : "Request Response Success"
        }
      },
      {
        "height" : 4,
        "width" : 6,
        "y" : 0,
        "x" : 12,
        "type" : "metric",
        "properties" : {
          "metrics" : [
            ["AWS/ApiGateway", "Count", "ApiName", "hcw-api-${var.env}", "Stage", "live", { region : "eu-west-2" }]
          ],
          "sparkline" : true,
          "view" : "singleValue",
          "region" : "eu-west-2",
          "period" : 300,
          "stat" : "Sum"
          "title" : "Request Count"
        }
      },
      {
        "height" : 6,
        "width" : 6,
        "y" : 4,
        "x" : 12,
        "type" : "metric",
        "properties" : {
          "metrics" : [
            ["AWS/CodeBuild", "FailedBuilds", "ProjectName", "hcw-api-deploy", { region : "eu-west-2" }],
            [".", "Builds", ".", ".", { region : "eu-west-2" }]
          ],
          "view" : "timeSeries",
          "stacked" : false,
          "region" : "eu-west-2",
          "period" : 300,
          "stat" : "Sum",
          "title" : "Deployments"
        }
      },
      {
        "height" : 6,
        "width" : 12,
        "y" : 12,
        "x" : 0,
        "type" : "metric",
        "properties" : {
          "metrics" : [
            ["AWS/ApiGateway", "Count", "ApiName", "hcw-api-${var.env}", { region : "eu-west-2" }],
            [".", "Latency", ".", ".", { region : "eu-west-2", stat : "Average" }],
            [".", "4XXError", ".", ".", { region : "eu-west-2" }],
            [".", "5XXError", ".", ".", { region : "eu-west-2" }]
          ],
          "sparkline" : false,
          "view" : "table",
          "region" : "eu-west-2",
          "period" : 300,
          "stat" : "Sum"
          "title" : "Request Info"
        }
      },
      {
        "height" : 6,
        "width" : 24,
        "y" : 18,
        "x" : 0,
        "type" : "log",
        "properties" : {
          "query" : "SOURCE '/aws/lambda/hcw-app-${var.env}' | fields @timestamp, @message, @logStream, @log\n| filter @message like \"[ERROR]\"\n| sort @timestamp desc\n| limit 10000",
          "region" : "eu-west-2",
          "stacked" : false,
          "view" : "table"
        }
      }
    ]
  })
}
