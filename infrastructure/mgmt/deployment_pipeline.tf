resource "aws_iam_role" "app_deployment_pipeline_role" {
  name = "DeploymentPipelineRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "codepipeline.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_policy" "codepipeline_policy" {
  name = "codepipeline_policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        "Effect" : "Allow",
        "Action" : ["codebuild:BatchGetBuilds", "codebuild:StartBuild"],
        "Resource" : "*"
      },
      {
        "Effect" : "Allow",
        "Action" : ["s3:PutObject", "s3:GetObject"],
        "Resource" : [
          aws_s3_bucket.build_artifacts.arn,
          "${aws_s3_bucket.build_artifacts.arn}/*"
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "codestar-connections:GetConnectionToken",
          "codestar-connections:GetConnection",
          "codeconnections:GetConnectionToken",
          "codeconnections:GetConnection",
          "codeconnections:UseConnection",
          "codestar-connections:UseConnection"
        ],
        "Resource" : [
          data.aws_codestarconnections_connection.github_connection.arn
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : "sts:AssumeRole",
        "Resource" : [
          "arn:aws:iam::711387117641:role/CodeBuildDeployJobRole",
          "arn:aws:iam::535002889321:role/CodeBuildDeployJobRole"
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "kms:DescribeKey",
          "kms:GenerateDataKey*",
          "kms:Encrypt",
          "kms:ReEncrypt*",
          "kms:Decrypt"
        ],
        "Resource" : aws_kms_key.kms_key.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "codepipeline_attach_policy" {
  role       = aws_iam_role.app_deployment_pipeline_role.name
  policy_arn = aws_iam_policy.codepipeline_policy.arn
}

resource "aws_codepipeline" "app_deployment_pipeline" {
  name           = "hcw-api-deployment"
  role_arn       = aws_iam_role.app_deployment_pipeline_role.arn
  pipeline_type  = "V2"
  execution_mode = "PARALLEL"

  artifact_store {
    location = aws_s3_bucket.build_artifacts.bucket
    type     = "S3"

    encryption_key {
      id   = aws_kms_key.kms_key.id
      type = "KMS"
    }
  }

  stage {
    name = "Source"

    action {
      name     = "Source"
      category = "Source"
      owner    = "AWS"
      provider = "CodeStarSourceConnection"
      version  = "1"

      output_artifacts = ["source_output"]

      configuration = {
        ConnectionArn    = data.aws_codestarconnections_connection.github_connection.arn
        FullRepositoryId = "NHSDigital/healthcare-worker-api"
        BranchName       = "develop"
      }

      namespace = "Source"
    }
  }

  stage {
    name = "Build"

    action {
      name     = "Build"
      category = "Build"
      owner    = "AWS"
      provider = "CodeBuild"
      version  = "1"

      input_artifacts  = ["source_output"]
      output_artifacts = ["build_output"]

      configuration = {
        ProjectName = "hcw-api-build"
      }
    }
  }

  stage {
    name = "Deploy"

    action {
      name     = "S3-Upload"
      category = "Deploy"
      owner    = "AWS"
      provider = "S3"
      version  = "1"

      input_artifacts = ["build_output"]

      configuration = {
        BucketName = aws_s3_bucket.build_artifacts.bucket
        ObjectKey  = "#{Source.CommitId}.zip"
        Extract    = "false"
      }
    }

    action {
      name     = "Deploy"
      category = "Build"
      owner    = "AWS"
      provider = "CodeBuild"
      version  = "1"

      input_artifacts = ["source_output"]

      role_arn = "arn:aws:iam::535002889321:role/CodeBuildDeployJobRole"

      configuration = {
        ProjectName = "hcw-api-deploy"

        EnvironmentVariables = jsonencode([
          {
            name  = "environment_name"
            value = "#{variables.branch}"
            type  = "PLAINTEXT"
          },
          {
            name  = "account_name"
            value = "dev"
            type  = "PLAINTEXT"
          },
          {
            name  = "app_s3_filename"
            value = "#{Source.CommitId}.zip"
            type  = "PLAINTEXT"
          }
        ])
      }
    }
  }

  stage {
    name = "Integration-Test"

    action {
      name     = "Integration-Test"
      category = "Build"
      owner    = "AWS"
      provider = "CodeBuild"
      version  = "1"

      input_artifacts = ["source_output"]

      configuration = {
        ProjectName = "hcw-integration-tests"

        EnvironmentVariables = jsonencode([
          {
            name  = "branch"
            value = "#{variables.branch}"
            type  = "PLAINTEXT"
          },
          {
            name  = "apim_private_key_secret_arn"
            value = var.apim_private_key_arn
            type  = "PLAINTEXT"
          }
        ])
      }
    }
  }

  stage {
    name = "Trigger-Static-Env-Deployment"

    action {
      name     = "Trigger-Static-Env-Deployment"
      category = "Build"
      owner    = "AWS"
      provider = "CodeBuild"
      version  = "1"

      input_artifacts = ["source_output"]

      configuration = {
        ProjectName = "hcw-deployment-static-env-trigger"

        EnvironmentVariables = jsonencode([
          {
            name  = "commit_id"
            value = "#{Source.CommitId}"
            type  = "PLAINTEXT"
          },
          {
            name  = "environment_name"
            value = "#{variables.branch}"
            type  = "PLAINTEXT"
          }
        ])
      }
    }
  }

  variable {
    name = "branch"
  }
}

resource "aws_iam_role" "deployment_trigger_role" {
  name = "DeploymentTriggerRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "codebuild.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_policy" "deployment_trigger_policy" {
  name = "deployment_trigger_policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        "Effect" : "Allow",
        "Action" : "codepipeline:StartPipelineExecution",
        "Resource" : [aws_codepipeline.app_deployment_pipeline.arn, aws_codepipeline.static_env_deployment_pipeline.arn]
      },
      {
        "Effect" : "Allow",
        "Action" : ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        "Resource" : [
          "arn:aws:logs:eu-west-2:${local.account_id}:log-group:/aws/codebuild/hcw-deployment-trigger:log-stream",
          "arn:aws:logs:eu-west-2:${local.account_id}:log-group:/aws/codebuild/hcw-deployment-trigger:log-stream:*",
          "arn:aws:logs:eu-west-2:${local.account_id}:log-group:/aws/codebuild/hcw-deployment-static-env-trigger:log-stream",
          "arn:aws:logs:eu-west-2:${local.account_id}:log-group:/aws/codebuild/hcw-deployment-static-env-trigger:log-stream:*"
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : "s3:GetObject",
        "Resource" : "arn:aws:s3:::nhse-iam-hcw-build-artifacts-mgmt/*"
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "codeconnections:GetConnectionToken",
          "codeconnections:GetConnection",
          "codeconnections:UseConnection"
        ],
        "Resource" : [
          data.aws_codestarconnections_connection.github_connection.arn
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "kms:DescribeKey",
          "kms:GenerateDataKey*",
          "kms:Encrypt",
          "kms:ReEncrypt*",
          "kms:Decrypt"
        ],
        "Resource" : [
          "arn:aws:kms:eu-west-2:209479271736:key/866deb7e-6dd0-4c7a-b479-3879651af711"
        ]
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "deployment_trigger-attach_policy" {
  role       = aws_iam_role.deployment_trigger_role.name
  policy_arn = aws_iam_policy.deployment_trigger_policy.arn
}

resource "aws_codebuild_project" "hcw-deployment-trigger" {
  name         = "hcw-deployment-trigger"
  service_role = aws_iam_role.deployment_trigger_role.arn

  environment {
    compute_type = "BUILD_GENERAL1_SMALL"
    image        = "aws/codebuild/amazonlinux2-x86_64-standard:5.0"
    type         = "LINUX_CONTAINER"
  }

  artifacts {
    type = "NO_ARTIFACTS"
  }

  source {
    type      = "GITHUB"
    location  = "https://github.com/NHSDigital/healthcare-worker-api"
    buildspec = "buildspecs/trigger_deployment.yml"

    git_submodules_config {
      fetch_submodules = false
    }
  }
}

resource "aws_iam_role" "integration_tests_role" {
  name = "IntegrationTestsRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "codebuild.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_policy" "integration_tests_policy" {
  name = "integration_tests_policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        "Effect" : "Allow",
        "Action" : ["s3:PutObject", "s3:GetObject"],
        "Resource" : [
          aws_s3_bucket.build_artifacts.arn,
          "${aws_s3_bucket.build_artifacts.arn}/*"
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        "Resource" : [
          "arn:aws:logs:eu-west-2:${local.account_id}:log-group:/aws/codebuild/hcw-integration-tests:log-stream",
          "arn:aws:logs:eu-west-2:${local.account_id}:log-group:/aws/codebuild/hcw-integration-tests:log-stream:*",
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : "secretsmanager:GetSecretValue"
        "Resource" : var.apim_private_key_arn
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "kms:DescribeKey",
          "kms:GenerateDataKey*",
          "kms:Encrypt",
          "kms:ReEncrypt*",
          "kms:Decrypt"
        ],
        "Resource" : [
          "arn:aws:kms:eu-west-2:209479271736:key/866deb7e-6dd0-4c7a-b479-3879651af711"
        ]
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "integration_tests_attach_policy" {
  role       = aws_iam_role.integration_tests_role.name
  policy_arn = aws_iam_policy.integration_tests_policy.arn
}

resource "aws_codebuild_project" "integration_tests" {
  name         = "hcw-integration-tests"
  service_role = aws_iam_role.integration_tests_role.arn

  environment {
    compute_type = "BUILD_GENERAL1_SMALL"
    image        = "aws/codebuild/amazonlinux2-x86_64-standard:5.0"
    type         = "LINUX_CONTAINER"
  }

  artifacts {
    type = "NO_ARTIFACTS"
  }

  source {
    type      = "GITHUB"
    location  = "https://github.com/NHSDigital/healthcare-worker-api"
    buildspec = "buildspecs/integration-tests.yml"

    git_submodules_config {
      fetch_submodules = false
    }
  }
}
