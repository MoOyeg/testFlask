import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


def create_uri(user,password,host,db):
        if ( user != "" and password != "" and host != "" and db != ""):
            return "mysql+pymysql://{}:{}@{}/{}".format(user,password, host,db)
        else:
            return "sqlite:///:memory:"


class Config(object):
    #Secret key Configuration for Flask not for application
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_USERNAME = os.environ.get('MYSQL_USER') or ""
    SQLALCHEMY_DATABASE_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ""
    SQLALCHEMY_DATABASE_HOST = os.environ.get('MYSQL_HOST') or ""
    SQLALCHEMY_DATABASE_DB = os.environ.get('MYSQL_DATABASE') or ""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DB_INIT = False
    
    #Generate URI from Parameters
    SQLALCHEMY_DATABASE_URI = create_uri(SQLALCHEMY_DATABASE_USERNAME,SQLALCHEMY_DATABASE_PASSWORD,SQLALCHEMY_DATABASE_HOST,
    SQLALCHEMY_DATABASE_DB)    

def myclassvariables():
    temp = {}
    result = vars(Config)
    for key in result:
        if "__" not in key and "<" not in key and "myclassvariables" not in key :
            temp.update({key:result[key]})
    return temp

