output "adb-admin-users-count" {
  description = "Number of admin users provisioned in databricks workspace"
  value       = length(resource.databricks_user.adb_admin)
}

output "adb-reader-users-count" {
  description = "Number of reader users (included admin one) provisioned in databricks workspace"
  value       = length(resource.databricks_user.adb_user)
}