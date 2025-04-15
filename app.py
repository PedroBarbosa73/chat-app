from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from flask_sqlalchemy import SQLAlchemy
import secrets
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import Unicode
from werkzeug.security import generate_password_hash, check_password_hash
import time
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
import mimetypes

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Log Azure environment information
if 'WEBSITE_SITE_NAME' in os.environ:
    logger.info("Running on Azure Web App")
    logger.info(f"Site Name: {os.getenv('WEBSITE_SITE_NAME')}")
    logger.info(f"Hostname: {os.getenv('WEBSITE_HOSTNAME')}")
    logger.info(f"Python Version: {os.getenv('PYTHON_VERSION')}")

app = Flask(__name__)

# Custom Jinja filter for datetime formatting
@app.template_filter('datetime')
def format_datetime(value):
    if not value:
        return ''
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return value.strftime('%B %d, %Y at %I:%M %p')

# Get connection string from environment variable
connection_string = os.getenv('AZURE_SQL_CONNECTIONSTRING')
if not connection_string:
    logger.error("AZURE_SQL_CONNECTIONSTRING environment variable is not set!")
    raise ValueError("Database connection string not found in environment variables")

container_name = "chat-media"  # Name of the container for storing media files
logger.debug(f"Database URL (without password): {connection_string.replace(connection_string.split(':')[2].split('@')[0], '***')}")

# Format connection string for SQL Server with proper encoding and timeout settings
try:
    if 'WEBSITE_SITE_NAME' in os.environ:  # Check if running on Azure
        # Azure-specific connection string modifications
        connection_string = connection_string.replace('ODBC+Driver+18+for+SQL+Server', 'ODBC+Driver+17+for+SQL+Server')
    else:
        # Local development connection string modifications
        connection_string = connection_string.replace('?', '?TrustServerCertificate=yes&connect_timeout=30&timeout=30&')
    
    logger.info("Database connection string configured successfully")
except Exception as e:
    logger.error(f"Error configuring database connection string: {str(e)}")
    raise

app.config['SQLALCHEMY_DATABASE_URI'] = connection_string
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(16))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)  # Session lasts for 31 days
app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # Refresh session on each request
db = SQLAlchemy(app)

# Make session permanent by default
@app.before_request
def make_session_permanent():
    session.permanent = True

