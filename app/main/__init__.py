'''
Module initalizes blueprint used by rest of application
'''
#PyLint
# pylint: disable=import-error
# pylint: disable=wrong-import-position
from flask import Blueprint

bp = Blueprint('main', __name__)

from app.main import routes
