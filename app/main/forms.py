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
    title = StringField('title', validators=[DataRequired()])
    text= TextAreaField('text', validators=[DataRequired()])
    submit = SubmitField('submit')
    # remove_key = StringField('Key')
    # remove = SubmitField('Remove')
    