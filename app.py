from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms, disconnect
import secrets
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import Unicode, text
from werkzeug.security import generate_password_hash, check_password_hash
import time
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
import mimetypes
import pyodbc
from functools import wraps
from sqlalchemy.exc import SQLAlchemyError
import sys
from werkzeug.utils import secure_filename
import uuid
from models import db, Message, User

load_dotenv()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Configure logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Log Azure environment information
if 'WEBSITE_SITE_NAME' in os.environ:
    logger.info("Running on Azure Web App")
    logger.info(f"Site Name: {os.getenv('WEBSITE_SITE_NAME')}")
    logger.info(f"Hostname: {os.getenv('WEBSITE_HOSTNAME')}")
    logger.info(f"Python Version: {os.getenv('PYTHON_VERSION')}")

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

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

# Format connection string for SQLAlchemy
try:
    # Parse the ODBC connection string components
    params = {}
    for param in connection_string.split(';'):
        if '=' in param:
            key, value = param.split('=', 1)
            params[key.strip()] = value.strip()
    
    # Construct SQLAlchemy URL
    server = params.get('Server', '').replace('tcp:', '')
    database = params.get('Database', '')
    username = params.get('Uid', '')
    password = params.get('Pwd', '')
    
    # Log masked connection info
    masked_info = f"Server={server}, Database={database}, Username={username}, Password=***"
    logger.debug(f"Database connection info (masked): {masked_info}")
    
    # Format the SQLAlchemy URL
    connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes&connection_timeout=60&command_timeout=60&pool_size=5&pool_timeout=60&pool_pre_ping=true"
    
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
app.config['SESSION_TYPE'] = 'filesystem'  # Use filesystem to store session data
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 5,
    'pool_timeout': 60,
    'pool_recycle': 1800,
    'max_overflow': 2,
    'connect_args': {
        'timeout': 60,
        'connect_timeout': 60
    }
}
app.config['SQLALCHEMY_POOL_PRE_PING'] = True  # Enable connection testing before use

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'mov'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_to_blob_storage(file_data, content_type):
    if not BLOB_STORAGE_ENABLED:
        return None
        
    try:
        # Generate unique filename
        file_extension = content_type.split('/')[-1]
        blob_name = f"{uuid.uuid4()}.{file_extension}"
        
        # Upload to blob storage
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(file_data, blob_type="BlockBlob", content_settings={"content_type": content_type})
        
        # Return the URL
        return blob_client.url
    except Exception as e:
        print(f"Error uploading to blob storage: {str(e)}")
        return None

# Initialize extensions
db = SQLAlchemy(app)

@app.before_request
def before_request():
    # Log the request details
    logger.debug(f"Request: {request.method} {request.url}")
    logger.debug(f"Session: {session}")
    
    # Check if user is not logged in and trying to access protected routes
    if request.endpoint and request.endpoint not in ['login', 'register', 'static']:
        if 'user_id' not in session:
            logger.debug("Unauthorized access attempt, redirecting to login")
            session.clear()  # Clear any existing session data
            return redirect(url_for('login'))
        else:
            # Validate that the user still exists in the database
            try:
                user = User.query.get(session['user_id'])
                if not user:
                    logger.debug("User not found in database, clearing session")
                    session.clear()
                    return redirect(url_for('login'))
            except Exception as e:
                logger.error(f"Error validating user session: {str(e)}")
                session.clear()
                return redirect(url_for('login'))

