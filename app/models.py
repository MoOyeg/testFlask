from app import db
from datetime import datetime

class KeyStore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    key = db.Column(db.String(64), index=True, unique=True)
    value = db.Column(db.String(120), index=True, unique=True)
    
    def __repr__(self):
        return '<Key {}>'.format(self.value) 