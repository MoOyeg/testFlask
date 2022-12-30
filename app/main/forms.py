'''Flask Form Module'''
# pylint: disable=import-error
# pylint: disable=unused-import
# pylint: disable=reimported
# pylint: disable=too-few-public-methods
from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Length

class PostForm(FlaskForm):
    '''Set Form to be used fields'''
    key = StringField('Key', validators=[DataRequired()])
    value = StringField('Value', validators=[DataRequired()])
    add = SubmitField('Add')
    remove_key = StringField('Key')
    remove = SubmitField('Remove')
    