@app.route('/')
def index():
    # If user is not logged in, redirect to login page
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        users = User.query.all()
        return render_template('index.html', users=users)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        logger.exception("Full traceback:")
        flash('An error occurred while loading the page.')
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    logger.debug("=== Starting login route ===")
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        logger.debug(f"Login attempt for username: {username}")
        
        if not username or not password:
            flash('Please provide both username and password')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()
        logger.debug(f"Found user: {user is not None}")
        
        if user:
            try:
                # Try to verify the password
                if user.check_password(password):
                    session['user_id'] = user.id
                    session['username'] = user.username
                    session.permanent = True
                    logger.info(f"Successful login for user: {username}")
                    return redirect(url_for('index'))
                else:
                    # If verification fails, try to migrate the password
                    try:
                        # Set the password again using SHA-256
                        user.set_password(password)
                        db.session.commit()
                        logger.info(f"Migrated password hash for user: {username}")
                        
                        # Log the user in
                        session['user_id'] = user.id
                        session['username'] = user.username
                        session.permanent = True
                        return redirect(url_for('index'))
                    except Exception as e:
                        logger.error(f"Error migrating password: {str(e)}")
                        flash('Error updating password. Please contact support.')
                        return redirect(url_for('login'))
            except Exception as e:
                logger.error(f"Error checking password: {str(e)}")
                flash('Invalid username or password')
                return redirect(url_for('login'))
        
        flash('Invalid username or password')
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please provide both username and password')
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
            session.permanent = True
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering user: {str(e)}")
            flash('Error creating account. Please try again.')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    try:
        if 'username' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401

        sender = session['username']
        receiver = request.form.get('receiver')
        content = request.form.get('content', '')
        media = request.files.get('media')
        
        if not receiver:
            return jsonify({'success': False, 'error': 'Receiver is required'}), 400

        has_media = False
        media_type = None
        media_url = None
        media_filename = None

        # Handle file upload if present
        if media and allowed_file(media.filename):
            try:
                # Generate unique filename
                filename = secure_filename(media.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{timestamp}_{filename}"
                
                # Save file locally
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                media.save(file_path)
                
                has_media = True
                media_type = media.content_type
                media_url = f'/uploads/{unique_filename}'
                media_filename = unique_filename
                
                logger.info(f"File uploaded successfully: {unique_filename}")
            except Exception as e:
                logger.error(f"Error saving file: {str(e)}")
                return jsonify({'success': False, 'error': 'Failed to save file'}), 500

        # Create and save the message
        try:
            message = Message(
                sender_username=sender,
                receiver_username=receiver,
                content=content,
                has_media=has_media,
                media_type=media_type,
                media_url=media_url,
                media_filename=media_filename
            )
            db.session.add(message)
            db.session.commit()
            
            # Prepare message data for socket emission
            message_data = message.to_dict()
            socketio.emit('new_message', message_data, room=sender)
            socketio.emit('new_message', message_data, room=receiver)
            
            return jsonify({
                'success': True,
                'message': message_data
            })
            
        except Exception as e:
            logger.error(f"Error saving message to database: {str(e)}")
            if has_media and media_filename:
                # Clean up uploaded file if message save fails
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], media_filename))
                except:
                    pass
            return jsonify({'success': False, 'error': 'Failed to save message'}), 500
            
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/messages/<username>')
@login_required
def get_messages(username):
    try:
        current_user = session['username']
        messages = Message.query.filter(
            ((Message.sender_username == current_user) & (Message.receiver_username == username)) |
            ((Message.sender_username == username) & (Message.receiver_username == current_user))
        ).order_by(Message.created_at.asc()).all()
        
        return jsonify({'success': True, 'messages': [msg.to_dict() for msg in messages]})
    except Exception as e:
        logger.error(f"Error in get_messages: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to retrieve messages'}), 500

@app.route('/users')
@login_required
def get_users():
    try:
        users = User.query.all()
        user_list = []
        for user in users:
            user_list.append({
                'id': user.id,
                'username': user.username,
                'created_at': user.created_at.isoformat() if user.created_at else None
            })
        return jsonify({
            'success': True,
            'users': user_list
        })
    except Exception as e:
        logger.error(f"Error getting users list: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error retrieving users list'
        }), 500

@app.route('/favorite-room', methods=['POST'])
@login_required
def toggle_favorite_room():
    try:
        logger.debug(f"Starting favorite room toggle for user {session.get('user_id')}")
        room_id = request.form.get('room_id')
        
        if not room_id:
            logger.warning("Toggle favorite failed: No room_id provided")
            return jsonify({'success': False, 'message': 'Room ID required'}), 400

        room_id = int(room_id)
        logger.debug(f"Checking if room {room_id} exists")
        room = Room.query.get(room_id)
        if not room:
            logger.warning(f"Toggle favorite failed: Room {room_id} not found")
            return jsonify({'success': False, 'message': 'Room not found'}), 404

        logger.debug(f"Checking existing favorite for user {session['user_id']} and room {room_id}")
        favorite = FavoriteRoom.query.filter_by(
            user_id=session['user_id'],
            room_id=room_id
        ).first()

        if favorite:
            logger.debug(f"Removing favorite for room {room_id}")
            db.session.delete(favorite)
            is_favorite = False
        else:
            logger.debug(f"Adding favorite for room {room_id}")
            favorite = FavoriteRoom(user_id=session['user_id'], room_id=room_id)
            db.session.add(favorite)
            is_favorite = True

        logger.debug("Committing changes to database")
        db.session.commit()
        logger.info(f"Successfully {'added' if is_favorite else 'removed'} room {room_id} {'to' if is_favorite else 'from'} favorites for user {session['user_id']}")
        
        return jsonify({
            'success': True,
            'is_favorite': is_favorite,
            'message': f'Room {"added to" if is_favorite else "removed from"} favorites successfully'
        })

    except ValueError as e:
        logger.error(f"Value error in toggle_favorite_room: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Invalid room ID format'
        }), 400
    except Exception as e:
        logger.error(f"Error toggling favorite room: {str(e)}")
        logger.exception("Full traceback:")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating favorites'
        }), 500

