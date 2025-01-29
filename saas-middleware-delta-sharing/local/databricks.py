import os
import base64
import requests
import json
from dotenv import load_dotenv

from azure_vault import AzureKeyVault

load_dotenv()

DATABRICKS_TOKEN_NAME = os.environ["DATABRICKS_TOKEN_NAME"]

class DatabricksClientAuthenticator:
	"""
	Class responsible for authenticating to Databricks using OAuth2 and an access token.
	"""
	domain = None
	token = None

	def __init__(self):
		"""
		Initializes authentication to access the Databricks API.
		"""
		self.domain = os.environ["DATABRICKS_HOST"]
		self.token = self.get_token()

	def get_token(self):
		"""
		Retrieves the access token using the information stored in Azure Key Vault.
		:return: The access token for authentication
		"""
		vault = AzureKeyVault()
		CLIENT_ID = json.loads(vault.get_secret(DATABRICKS_TOKEN_NAME).value)['CLIENT_ID']
		CLIENT_SECRET = json.loads(vault.get_secret(DATABRICKS_TOKEN_NAME).value)['CLIENT_SECRET']
		URL=f"https://{self.domain}/oidc/v1/token"

		headers = {'Content-Type': 'application/x-www-form-urlencoded'}
		payload = {'grant_type': 'client_credentials', 'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET, 'scope': 'all-apis'}

		response = requests.post(URL,headers=headers, data=payload)

		return response.json()['access_token']

	def before_http_request(self, headers):
		"""
		Adds authentication information to the HTTP request headers.
		:param headers: The initial request headers
		:return: The headers with added authentication information
		"""
		headers['Authorization'] = f"Bearer {self.token}"
		headers['Content-Type'] = f"application/json"
		return headers

class DatabricksDeltaSharingClient:
	"""
	Class to interact with the Delta Sharing API from Databricks, allowing secure data sharing.
	"""
	authenticator = None
	domain = None

	def __init__(self):
		"""
		Initializes authentication and Databricks domain for API calls.
		"""
		self.authenticator = DatabricksClientAuthenticator()
		self.domain = self.authenticator.domain

	def _get_api(self, uri: str):
		"""
		Helper function to perform GET API requests.
		:param uri: The URL to use for the GET request
		:return: The JSON response from the API
		"""
		headers = self.authenticator.before_http_request({})
		try:
			response = requests.get(uri, headers=headers)
			response.raise_for_status()
			return response.json()
		except requests.exceptions.HTTPError as error:
			raise error
		except requests.ConnectionError as error:
			raise error

	def _post_api(self, uri: str, body: dict):
		"""
		Helper function to perform POST API requests.
		:param uri: The URL to use for the POST request
		:param body: The body of the request in JSON format
		:return: The JSON response from the API
		"""
		headers = self.authenticator.before_http_request({})
		try:
			response = requests.post(uri, headers=headers, json=body)
			response.raise_for_status()
			return response.json()
		except requests.exceptions.HTTPError as error:
			raise error
		except requests.ConnectionError as error:
			raise error

	def _patch_api(self, uri: str, body: dict):
		"""
		Helper function to perform PATCH API requests.
		:param uri: The URL to use for the PATCH request
		:param body: The body of the request in JSON format
		:return: The JSON response from the API
		"""
		headers = self.authenticator.before_http_request({})
		try:
			response = requests.patch(uri, headers=headers, json=body)
			response.raise_for_status()
			return response.json()
		except requests.exceptions.HTTPError as error:
			raise error
		except requests.ConnectionError as error:
			raise error
		
	def _delete_api(self, uri: str):
		"""
		Helper function to perform DELETE API requests.
		:param uri: The URL to use for the DELETE request
		:return: The JSON response from the API
		"""
		headers = self.authenticator.before_http_request({})
		try:
			response = requests.delete(uri, headers=headers)
			response.raise_for_status()
			return response.json()
		except requests.exceptions.HTTPError as error:
			raise error
		except requests.ConnectionError as error:
			raise error

	def create_share(self, share_name: str, table_name: str, partitions: list):
		"""
		Creates a data share in the Databricks Unity Catalog.
		:param share_name: The name of the share
		:param table_name: The name of the table to be shared
		:param partitions: A list of partitions to share
		:return: The API response message
		"""
		# Create share
		create_share_url = f"https://{self.domain}/api/2.1/unity-catalog/shares"
		payload = {'name': share_name}
		response = self._post_api(create_share_url, payload)

		# Update share with tables & partitions
		update_share_url = f"https://{self.domain}/api/2.1/unity-catalog/shares/{share_name}"
		payload = {
			"updates": [
					{
						"action": "ADD",
						"data_object": {
							"name": table_name,
							"history_data_sharing_status": "ENABLED",
							"partitions": partitions
						}
					}
				]
		}
		response = self._patch_api(update_share_url, payload)

		return response

	def update_share_permissions(self, share_name: str, recipient_name: str):
		"""
		Updates share permissions for a recipient.
		:param share_name: The name of the share
		:param recipient_name: The name of the recipient
		:return: The API response message
		"""
		grant_share_url = f"https://{self.domain}/api/2.1/unity-catalog/shares/{share_name}/permissions"
		payload = {"changes": [{"principal": recipient_name,"add": ["SELECT"]}]}

		response = self._patch_api(grant_share_url, payload)
		return response
	
	def delete_share(self, share_name: str):
		"""
		Deletes a data share from Databricks Unity Catalog.
		:param share_name: The name of the share to delete
		:return: The API response message
		"""
		# Create share
		delete_share_url = f"https://{self.domain}/api/2.1/unity-catalog/shares/{share_name}"
		response = self._delete_api(delete_share_url)

		return response

	def create_recipient(self, recipient_name: str):
		"""
		Creates a recipient for data sharing.
		:param recipient_name: The name of the recipient
		:return: The API response after recipient activation
		"""
		# Create recipient
		create_recipient_url = f"https://{self.domain}/api/2.1/unity-catalog/recipients"
		payload = {'name': recipient_name, 'authentication_type': 'TOKEN'}
		response = self._post_api(create_recipient_url, payload)
		# Active token
		activation_url_token = response['tokens'][0]['activation_url'].split(sep="?")[1]
		activate_recipient_url = f"https://{self.domain}/api/2.1/unity-catalog/public/data_sharing_activation/{activation_url_token}"
		response = requests.get(activate_recipient_url)

		return response.json()
	
	def rotate_recipient_token(self, recipient_name: str):
		"""
		Rotates a recipient's token, generating a new activation token.
		:param recipient_name: The name of the recipient
		:return: The API response after activating the new token
		"""
		# Get new activation_url_token
		rotate_share_url = f"https://{self.domain}/api/2.1/unity-catalog/recipients/{recipient_name}/rotate-token"
		payload = {"existing_token_expire_in_seconds": 0}
		response = self._post_api(rotate_share_url, payload)
		# Active token
		activation_url_token = response['tokens'][0]['activation_url'].split(sep="?")[1]
		activate_recipient_url = f"https://{self.domain}/api/2.1/unity-catalog/public/data_sharing_activation/{activation_url_token}"

		response = requests.get(activate_recipient_url)

		return response.json()
	
	def delete_recipient(self, recipient_name: str):
		"""
		Deletes an existing recipient.
		:param recipient_name: The name of the recipient to delete
		:return: The API response message
		"""
		delete_recipient_url = f"https://{self.domain}/api/2.1/unity-catalog/recipients/{recipient_name}"
		response = self._delete_api(delete_recipient_url)