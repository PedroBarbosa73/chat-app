from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import secrets
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
from sqlalchemy import Unicode
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
logger.debug(f"Database URL (without password): {connection_string.replace(connection_string.split(':')[2].split('@')[0], '***')}")

# Format connection string for SQL Server with proper encoding
connection_string = connection_string.replace('?', '?TrustServerCertificate=yes&')
app.config['SQLALCHEMY_DATABASE_URI'] = connection_string
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(16))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False
db = SQLAlchemy(app)

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
    content = db.Column(Unicode(4000), nullable=False)  # Using Unicode type for proper emoji support
    message_id = db.Column(db.String(20), unique=True, nullable=False)
    username = db.Column(db.String(50), nullable=False, default='Anonymous')
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with Room
    room = db.relationship('Room', backref=db.backref('messages', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'message_id': self.message_id,
            'username': self.username,
            'room_name': self.room.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
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

# Create tables if they don't exist
with app.app_context():
    try:
        # Check if tables exist
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
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
    
    rooms = Room.query.order_by(Room.name).all()
    authorized_rooms = session.get('authorized_rooms', [])
    
    # Get favorite rooms for the current user
    favorite_rooms = FavoriteRoom.query.filter_by(user_id=session['user_id']).all()
    favorite_room_ids = [fav.room_id for fav in favorite_rooms]
    
    return render_template('index.html', 
                         rooms=rooms, 
                         authorized_rooms=authorized_rooms,
                         favorite_room_ids=favorite_room_ids)

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
        room_id = request.args.get('room_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = 50  # Number of messages per page
        
        if not room_id:
            return jsonify({'error': 'Room ID is required'})
        
        # Check if user is authorized for private rooms
        room = Room.query.get(room_id)
        if not room:
            return jsonify({'error': 'Room not found'})
        
        if room.is_private and room_id not in session.get('authorized_rooms', []):
            return jsonify({'error': 'Unauthorized'})
        
        # Get messages with pagination, ordered by created_at descending
        messages = Message.query.filter_by(room_id=room_id)\
            .order_by(Message.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
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
        content = request.form.get('message')
        username = request.form.get('username', 'Anonymous')
        room_id = request.form.get('room_id', type=int)
        
        if not content or not room_id:
            return jsonify({'success': False, 'message': 'Message and room selection are required'})
        
        # Verify room exists and user is authorized
        room = Room.query.get(room_id)
        if not room:
            return jsonify({'success': False, 'message': 'Selected room does not exist'})
            
        authorized_rooms = session.get('authorized_rooms', [])
        if room.is_private and room_id not in authorized_rooms:
            return jsonify({'success': False, 'message': 'You are not authorized to post in this room'})
        
        message_id = secrets.token_urlsafe(8)
        new_message = Message(
            content=content,
            message_id=message_id,
            username=username,
            room_id=room_id
        )
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

@app.route('/favorite-rooms')
def get_favorite_rooms():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    try:
        favorites = FavoriteRoom.query.filter_by(user_id=session['user_id']).all()
        return jsonify({
            'success': True,
            'favorites': [fav.to_dict() for fav in favorites]
        })
    except Exception as e:
        logger.error(f"Error getting favorite rooms: {str(e)}")
        return jsonify({'success': False, 'message': 'Error getting favorite rooms'})

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