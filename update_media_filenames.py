from app import app, db, Message, container_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_media_filenames():
    with app.app_context():
        try:
            # Get list of all blobs
            blobs = list(container_client.list_blobs())
            logger.info(f"Found {len(blobs)} blobs in storage")
            
            # Get all messages with media filenames
            messages = Message.query.filter(Message.media_filename.isnot(None)).all()
            logger.info(f"Found {len(messages)} messages with media filenames")
            
            # Create a mapping of extensions to blobs
            ext_to_blobs = {}
            for blob in blobs:
                ext = blob.name.split('.')[-1].lower()
                if ext not in ext_to_blobs:
                    ext_to_blobs[ext] = []
                ext_to_blobs[ext].append(blob)
            
            updated_count = 0
            for message in messages:
                original_ext = message.media_filename.split('.')[-1].lower()
                
                # Find blobs with matching extension
                matching_blobs = ext_to_blobs.get(original_ext, [])
                
                if matching_blobs:
                    # Use any blob with the matching extension
                    # We'll take the first one since we can't match by timestamp
                    matching_blob = matching_blobs.pop(0)
                    
                    logger.info(f"Updating message {message.message_id}:")
                    logger.info(f"  Old filename: {message.media_filename}")
                    logger.info(f"  New filename: {matching_blob.name}")
                    
                    message.media_filename = matching_blob.name
                    message.has_media = True
                    message.content = ""  # Clear the "Media no longer available" message
                    updated_count += 1
            
            # Commit changes
            if updated_count > 0:
                db.session.commit()
                logger.info(f"Updated {updated_count} messages")
            else:
                logger.info("No messages needed updating")
                
            return updated_count
            
        except Exception as e:
            logger.error(f"Error during update: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    print("Starting media filename updates...")
    try:
        updated = update_media_filenames()
        print(f"Successfully updated {updated} messages")
    except Exception as e:
        print(f"Error during update: {str(e)}") 