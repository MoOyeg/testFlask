
"""BluePrint/Flask Init file for Application"""

#Pylint
# pylint: disable=import-outside-toplevel
# pylint: disable=import-error
# pylint: disable=ungrouped-imports
# pylint: disable=wrong-import-order

import os
from flask import Flask, request, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel, lazy_gettext as _l
from config import Config
from flask.logging import default_handler



db = SQLAlchemy()
migrate = Migrate()
bootstrap = Bootstrap()


def create_app(config_class=Config):
    """Method that intializes whole app for flask"""
    app = Flask(__name__)
    app.config['DEBUG'] = True
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app,db)
    bootstrap.init_app(app)
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    return app
