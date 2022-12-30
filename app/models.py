'''Model used the Represent a Keystore object'''
#Pylint
# pylint: disable=too-few-public-methods
# pylint: disable=trailing-whitespace

from datetime import datetime
from app import db

class KeyStore(db.Model):
    """KeyStore Object """
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    key = db.Column(db.String(64), index=True, unique=True)
    value = db.Column(db.String(120), index=True, unique=False)
    
    def __repr__(self):
        """ Return Class Representation"""
        return '<Key {}>'.format(self.value)
    