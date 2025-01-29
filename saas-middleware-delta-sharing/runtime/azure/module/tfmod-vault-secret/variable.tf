variable "key_vault_id" {
  description = "Azure Key Vault id"
  type        = string
}

variable "secret_list" {
  description = "secret information"
  type = list(object({
    name         = string
    secret_value = any
  }))
}