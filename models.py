from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
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

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_username = db.Column(db.String(80), db.ForeignKey('users.username'), nullable=False)
    receiver_username = db.Column(db.String(80), db.ForeignKey('users.username'), nullable=False)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    has_media = db.Column(db.Boolean, default=False)
    media_type = db.Column(db.String(50))
    media_url = db.Column(db.String(500))
    media_filename = db.Column(db.String(255))

    def to_dict(self):
        return {
            'id': self.id,
            'sender': self.sender_username,
            'receiver': self.receiver_username,
            'content': self.content,
            'timestamp': self.created_at.isoformat() if self.created_at else None,
            'has_media': self.has_media,
            'media_type': self.media_type,
            'media_url': self.media_url,
            'media_filename': self.media_filename
        }