@app.route('/favorite-rooms')
@login_required
def get_favorite_rooms():
    try:
        logger.debug(f"Fetching favorite rooms for user {session.get('user_id')}")
        favorites = FavoriteRoom.query.filter_by(user_id=session['user_id']).all()
        favorite_rooms = []
        
        logger.debug(f"Found {len(favorites)} favorite rooms")
        for fav in favorites:
            logger.debug(f"Processing favorite room {fav.room_id}")
            room = Room.query.get(fav.room_id)
            if room:
                favorite_rooms.append({
                    'room_id': room.id,
                    'room_name': room.name,
                    'room': {
                        'is_private': room.is_private
                    }
                })
            else:
                logger.warning(f"Found orphaned favorite for non-existent room {fav.room_id}")
                
        logger.info(f"Successfully retrieved {len(favorite_rooms)} favorite rooms for user {session['user_id']}")
        return jsonify({
            'success': True,
            'favorites': favorite_rooms
        })
    except Exception as e:
        logger.error(f"Error getting favorite rooms: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({
            'success': False,
            'message': 'Error retrieving favorites'
        }), 500

@socketio.on('connect')
def handle_connect():
    try:
        logger.debug("=== Starting handle_connect ===")
        username = session.get('username')
        if not username:
            logger.warning("No username in session during connect")
            return False
            
        logger.debug(f"User {username} connected")
        join_room(username)  # Join a room named after the username
        emit('connection_established', {
            'username': username,
            'status': 'connected'
        })
        return True
        
    except Exception as e:
        logger.error(f"Error in handle_connect: {str(e)}")
        logger.exception("Full traceback:")
        return False

@socketio.on('disconnect')
def handle_disconnect():
    try:
        logger.debug("=== Starting handle_disconnect ===")
        username = session.get('username')
        if username:
            logger.debug(f"User {username} disconnected")
            leave_room(username)
            emit('user_disconnected', {'username': username}, broadcast=True)
    except Exception as e:
        logger.error(f"Error in handle_disconnect: {str(e)}")
        logger.exception("Full traceback:")

@app.route('/uploads/<path:filename>')
def serve_file(filename):
    """Serve uploaded files."""
    try:
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            filename,
            as_attachment=False
        )
    except Exception as e:
        logger.error(f"Error serving file {filename}: {str(e)}")
        return "File not found", 404

# Initialize blob storage
def initialize_blob_storage():
    try:
        global BLOB_STORAGE_ENABLED, container_client
        BLOB_STORAGE_ENABLED = False
        container_client = None
        
        # Check if Azure storage connection string is available
        storage_connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if storage_connection_string:
            # Initialize blob service client
            blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)
            container_client = blob_service_client.get_container_client(container_name)
            BLOB_STORAGE_ENABLED = True
            logger.info("Azure Blob Storage initialized successfully")
            return True
        else:
            logger.warning("Azure Blob Storage connection string not found. Using local storage only.")
            return True
    except Exception as e:
        logger.error(f"Error initializing blob storage: {str(e)}")
        return True  # Return True to allow the app to run with local storage only

def initialize_database():
    try:
        logger.info("Initializing database...")
        with app.app_context():
            # Get database engine
            engine = db.engine
            
            # Create tables if they don't exist
            with engine.begin() as connection:
                # Check if tables exist
                tables_exist = connection.execute(text("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME IN ('users', 'messages')
                """)).scalar()
                
                if not tables_exist:
                    logger.info("Creating database tables...")
                    # Create tables with explicit schema
                    connection.execute(text("""
                        IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'users') AND type in (N'U'))
                        CREATE TABLE users (
                            id INTEGER IDENTITY(1,1) PRIMARY KEY,
                            username NVARCHAR(80) UNIQUE NOT NULL,
                            password_hash NVARCHAR(256) NOT NULL,
                            created_at DATETIME DEFAULT GETDATE()
                        );
                        
                        IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'messages') AND type in (N'U'))
                        CREATE TABLE messages (
                            id INTEGER IDENTITY(1,1) PRIMARY KEY,
                            sender_username NVARCHAR(80) NOT NULL,
                            receiver_username NVARCHAR(80) NOT NULL,
                            content NTEXT,
                            created_at DATETIME DEFAULT GETDATE(),
                            has_media BIT DEFAULT 0,
                            media_type NVARCHAR(50),
                            media_url NVARCHAR(500),
                            media_filename NVARCHAR(255),
                            FOREIGN KEY (sender_username) REFERENCES users(username),
                            FOREIGN KEY (receiver_username) REFERENCES users(username)
                        );
                    """))
                    
                    # Create admin user if it doesn't exist
                    admin_exists = connection.execute(text("SELECT COUNT(*) FROM users WHERE username = 'admin'")).scalar()
                    if not admin_exists:
                        connection.execute(
                            text("INSERT INTO users (username, password_hash, created_at) VALUES (:username, :password_hash, GETDATE())"),
                            {"username": "admin", "password_hash": generate_password_hash('admin')}
                        )
                        logger.info("Admin user created successfully")
                    
                    logger.info("Database tables created successfully")
                else:
                    logger.info("Database tables already exist")
            
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

# Add this route near the top of your routes
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8181))
    app.logger.info(f"Starting application on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False) 