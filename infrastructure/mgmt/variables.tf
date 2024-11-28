variable "account" {
  type = string
}

variable "bgp_asn" {
  type    = string
  default = "65000"
}

variable "apim_private_key_arn" {
  type = string
}
