locals {
  env = terraform.workspace
}

variable "account" {
  type = string
}

variable "account_id" {
  type = string
}

variable "apim_environment" {
  type = string
}

variable "app_s3_filename" {
  type    = string
  default = "hcw-api-build.zip"
}

variable "vpc_cidr_block" {
  description = "The CIDR block for the VPC. Default value is a valid CIDR, but not acceptable by AWS and should be overridden"
  type        = string
}

variable "ldap_gateway_url" {
  type = string
}

variable "ldap_service_endpoint" {
  type = string
}

variable "subdomain" {
  type = string
}

variable "provisioned_capacity" {
  type = number
}

variable "include_nft_vpc" {
  type = bool
}

variable "log_group_retention" {
  description = "Number of days to retain CloudWatch log groups"
  type        = number
  default     = 30
}

variable "sandbox" {
  type = bool
}

variable "vpc_env" {
  type = string
}
