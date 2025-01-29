from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os

from azure_vault import AzureKeyVault
from databricks import DatabricksDeltaSharingClient

app = FastAPI()

DELTASHARING_TABLES_NAME = os.environ["DELTASHARING_TABLES_NAME"]

@app.get("/clientspace/{client_id}/delta-sharing-token", status_code=200)
def get_share(client_id: str):
  """
  Retrieves the Delta Sharing token for a specific client.
  :param client_id: The unique identifier for the client
  :return: The Delta Sharing token if found
  """
  try:
    # Get the secret (Delta Sharing token) from Azure Key Vault
    vault_client = AzureKeyVault().get_secret(client_id).value
    return json.loads(vault_client)
  except Exception as ex:
    # Handle errors if the secret is not found
    if type(ex).__name__ == "ResourceNotFoundError":
      raise HTTPException(status_code=404, detail="Token doesn’t exis.")
    else:
      template = "DeltaSharingException - An exception of type {0} occurred. Arguments:\n{1!r}"
      message = template.format(type(ex).__name__, ex.args)
      raise HTTPException(status_code=500, detail=message)


@app.post("/clientspace/{client_id}/delta-sharing-token", status_code=200)
def create_share(client_id: str):
  """
  Creates a new Delta Sharing token for a client if it doesn't already exist.
  :param client_id: The unique identifier for the client
  :return: The response indicating success or failure
  """
  try:
    # Attempt to get the secret (Delta Sharing token) for the client
    client_id = AzureKeyVault().get_secret(client_id).value
    print(client_id)
    return HTTPException(status_code=409, detail="Token already exists.")
  except Exception as ex:
    try:
      # Handle ResourceNotFoundError to create a new token if not found
      if type(ex).__name__ == "ResourceNotFoundError":
        # Get the table name from Azure Key Vault
        table_name = json.loads(AzureKeyVault().get_secret(DELTASHARING_TABLES_NAME).value)['partitioned_platform_usage']
        delta_sharing = DatabricksDeltaSharingClient()

        # Create share and recipient for the client
        partitions= [{"values": [{"name": "client_space_uid", "value": client_id, "op": "EQUAL" }]}]
        share_response = delta_sharing.create_share(f"{client_id}_partitioned_platform_usage", table_name, partitions)
        recipient_response = delta_sharing.create_recipient(client_id)

        # Save the recipient token to Azure Key Vault
        AzureKeyVault().set_secret(client_id, json.dumps(recipient_response))

        # Grant access to the recipient on the share
        update_grant_response = delta_sharing.update_share_permissions(f"{client_id}_partitioned_platform_usage", f"{client_id}")

        return recipient_response
      else:
        # Handle any other errors by raising an exception
        template = "AzureKeyVault - An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        raise HTTPException(status_code=500, detail=message)
    except Exception as e:
      # Handle nested exceptions when creating share or recipient
      template = "DeltaSharingException - An exception of type {0} occurred. Arguments:\n{1!r}"
      message = template.format(type(e).__name__, e.args)
      raise HTTPException(status_code=500, detail=message)


@app.post("/clientspace/{client_id}/delta-sharing-token/refresh", status_code=200)
def refresh_recipient(client_id: str):
  """
  Refreshes the Delta Sharing token for a recipient.
  :param client_id: The unique identifier for the client
  :return: The new recipient token
  """
  try:
    # Retrieve the secret (current token) for the client
    vault = AzureKeyVault()
    client = vault.get_secret(client_id).value
    print(client)

    # Rotate the recipient token
    delta_sharing = DatabricksDeltaSharingClient()
    recipient_response = delta_sharing.rotate_recipient_token(client_id)
    
    # Update the vault with the new token
    vault.set_secret(client_id, json.dumps(recipient_response))
    return recipient_response
  except Exception as ex:
    # Handle errors if the secret is not found
    if type(ex).__name__ == "ResourceNotFoundError":
      raise HTTPException(status_code=404, detail="Token doesn’t exis.")
    # Handle any other errors by raising an exception
    else:
      template = "DeltaSharingException - An exception of type {0} occurred. Arguments:\n{1!r}"
      message = template.format(type(ex).__name__, ex.args)
      raise HTTPException(status_code=500, detail=message)


@app.delete("/clientspace/{client_id}/delta-sharing-token", status_code=204)
def delete_share(client_id: str):
  """
  Deletes the Delta Sharing token for a client and revokes access.
  :param client_id: The unique identifier for the client
  :return: A response indicating successful deletion
  """
  try:
    # Retrieve the secret (token) for the client
    vault = AzureKeyVault()
    client = vault.get_secret(client_id).value
    print(client)

    # Delete recipient and share
    delta_sharing = DatabricksDeltaSharingClient()
    recipient_response = delta_sharing.delete_recipient(client_id)
    share_response = delta_sharing.delete_share(f"{client_id}_partitioned_platform_usage")

    # Delete the secret from Azure Key Vault
    vault_response = vault.delete_secret(client_id)
  except Exception as ex:
    # Handle errors if the secret is not found
    if type(ex).__name__ == "ResourceNotFoundError":
      raise HTTPException(status_code=404, detail="Token doesn’t exis.")
    # Handle any other errors by raising an exception
    else:
      template = "DeltaSharingException - An exception of type {0} occurred. Arguments:\n{1!r}"
      message = template.format(type(ex).__name__, ex.args)
      raise HTTPException(status_code=500, detail=message)