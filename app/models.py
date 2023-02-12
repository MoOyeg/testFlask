'''Model used the Represent a Keystore object'''
# Pylint
# pylint: disable=too-few-public-methods
# pylint: disable=trailing-whitespace


from datetime import datetime
from app import db


class Note(db.Model):
    """KeyStore Object """

    __tablename__ = 'note'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    title = db.Column(db.String(64), index=True)
    note = db.Column(db.Text, unique=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    title_user_id = db.column_property(title + " " + user_id)

    def __repr__(self):
        """ Return Class Representation"""
        return f"<id={self.id}, timestamp={self.timestamp},title={self.title},note={self.note},user_id={self.user_id}>"


class User(db.Model):
    """User Object that owns a keystore"""

    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    firstname = db.Column(db.String(120), unique=False)
    lastname = db.Column(db.String(120), unique=False)
    fullname = db.column_property(firstname + " " + lastname)
    auth_method = db.Column(db.String(120), unique=False)
    user_note = db.relationship(Note, backref='report')    
    user_note_count = db.column_property(db.select([db.func.count(Note.id)]).\
            where(Note.user_id==id).\
            correlate_except(Note))

    def __repr__(self):
        """ Return Class Representation"""
        return f"<id={self.id}, username={self.username},firstname={self.firstname},lastname={self.lastname},fullname={self.fullname}>"


class InsertCountMetric(db.Model):
    """Count User Insertion Count"""
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))


class DeleteCountMetric(db.Model):
    """Count User Insertion Count"""
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
