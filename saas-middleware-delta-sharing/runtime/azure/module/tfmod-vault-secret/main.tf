resource "azurerm_key_vault_secret" "secret" {
  for_each = {
    for index, vault in var.secret_list :
    vault.name => vault
  }
  name         = each.value.name
  value        = each.value.secret_value
  key_vault_id = var.key_vault_id
}