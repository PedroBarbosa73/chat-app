from app import app, db, Message, container_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_media_messages():
    try:
        # Get all messages with media
        media_messages = Message.query.filter_by(has_media=True).all()
        logger.info(f"Found {len(media_messages)} messages with media")
        
        cleaned_count = 0
        for message in media_messages:
            if not message.media_filename:
                continue
                
            try:
                # Check if blob exists
                blob_client = container_client.get_blob_client(message.media_filename)
                blob_client.get_blob_properties()
            except Exception as e:
                logger.info(f"Marking message {message.message_id} as no media (blob not found: {message.media_filename})")
                # Update message to show media is no longer available
                message.content = "(Media no longer available - System Upgrade)"
                message.has_media = False
                message.media_url = None
                cleaned_count += 1
        
        # Commit changes
        db.session.commit()
        logger.info(f"Cleaned up {cleaned_count} messages with missing media")
        return cleaned_count
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        db.session.rollback()
        raise

if __name__ == "__main__":
    print("Starting media messages cleanup...")
    with app.app_context():
        try:
            cleaned = cleanup_media_messages()
            print(f"Successfully cleaned up {cleaned} messages with missing media")
        except Exception as e:
            print(f"Error during cleanup: {str(e)}") 