from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import secrets
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Get connection string from environment variable
connection_string = os.getenv('AZURE_SQL_CONNECTIONSTRING')
logger.debug(f"Database URL (without password): {connection_string.replace(connection_string.split(':')[2].split('@')[0], '***')}")

app.config['SQLALCHEMY_DATABASE_URI'] = connection_string
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(16))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    message_id = db.Column(db.String(20), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'message_id': self.message_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

def init_db():
    try:
        with app.app_context():
            # Drop existing tables
            db.drop_all()
            logger.info("Dropped existing tables")
            
            # Create tables with new schema
            db.create_all()
            logger.info("Database tables created successfully with new schema")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise

# Initialize database
init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/messages')
def get_messages():
    try:
        messages = Message.query.order_by(Message.created_at.desc()).all()
        return jsonify([message.to_dict() for message in messages])
    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}")
        return jsonify([])

@app.route('/create', methods=['POST'])
def create_message():
    try:
        content = request.form.get('message')
        if not content:
            return redirect(url_for('home'))
        
        message_id = secrets.token_urlsafe(8)
        new_message = Message(content=content, message_id=message_id)
        db.session.add(new_message)
        db.session.commit()
        logger.info(f"Message created successfully with ID: {message_id}")
        
        return redirect(url_for('home'))
    except Exception as e:
        logger.error(f"Error creating message: {str(e)}")
        db.session.rollback()
        return "Error creating message. Please try again.", 500

if __name__ == '__main__':
    # Get local IP address
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    # Enable debug mode and allow external access
    port = int(os.getenv('PORT', 8080))
    print(f"\nAccess the chat app at:")
    print(f"Local: http://localhost:{port}")
    print(f"Network: http://{local_ip}:{port}\n")
    
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=True) 