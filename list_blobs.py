from app import container_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_all_blobs():
    try:
        print("\nListing all blobs in container:")
        print("-" * 50)
        blob_count = 0
        for blob in container_client.list_blobs():
            print(f"Name: {blob.name}")
            print(f"Last Modified: {blob.last_modified}")
            print(f"Size: {blob.size} bytes")
            print("-" * 50)
            blob_count += 1
        print(f"\nTotal blobs found: {blob_count}")
    except Exception as e:
        print(f"Error listing blobs: {str(e)}")

if __name__ == "__main__":
    list_all_blobs() 