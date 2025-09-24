variable "is_pr" {
  type = bool
}

variable "env" {
  type = string
}

variable "s3_filename" {
  type = string
}

variable "apim_environment" {
  type = string
}

variable "ldap_gateway_url" {
  type = string
}

variable "provisioned_capacity" {
  type = number
}

variable "sandbox_mode" {
  type = bool
}

variable "vpc_env" {
  type = string
}

variable "subdomain" {
  type = string
}

variable "account_id" {
  type = string
}

variable "hec_token_secret_id" {
  type = string
}

variable "log_group_retention" {
  description = "Number of days to retain CloudWatch log groups"
  type        = number
  default     = 30
}

variable "access_logs_bucket_id" {
  description = "Access logs bucket id"
  type        = string
  default     = null
}
