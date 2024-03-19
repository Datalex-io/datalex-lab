variable "subscription_id" {
  description = "deployment subscription"
  type        = string
}

variable "resource_group_name" {
  description = "Applicatif resource group's name"
  type        = string
}

variable "databricks_workspace_name" {
  description = "Databricks' workspace name"
  type        = string
}

variable "admin_group_name" {
  description = "EntraID's admin group name"
  type        = string
}

variable "reader_group_name" {
  description = "EntraID's reader group name"
  type        = string
}