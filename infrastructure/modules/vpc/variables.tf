variable "env" {
  type = string
}

variable "account" {
  type = string
}

variable "vpc_cidr_block" {
  description = "The CIDR block for the VPC. Default value is a valid CIDR, but not acceptable by AWS and should be overridden"
  type        = string
}

variable "log_group_retention" {
  default = 30
}

variable "subdomain" {
  type = string
}

variable "ldap_service_endpoint" {
  type = string
}

variable "account_id" {
  type = string
}