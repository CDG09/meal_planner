import datetime

from app import db
from passlib.hash import sha256_crypt
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Password handling
    def set_password(self, password):  # To hash passwords before storing
        self.password_hash = sha256_crypt.encrypt(password)

    def check_password(self, password):  # To verify password during login
        return sha256_crypt.verify(password, self.password_hash)

class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(255))
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='meal', lazy='dynamic')


