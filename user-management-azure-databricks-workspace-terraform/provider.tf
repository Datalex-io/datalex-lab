provider "azurerm" {
  subscription_id            = var.subscription_id
  skip_provider_registration = true

  features {}
}

provider "databricks" {
  azure_workspace_resource_id = data.azurerm_databricks_workspace.this.id
}