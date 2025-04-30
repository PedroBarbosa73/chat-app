from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv

def test_azure_storage_connection():
    try:
        # Load environment variables
        load_dotenv()
        
        # Get connection string
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if not connection_string:
            print("Error: AZURE_STORAGE_CONNECTION_STRING not found in environment variables")
            return False
            
        # Create the BlobServiceClient object
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Get a list of containers (this will test the connection)
        containers = list(blob_service_client.list_containers())
        print(f"Successfully connected to Azure Storage!")
        print(f"Found {len(containers)} containers:")
        for container in containers:
            print(f"- {container.name}")
            
        return True
        
    except Exception as e:
        print(f"Error connecting to Azure Storage: {str(e)}")
        return False

if __name__ == "__main__":
    test_azure_storage_connection() 