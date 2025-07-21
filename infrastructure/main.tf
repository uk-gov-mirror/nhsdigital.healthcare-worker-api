locals {
  is_pr   = length(regexall("pr-.*", local.env)) > 0
  is_mgmt = length(regexall("mgmt*", local.env)) > 0 || local.env == "management"
  is_sand = var.sandbox

  include_vpc = !local.is_pr && !local.is_mgmt && !local.is_sand
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    encrypt        = true
    bucket         = "nhse-iam-hcw-terraform-state"
    dynamodb_table = "terraform-state-lock"
    key            = "terraform.tfstate"
    region         = "eu-west-2"
    assume_role = {
      role_arn = "arn:aws:iam::209479271736:role/CodeBuildDeployJobRole"
    }
  }
}

provider "aws" {
  region = "eu-west-2"

  assume_role {
    role_arn = format("arn:aws:iam::%s:role/CodeBuildDeployJobRole", var.account_id)
  }

  default_tags {
    tags = {
      Environment = local.env
      Account     = var.account
    }
  }
}


provider "aws" {
  alias  = "management"
  region = "eu-west-2"

  assume_role {
    role_arn = "arn:aws:iam::209479271736:role/CodeBuildDeployJobRole"
  }

  default_tags {
    tags = {
      Environment = local.env
      Account     = var.account
    }
  }
}

module "terraform_state" {
  source = "./terraform_state"

  count = local.env == "management" ? 1 : 0
}

module "management" {
  source               = "./mgmt"
  account              = var.account
  apim_private_key_arn = module.deploy[0].apim_private_key_arn

  count = local.env == "management" ? 1 : 0
}

module "vpc" {
  source         = "./modules/vpc"
  account        = var.account
  vpc_cidr_block = var.vpc_cidr_block
  env            = local.env
  subdomain      = var.subdomain

  ldap_service_endpoint = var.ldap_service_endpoint
  log_group_retention   = var.log_group_retention

  count = local.include_vpc ? 1 : 0
}

module "deploy" {
  source = "./deploy"

  count = local.is_mgmt ? 1 : 0
}

data "aws_secretsmanager_secret" "hec_token" {
  count = !local.include_vpc ? 1 : 0
  name  = "hec_token"
}

module "app" {
  source     = "./modules/hcw-api"
  env        = local.env
  is_pr      = local.is_pr
  subdomain  = var.subdomain
  account_id = var.account_id

  sandbox_mode = var.sandbox

  s3_filename          = var.app_s3_filename
  apim_environment     = var.apim_environment
  ldap_gateway_url     = var.ldap_gateway_url
  provisioned_capacity = var.provisioned_capacity
  vpc_env              = var.vpc_env
  hec_token_secret_id  = local.include_vpc ? module.vpc[0].hec_token_secret_id : data.aws_secretsmanager_secret.hec_token[0].id
  log_group_retention  = var.log_group_retention

  count = !local.is_mgmt ? 1 : 0
}

module "nft" {
  source = "./modules/nft"
  env    = local.env

  count = var.include_nft_vpc && !local.is_pr && !local.is_mgmt ? 1 : 0
}
