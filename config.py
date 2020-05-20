import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DB_INIT = False

    def myclassvariables():
        temp = {}
        result = vars(Config)
        for key in result:
            if "__" not in key and "<" not in key and "myclassvariables" not in key :
                temp.update({key:result[key]})
        return temp
