/*
  Get Databricks' workspace data
*/
data "azurerm_databricks_workspace" "this" {
  name                = var.databricks_workspace_name
  resource_group_name = var.resource_group_name
}

/*
  Get EntraID's Groups
*/
data "azuread_group" "admin" {
  display_name     = var.admin_group_name
  security_enabled = true
}
data "azuread_group" "reader" {
  display_name     = var.reader_group_name
  security_enabled = true
}

/*
  Get EntraID's Groups members
*/
data "azuread_users" "aad_admin_users" {
  object_ids = data.azuread_group.admin.members
}
data "azuread_users" "aad_reader_users" {
  object_ids = data.azuread_group.reader.members
}

/*
  Add admin's users to Databricks with admin membership
*/
data "databricks_group" "admins" {
  display_name = "admins"
}
resource "databricks_user" "adb_admin" {
  for_each             = { for i, v in data.azuread_users.aad_admin_users.users : i => v }
  user_name            = each.value.mail
  display_name         = each.value.display_name
  allow_cluster_create = true
}
resource "databricks_group_member" "adb-admin-member" {
  for_each  = databricks_user.adb_admin
  group_id  = data.databricks_group.admins.id
  member_id = each.value.id
}

/*
  Add reader's users to Databricks
*/
resource "databricks_user" "adb_user" {
  for_each     = { for i, v in data.azuread_users.aad_reader_users.users : i => v }
  user_name    = each.value.mail
  display_name = each.value.display_name
}

# Assign DDL permissions for all users (Databricks's users group) on hive_metastore
resource "databricks_sql_permissions" "reader" {
  catalog = true

  privilege_assignments {
    principal  = "users"
    privileges = ["SELECT", "READ_METADATA"]
  }
}