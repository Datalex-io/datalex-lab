data "azurerm_client_config" "current" {}

data "azurerm_resource_group" "resource_group_engineering" {
  name = "datahub-engineering-${var.environment}"
}

data "azuread_group" "datahub_administrator" {
  display_name     = "Datahub Administrator"
  security_enabled = true
}

resource "azurerm_storage_account" "linux_storage_account" {
  name                     = "${var.environment}${var.storage_account_name}"
  resource_group_name      = data.azurerm_resource_group.resource_group_engineering.name
  location                 = data.azurerm_resource_group.resource_group_engineering.location
  tags                        = data.azurerm_resource_group.resource_group_engineering.tags
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_service_plan" "linux_service_plan" {
  name                = "${var.environment}-${var.service_plan_name}"
  resource_group_name = data.azurerm_resource_group.resource_group_engineering.name
  location            = data.azurerm_resource_group.resource_group_engineering.location
  tags                = data.azurerm_resource_group.resource_group_engineering.tags
  os_type             = "Linux"
  sku_name            = "Y1"
}

resource "azurerm_application_insights" "linux_application_insights" {
  name                = "${var.environment}-${var.azurerm_application_insights_name}"
  resource_group_name = data.azurerm_resource_group.resource_group_engineering.name
  location            = data.azurerm_resource_group.resource_group_engineering.location
  tags                        = data.azurerm_resource_group.resource_group_engineering.tags
  application_type    = "other"
}

resource "azurerm_linux_function_app" "linux_python_linux_function_app" {
  name                = "${var.environment}-${var.azurerm_linux_function_app_name}"
  resource_group_name = data.azurerm_resource_group.resource_group_engineering.name
  location            = data.azurerm_resource_group.resource_group_engineering.location
  tags                        = data.azurerm_resource_group.resource_group_engineering.tags
  
  service_plan_id            = azurerm_service_plan.linux_service_plan.id
  storage_account_name       = azurerm_storage_account.linux_storage_account.name
  storage_account_access_key = azurerm_storage_account.linux_storage_account.primary_access_key
  https_only                 = true
  site_config {
    application_insights_key = azurerm_application_insights.linux_application_insights.instrumentation_key
    application_insights_connection_string = azurerm_application_insights.linux_application_insights.connection_string
    application_stack {
        python_version = 3.11 #FUNCTIONS_WORKER_RUNTIME        
    }
  }
  app_settings = {
    "APPINSIGHTS_INSTRUMENTATIONKEY" = "${azurerm_application_insights.linux_application_insights.instrumentation_key}",
    KEY_VAULT_NAME="${var.environment}${var.azure_key_vault_name}"
    DATABRICKS_TOKEN_NAME=var.databricks_token_name
    DELTASHARING_TABLES_NAME=var.databricks_delta_sharing_name
    DATABRICKS_HOST=var.databricks_host
  }
  identity {
        type = "SystemAssigned"
    }
}

# create azure vault
resource "azurerm_key_vault" "middleware_vault" {
  name                        = "${var.environment}${var.azure_key_vault_name}"
  resource_group_name         = data.azurerm_resource_group.resource_group_engineering.name
  location                    = data.azurerm_resource_group.resource_group_engineering.location
  tags                        = data.azurerm_resource_group.resource_group_engineering.tags
  enabled_for_disk_encryption = true
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false

  sku_name = "standard"

  # add Datahub administrator
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azuread_group.datahub_administrator.object_id

    key_permissions = [
      "Backup", "Create", "Decrypt", "Delete", "Encrypt", "Get", "Import", "List", "Purge", "Recover", "Restore", "Sign", "UnwrapKey", "Update", "Verify", "WrapKey", "Release", "Rotate", "GetRotationPolicy", "SetRotationPolicy",
    ]

    secret_permissions = [
      "Get", "List", "Set", "Delete", "Recover", "Backup", "Restore", "Purge",
    ]

    storage_permissions = [
      "Backup", "Delete", "DeleteSAS", "Get", "GetSAS", "List", "ListSAS", "Purge", "Recover", "RegenerateKey", "Restore", "Set", "SetSAS", "Update"
    ]
  }
  # add Azure Function
  access_policy {
    tenant_id = "${azurerm_linux_function_app.linux_python_linux_function_app.identity.0.tenant_id}"
    object_id = "${azurerm_linux_function_app.linux_python_linux_function_app.identity.0.principal_id}"

    secret_permissions = [
      "Get", "List", "Set", "Delete", "Recover", "Backup", "Restore", "Purge",
    ]
  }
}

data "azurerm_function_app_host_keys" "linux_python_linux_function_app" {
  name                = "${var.environment}-${var.azurerm_linux_function_app_name}"
  resource_group_name = data.azurerm_resource_group.resource_group_engineering.name
}

# Add Azure Function's key to azure keyvault
resource "azurerm_key_vault_secret" "engineering" {
  name = "azureFunctionAccessKey"
  value = data.azurerm_function_app_host_keys.linux_python_linux_function_app.default_function_key
  key_vault_id = azurerm_key_vault.middleware_vault.id
  depends_on = [ azurerm_linux_function_app.linux_python_linux_function_app ]
}

module "vault_secret" {
  source          = "./module/tfmod-vault-secret"
  key_vault_id = azurerm_key_vault.middleware_vault.id
  secret_list     = concat(var.databricks_token, var.databricks_tables_names)
}