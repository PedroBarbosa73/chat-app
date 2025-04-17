from app import app, container_client
from azure.core.exceptions import ResourceNotFoundError

def check_storage():
    with app.app_context():
        try:
            # Check container properties
            props = container_client.get_container_properties()
            print(f"Container last modified: {props.last_modified}")
            
            # List all blobs
            print("\nListing blobs:")
            blobs = container_client.list_blobs()
            count = 0
            for blob in blobs:
                count += 1
                print(f"{count}. {blob.name} (size: {blob.size} bytes)")
                
            if count == 0:
                print("No blobs found in container")
                
        except ResourceNotFoundError:
            print("Container not found")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_storage() 