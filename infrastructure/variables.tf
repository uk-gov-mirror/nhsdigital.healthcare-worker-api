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

variable "bgp_asn" {}

variable "ldap_gateway_cidr_block" {
  type = string
}

variable "ldap_gateway_url" {
  type = string
}
