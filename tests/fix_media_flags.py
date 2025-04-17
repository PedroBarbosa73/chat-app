from app import app, db, Message, container_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_media_flags():
    with app.app_context():
        try:
            # Get all messages with media filenames
            messages = Message.query.filter(Message.media_filename.isnot(None)).all()
            logger.info(f"Found {len(messages)} messages with media filenames")
            
            fixed_count = 0
            for message in messages:
                try:
                    # Check if blob exists
                    blob_client = container_client.get_blob_client(message.media_filename)
                    blob_client.get_blob_properties()
                    
                    # If we get here, the blob exists
                    if not message.has_media:
                        logger.info(f"Fixing message {message.message_id}: Setting has_media to True")
                        message.has_media = True
                        message.content = ""  # Clear the "Media no longer available" message
                        fixed_count += 1
                        
                except Exception as e:
                    # Blob doesn't exist
                    if message.has_media:
                        logger.info(f"Fixing message {message.message_id}: Setting has_media to False")
                        message.has_media = False
                        message.content = "(Media no longer available - System Upgrade)"
                        fixed_count += 1
            
            # Commit changes
            if fixed_count > 0:
                db.session.commit()
                logger.info(f"Fixed {fixed_count} messages")
            else:
                logger.info("No messages needed fixing")
                
            return fixed_count
            
        except Exception as e:
            logger.error(f"Error during fix: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    print("Starting media flags fix...")
    try:
        fixed = fix_media_flags()
        print(f"Successfully fixed {fixed} messages")
    except Exception as e:
        print(f"Error during fix: {str(e)}") 