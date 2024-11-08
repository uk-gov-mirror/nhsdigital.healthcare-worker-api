variable "account" {
  type = string
}

variable "bgp_asn" {
  type    = string
  default = "65000"
}

variable "vpc_cidr_block" {
  type = string
}

variable "apim_private_key_arn" {
  type = string
}
