provider "azurerm" {
  subscription_id            = var.environment == "run" ? "" : ""
  skip_provider_registration = true

  features {}
}