from app import app, db, Message

def check_messages():
    with app.app_context():
        # Get all messages
        messages = Message.query.all()
        print(f"\nTotal messages in database: {len(messages)}")
        
        # Get messages without media
        no_media = Message.query.filter_by(has_media=False).all()
        print(f"\nMessages without media: {len(no_media)}")
        
        # Print details of messages without media
        for i, msg in enumerate(no_media, 1):
            print(f"\nMessage {i}:")
            print(f"ID: {msg.message_id}")
            print(f"Content: {msg.content}")
            print(f"Username: {msg.username}")
            print(f"Created at: {msg.created_at}")
            print(f"Has media: {msg.has_media}")
            print(f"Media filename: {msg.media_filename}")
            print("-" * 50)

if __name__ == "__main__":
    check_messages() 