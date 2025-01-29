variable "environment" {
  description = "deployment environment"
  type        = string
}

variable "storage_account_name" {
  type = string
}

variable "service_plan_name" {
  type = string
}

variable "azurerm_linux_function_app_name" {
  type = string
}

variable "azurerm_application_insights_name" {
  type = string
}
variable "azure_key_vault_name" {
  type = string
}

variable "databricks_token" {
  description = "databricks' token"
  type = list(object({
    name         = string
    secret_value = string
  }))
}

variable "databricks_tables_names" {
  description = "databricks' tables names"
  type = list(object({
    name         = string
    secret_value = string
  }))
}

variable "databricks_token_name" {
  description = "databricks' token names"
  type = string
}

variable "databricks_delta_sharing_name" {
  description = "databricks' delta sharing names"
  type = string
}

variable "databricks_host" {
  description = "databricks' token names"
  type = string
}