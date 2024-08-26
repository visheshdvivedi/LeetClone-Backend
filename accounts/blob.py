import os, base64

import requests
from django.conf import settings
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

_conn_string = settings.STORAGE_CONN_STRING
blob_service_client = BlobServiceClient.from_connection_string(_conn_string)

def upload_file_from_url(name:str, url:str):
    blob_client = blob_service_client.get_blob_client(container=settings.STORAGE_CONTAINER_NAME, blob=name)
    img_data = requests.get(url).content
    blob_client.upload_blob(img_data, overwrite=True)
    return blob_client.url

def upload_file_from_bytes(name:str, img_data:bytes):
    blob_client = blob_service_client.get_blob_client(container=settings.STORAGE_CONTAINER_NAME, blob=name)
    blob_client.upload_blob(img_data, overwrite=True)
    return blob_client.url

def get_all_blobs():
    blob_container_client = blob_service_client.get_container_client(container=settings.STORAGE_CONTAINER_NAME)
    return [blob.name for blob in blob_container_client.list_blobs()]

def download_blob(name: str, path: str):
    blob_client = blob_service_client.get_blob_client(container=settings.STORAGE_CONTAINER_NAME, blob=name)
    return base64.b64encode(blob_client.download_blob().readall())