import os
import base64
import requests
import json
from dotenv import load_dotenv
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

load_dotenv()

KEY_VAULT_NAME = os.environ["KEY_VAULT_NAME"]

class AzureKeyVault:
	"""
  Class to interact with Azure Key Vault for secret management.
  """
	keyvault_url = None
	credential = None
	client = None
	domain = None

	def __init__(self):
		"""
		Initialize the Key Vault URL and the client to access secrets.
		"""
		self.keyvault_url = f"https://{KEY_VAULT_NAME}.vault.azure.net"
		self.credential = DefaultAzureCredential()
		self.client = SecretClient(vault_url=self.keyvault_url, credential=self.credential)

	def get_secret(self, secret_name: str):
		"""
		Retrieves a secret from Azure Key Vault.
		:param secret_name: The name of the secret to retrieve
		:return: The secret object
		"""
		return self.client.get_secret(secret_name)
  
	def set_secret(self, secret_name: str, secret_value: str):
		"""
		Sets a secret in Azure Key Vault.
		:param secret_name: The name of the secret
		:param secret_value: The value of the secret to store
		:return: The created or updated secret
		"""
		return self.client.set_secret(secret_name, secret_value)
	
	def delete_secret(self, secret_name: str):
		"""
		Deletes a secret from Key Vault and purges it permanently.
		:param secret_name: The name of the secret to delete
		:return: The deleted secret
		"""
		delete_secret_poller = self.client.begin_delete_secret(secret_name)
		secret = delete_secret_poller.result()
		delete_secret_poller.wait()
		# Purge the deleted secret permanently
		self.client.purge_deleted_secret(secret_name)
		print(f"Secret with name '{secret.name}' was deleted on date {secret.deleted_date}.")
		return secret