class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    is_private = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        if password:
            self.password_hash = generate_password_hash(password)
            self.is_private = True
        else:
            self.password_hash = None
            self.is_private = False

    def check_password(self, password):
        # If room is private and has a password hash, require password
        if self.is_private and self.password_hash:
            if not password:
                return False
            return check_password_hash(self.password_hash, password)
        # If room is not private or has no password hash, allow access
        return True

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'is_private': self.is_private,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(Unicode(4000), nullable=True)  # Changed to nullable=True
    message_id = db.Column(db.String(20), unique=True, nullable=False)
    username = db.Column(db.String(50), nullable=False, default='Anonymous')
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    # New fields for media
    has_media = db.Column(db.Boolean, default=False)
    media_type = db.Column(db.String(50), nullable=True)  # 'image' or 'video'
    media_url = db.Column(db.String(500), nullable=True)
    media_filename = db.Column(db.String(255), nullable=True)

    # Relationship with Room
    room = db.relationship('Room', backref=db.backref('messages', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'message_id': self.message_id,
            'username': self.username,
            'room_name': self.room.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'has_media': self.has_media,
            'media_type': self.media_type,
            'media_url': self.media_url,
            'media_filename': self.media_filename
        }

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class FavoriteRoom(db.Model):
    __tablename__ = 'favorite_rooms'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Add unique constraint to prevent duplicate favorites
    __table_args__ = (db.UniqueConstraint('user_id', 'room_id', name='unique_user_room_favorite'),)

    # Relationships
    user = db.relationship('User', backref=db.backref('favorite_rooms', lazy=True))
    room = db.relationship('Room', backref=db.backref('favorited_by', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'room_id': self.room_id,
            'room_name': self.room.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Global variables for blob storage
blob_service_client = None
container_client = None

def initialize_blob_storage():
    global blob_service_client, container_client
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info("Initializing Azure Blob Storage...")
            connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            if not connection_string:
                raise ValueError("AZURE_STORAGE_CONNECTION_STRING not found in environment variables")
            
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            container_name = "chat-media"
            
            # Create container if it doesn't exist
            container_client = blob_service_client.get_container_client(container_name)
            try:
                container_client.get_container_properties()
                logger.info(f"Container '{container_name}' exists and is accessible")
                return True
            except Exception as container_error:
                logger.warning(f"Container '{container_name}' does not exist, creating it... Error: {str(container_error)}")
                container_client = blob_service_client.create_container(container_name)
                logger.info(f"Container '{container_name}' created successfully")
                return True
                
        except Exception as e:
            retry_count += 1
            logger.error(f"Error initializing Azure Blob Storage (attempt {retry_count}/{max_retries}): {str(e)}")
            if retry_count == max_retries:
                logger.error("Failed to initialize blob storage after maximum retries")
                return False
            time.sleep(1)  # Wait before retrying

# Initialize storage on startup
def initialize_storage():
    with app.app_context():
        if not initialize_blob_storage():
            logger.error("Failed to initialize blob storage")

# Register the initialization function
app.before_request_funcs.setdefault(None, []).append(initialize_storage)

def ensure_blob_storage():
    global blob_service_client, container_client
    if blob_service_client is None or container_client is None:
        return initialize_blob_storage()
    return True

def generate_sas_token(blob_name):
    """Generate a SAS token for a blob"""
    try:
        # Get account info from the container client
        account_name = container_client.account_name
        # Get the account key from the connection string
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        # Parse connection string to get account key
        connection_parts = dict(part.split('=', 1) for part in connection_string.split(';'))
        account_key = connection_parts.get('AccountKey')
        
        if not account_key:
            raise ValueError("AccountKey not found in connection string")
        
        # Generate SAS token
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(timezone.utc) + timedelta(hours=24)
        )
        return sas_token
    except Exception as e:
        logger.error(f"Error generating SAS token: {str(e)}")
        raise

# Create tables if they don't exist
with app.app_context():
    try:
        # Create all tables if they don't exist
        db.create_all()
        logger.info("Tables created/updated successfully")
    except Exception as e:
        logger.error(f"Error during table creation: {str(e)}")
        raise

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        # Retry connection if needed
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                rooms = Room.query.order_by(Room.name).all()
                authorized_rooms = session.get('authorized_rooms', [])
                
                # Get favorite rooms for the current user
                favorite_rooms = FavoriteRoom.query.filter_by(user_id=session['user_id']).all()
                favorite_room_ids = [fav.room_id for fav in favorite_rooms]
                
                return render_template('index.html', 
                                    rooms=rooms, 
                                    authorized_rooms=authorized_rooms,
                                    favorite_room_ids=favorite_room_ids)
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    logger.error(f"Error connecting to database after {max_retries} retries: {str(e)}")
                    flash('Error connecting to database. Please try again later.')
                    return redirect(url_for('login'))
                logger.warning(f"Retrying database connection (attempt {retry_count}/{max_retries})")
                time.sleep(1)  # Wait 1 second before retrying
    except Exception as e:
        logger.error(f"Error in home route: {str(e)}")
        flash('Error loading page. Please try again later.')
        return redirect(url_for('login'))

@app.route('/create-room', methods=['POST'])
def create_room():
    try:
        room_name = request.form.get('room_name')
        password = request.form.get('room_password')
        
        if not room_name:
            flash('Room name is required')
            return redirect(url_for('home'))
        
        # Check if room already exists
        existing_room = Room.query.filter_by(name=room_name).first()
        if existing_room:
            flash('Room already exists')
            return redirect(url_for('home'))
        
        new_room = Room(name=room_name)
        new_room.set_password(password)
        
        db.session.add(new_room)
        db.session.commit()
        
        # If room is private, add it to authorized rooms for the creator
        if new_room.is_private:
            authorized_rooms = session.get('authorized_rooms', [])
            authorized_rooms.append(new_room.id)
            session['authorized_rooms'] = authorized_rooms
        
        logger.info(f"Room created successfully: {room_name} (Private: {new_room.is_private})")
        return redirect(url_for('home'))
    except Exception as e:
        logger.error(f"Error creating room: {str(e)}")
        db.session.rollback()
        flash('Error creating room')
        return redirect(url_for('home'))

@app.route('/join-room', methods=['POST'])
def join_room():
    try:
        room_id = request.form.get('room_id', type=int)
        password = request.form.get('room_password', '')
        
        if not room_id:
            return jsonify({'success': False, 'message': 'Room ID is required'})
        
        room = Room.query.get(room_id)
        if not room:
            return jsonify({'success': False, 'message': 'Room not found'})
        
        if room.check_password(password):
            authorized_rooms = session.get('authorized_rooms', [])
            if room_id not in authorized_rooms:
                authorized_rooms.append(room_id)
                session['authorized_rooms'] = authorized_rooms
                session.modified = True
                # Force session to be saved
                session.permanent = True
            return jsonify({
                'success': True,
                'room_id': room_id,
                'is_private': room.is_private,
                'room_name': room.name
            })
        else:
            return jsonify({'success': False, 'message': 'Incorrect password'})
    except Exception as e:
        logger.error(f"Error joining room: {str(e)}")
        return jsonify({'success': False, 'message': 'Error joining room'})

@app.route('/messages')
def get_messages():
    try:
        # Check if user is logged in
        if 'user_id' not in session:
            logger.debug("User not logged in")
            return jsonify({'error': 'Please log in to view messages'})
            
        room_id = request.args.get('room_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = 50  # Number of messages per page
        
        logger.debug(f"Fetching messages for room_id: {room_id}, page: {page}")
        
        if not room_id:
            logger.debug("No room_id provided")
            return jsonify({'error': 'Room ID is required'})
        
        # Check if user is authorized for private rooms
        room = Room.query.get(room_id)
        if not room:
            logger.debug(f"Room not found: {room_id}")
            return jsonify({'error': 'Room not found'})
        
        authorized_rooms = session.get('authorized_rooms', [])
        if room.is_private and room_id not in authorized_rooms:
            logger.debug(f"User not authorized for private room: {room_id}")
            return jsonify({'error': 'Unauthorized access to private room'})
        
        # Get messages with pagination, ordered by created_at ascending
        messages = Message.query.filter_by(room_id=room_id)\
            .order_by(Message.created_at.asc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        logger.debug(f"Found {messages.total} total messages, showing {len(messages.items)} on page {page}")
        
        return jsonify({
            'messages': [msg.to_dict() for msg in messages.items],
            'has_next': messages.has_next,
            'next_page': messages.next_num if messages.has_next else None,
            'total': messages.total
        })
    
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}")
        return jsonify({'error': 'Error getting messages'})

@app.route('/create', methods=['POST'])
def create_message():
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Please login first'})
        
        data = request.get_json()
        content = data.get('message', '').strip()
        username = data.get('username', 'Anonymous')
        room_id = data.get('room_id')
        media_data = data.get('media_data')
        
        if not room_id:
            return jsonify({'success': False, 'message': 'Room selection is required'})
        
        if not content and not media_data:
            return jsonify({'success': False, 'message': 'Message or media is required'})
            
        # Verify room exists and user is authorized
        room = Room.query.get(room_id)
        if not room:
            return jsonify({'success': False, 'message': 'Selected room does not exist'})
            
        authorized_rooms = session.get('authorized_rooms', [])
        if room.is_private and room_id not in authorized_rooms:
            return jsonify({'success': False, 'message': 'You are not authorized to post in this room'})
        
        message_id = secrets.token_urlsafe(8)
        new_message = Message(
            content=content if content else None,  # Allow NULL content
            message_id=message_id,
            username=username,
            room_id=room_id
        )
        
        # Add media information if present
        if media_data and media_data.get('success'):
            new_message.has_media = True
            new_message.media_type = media_data.get('media_type')
            new_message.media_url = media_data.get('media_url')
            new_message.media_filename = media_data.get('filename')
        
        db.session.add(new_message)
        db.session.commit()
        logger.info(f"Message created successfully with ID: {message_id} by user: {username} in room: {room.name}")
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error creating message: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error creating message'})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('home'))
        
        flash('Invalid username or password')
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        user = User(username=username)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('home'))
        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            db.session.rollback()
            flash('Error registering user')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/favorite-room', methods=['POST'])
def favorite_room():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    try:
        room_id = request.form.get('room_id', type=int)
        if not room_id:
            return jsonify({'success': False, 'message': 'Room ID is required'})
        
        # Check if room exists
        room = Room.query.get(room_id)
        if not room:
            return jsonify({'success': False, 'message': 'Room not found'})
        
        # Check if already favorited
        existing_favorite = FavoriteRoom.query.filter_by(
            user_id=session['user_id'],
            room_id=room_id
        ).first()
        
        if existing_favorite:
            # If already favorited, unfavorite it
            db.session.delete(existing_favorite)
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Room removed from favorites',
                'is_favorite': False
            })
        
        # Add to favorites
        new_favorite = FavoriteRoom(
            user_id=session['user_id'],
            room_id=room_id
        )
        db.session.add(new_favorite)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Room added to favorites',
            'is_favorite': True
        })
    
    except Exception as e:
        logger.error(f"Error managing favorite room: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error managing favorite room'})

@app.route('/favorite-rooms', methods=['GET'])
def get_favorite_rooms():
    try:
        logger.debug("=== Starting get_favorite_rooms ===")
        logger.debug(f"Session contents: {dict(session)}")
        
        if 'user_id' not in session:
            logger.warning("No user_id found in session")
            return jsonify({'success': False, 'message': 'Please login first'})
        
        user_id = session['user_id']
        logger.debug(f'Getting favorites for user_id: {user_id}')
        
        # First check if user exists
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User not found for user_id: {user_id}")
            return jsonify({'success': False, 'message': 'User not found'})
        
        logger.debug(f'Found user: {user.username}')
        
        # Get favorite rooms with complete room information
        logger.debug("Querying favorite rooms from database")
        favorites = db.session.query(FavoriteRoom, Room)\
            .join(Room, FavoriteRoom.room_id == Room.id)\
            .filter(FavoriteRoom.user_id == user_id)\
            .all()
        
        logger.debug(f'Found {len(favorites)} favorites')
        
        # Log each favorite room for debugging
        for fav, room in favorites:
            logger.debug(f'Favorite room: {room.name} (ID: {room.id})')
            logger.debug(f'Favorite entry: user_id={fav.user_id}, room_id={fav.room_id}')
        
        # Format the response with complete room information
        favorite_rooms = [{
            'id': fav.id,
            'user_id': fav.user_id,
            'room_id': fav.room_id,
            'room_name': room.name,
            'room': {
                'id': room.id,
                'name': room.name,
                'is_private': room.is_private,
                'created_at': room.created_at.isoformat() if room.created_at else None
            }
        } for fav, room in favorites]
        
        response = {
            'success': True,
            'favorites': favorite_rooms
        }
        logger.debug(f'Sending response: {response}')
        logger.debug("=== End get_favorite_rooms ===")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error getting favorite rooms: {str(e)}")
        logger.exception("Full traceback:")  # This will log the full stack trace
        return jsonify({'success': False, 'message': f'Error getting favorite rooms: {str(e)}'})

@app.route('/upload-media', methods=['POST'])
def upload_media():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    try:
        # Ensure blob storage is initialized
        if not ensure_blob_storage():
            return jsonify({'success': False, 'message': 'Storage service unavailable'})
            
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'})
        
        # Check file type
        content_type = file.content_type
        if not content_type.startswith(('image/', 'video/')):
            return jsonify({'success': False, 'message': 'Only image and video files are allowed'})
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{secrets.token_urlsafe(16)}{file_extension}"
        
        logger.info(f"Attempting to upload file {file.filename} as {unique_filename}")
        
        # Upload to Azure Blob Storage with retry
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                blob_client = container_client.get_blob_client(unique_filename)
                blob_client.upload_blob(file)
                logger.info(f"File uploaded successfully: {unique_filename}")
                
                # Generate SAS token for the blob
                sas_token = generate_sas_token(unique_filename)
                
                # Get the URL of the uploaded file with SAS token
                media_url = f"{blob_client.url}?{sas_token}"
                
                return jsonify({
                    'success': True,
                    'media_url': media_url,
                    'media_type': 'image' if content_type.startswith('image/') else 'video',
                    'filename': file.filename,
                    'unique_filename': unique_filename
                })
            except Exception as e:
                retry_count += 1
                logger.error(f"Error uploading file (attempt {retry_count}/{max_retries}): {str(e)}")
                if retry_count == max_retries:
                    return jsonify({'success': False, 'message': 'Error uploading file after multiple attempts'})
                time.sleep(1)
                
    except Exception as e:
        logger.error(f"Error in upload_media route: {str(e)}")
        return jsonify({'success': False, 'message': 'Error processing upload request'})

@app.route('/delete-room/<int:room_id>', methods=['DELETE'])
def delete_room(room_id):
    if not session.get('username') or session['username'].lower() != 'nando':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    try:
        # Delete messages first (due to foreign key constraint)
        db.session.query(Message).filter_by(room_id=room_id).delete()
        
        # Delete room favorites
        db.session.query(FavoriteRoom).filter_by(room_id=room_id).delete()
        
        # Delete the room
        room = db.session.query(Room).filter_by(id=room_id).first()
        if room:
            db.session.delete(room)
            db.session.commit()
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Room not found'}), 404
            
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting room: {str(e)}")
        return jsonify({'success': False, 'message': 'Error deleting room'}), 500

if __name__ == '__main__':
    try:
        # Azure Web Apps expects port 8000 when running in container
        port = int(os.environ.get('WEBSITES_PORT', '8000'))
        print(f"Starting server on port {port}")
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        print(f"Error starting server: {e}")
        raise 