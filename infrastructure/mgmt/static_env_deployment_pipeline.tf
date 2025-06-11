resource "aws_codebuild_project" "hcw-deployment-static-env-trigger" {
  name         = "hcw-deployment-static-env-trigger"
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
    buildspec = "buildspecs/static-env-deploy-trigger.yml"

    git_submodules_config {
      fetch_submodules = false
    }
  }
}

resource "aws_kms_key" "kms_key" {
  description         = "Encryption key used for artifacts which are shared between AWS accounts"
  enable_key_rotation = true

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::209479271736:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow access for Key Administrators"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::209479271736:role/aws-reserved/sso.amazonaws.com/eu-west-2/AWSReservedSSO_AWSAdministratorAccess_a77a65f102a298f7"
        }
        Action = [
          "kms:Create*",
          "kms:Describe*",
          "kms:Enable*",
          "kms:List*",
          "kms:Put*",
          "kms:Update*",
          "kms:Revoke*",
          "kms:Disable*",
          "kms:Get*",
          "kms:Delete*",
          "kms:TagResource",
          "kms:UntagResource",
          "kms:ScheduleKeyDeletion",
          "kms:CancelKeyDeletion",
          "kms:RotateKeyOnDemand"
        ]
        Resource : "*"
      },
      {
        Sid    = "Allow use of the key"
        Effect = "Allow"
        Principal = {
          AWS = [
            "arn:aws:iam::711387117641:root",
            "arn:aws:iam::535002889321:root",
            "arn:aws:iam::266735814611:root"
          ]
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      },
      {
        Sid    = "Allow attachment of persistent resources"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::711387117641:root"
        }
        Action = [
          "kms:CreateGrant",
          "kms:ListGrants",
          "kms:RevokeGrant"
        ]
        Resource = "*"
        Condition = {
          Bool = {
            "kms:GrantIsForAWSResource" = "true"
          }
        }
      }
    ]
  })
}

resource "aws_kms_alias" "key_alias" {
  name          = "alias/Artifact-Encryption-Key"
  target_key_id = aws_kms_key.kms_key.key_id
}

resource "aws_codepipeline" "static_env_deployment_pipeline" {
  name           = "hcw-api-static-env-deployment"
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
    name = "Int-Approval"
    action {
      category = "Approval"
      name     = "Int-Approval"
      owner    = "AWS"
      provider = "Manual"
      version  = "1"
    }
  }

  stage {
    name = "Int-Deploy"

    action {
      name     = "Int-Deploy"
      category = "Build"
      owner    = "AWS"
      provider = "CodeBuild"
      version  = "1"

      input_artifacts = ["source_output"]

      role_arn = "arn:aws:iam::711387117641:role/CodeBuildDeployJobRole"

      configuration = {
        ProjectName = "hcw-api-deploy"

        EnvironmentVariables = jsonencode([
          {
            name  = "environment_name"
            value = "int"
            type  = "PLAINTEXT"
          },
          {
            name  = "account_name"
            value = "int"
            type  = "PLAINTEXT"
          },
          {
            name  = "app_s3_filename"
            value = "#{variables.commit_id}.zip"
            type  = "PLAINTEXT"
          }
        ])
      }
    }
  }

  stage {
    name = "Int-Integration-Test"

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
            value = "int"
            type  = "PLAINTEXT"
          }
        ])
      }
    }
  }

  stage {
    name = "Prod-Approval"
    action {
      category = "Approval"
      name     = "Prod-Approval"
      owner    = "AWS"
      provider = "Manual"
      version  = "1"
    }
  }

  stage {
    name = "Prod-Deploy"

    action {
      name     = "Prod-Deploy"
      category = "Build"
      owner    = "AWS"
      provider = "CodeBuild"
      version  = "1"

      input_artifacts = ["source_output"]

      role_arn = "arn:aws:iam::266735814611:role/CodeBuildDeployJobRole"

      configuration = {
        ProjectName = "hcw-api-deploy"

        EnvironmentVariables = jsonencode([
          {
            name  = "environment_name"
            value = "int"
            type  = "PLAINTEXT"
          },
          {
            name  = "account_name"
            value = "int"
            type  = "PLAINTEXT"
          },
          {
            name  = "app_s3_filename"
            value = "#{variables.commit_id}.zip"
            type  = "PLAINTEXT"
          }
        ])
      }
    }
  }

  variable {
    name = "commit_id"
  }
}
