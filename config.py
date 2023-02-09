'''Module obtains Configuration for Flask Applications'''
# pylint: disable=global-statement
# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods
# pylint: consider-using-dict-items

import os
import logging
import requests
from dotenv import load_dotenv  # pylint: disable=import-error

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

COUNT_PULL = 0
METADATA = {}


def create_uri(user, password, host, db):
    '''Method Falls back to SQLLite if cannot reach MYSQl Database'''
    if (user != "" and password != "" and host != "" and db != ""):
        return "mysql+pymysql://{}:{}@{}/{}".format(user, password, host, db)
    return "sqlite:///:memory:"


def pullmetadata(hostname, metadata_port):
    '''Pull Metadata from Metadata tool if available'''
    timeout = 3
    global COUNT_PULL
    try:
        result = requests.get("http://{0}:{1}/metadata".format(
            hostname, metadata_port),  timeout=timeout, allow_redirects=True)
    except Exception as error:  # pylint: disable=broad-except
        print("Error in determine function for {0} module, see exception stack\n:{1}"
              .format(__name__, error))
        return {}
    finally:
        COUNT_PULL += 1
    return result.json()


class Config():
    '''Class to hold Class Variables for Flask Module'''
    # Secret key Configuration for Flask not for application
    CLOUD_PROVIDER = os.environ.get('CLOUD_PROVIDER') or ""
    CLOUD_REGION = os.environ.get('CLOUD_REGION') or ""
    CLOUD_AVAILIBILITY_ZONE = os.environ.get('CLOUD_AVAILIBILITY_ZONE') or ""
    HOSTNAME = os.environ.get('NODE_NAME') or ""
    METADATA_PORT = os.environ.get("METADATA_PORT") or "8080"
    KUBERNETES_DISTRIBUTION = os.environ.get('KUBERNETES_DISTRIBUTION') or ""
    KUBERNETES_VERSION = os.environ.get('KUBERNETES_VERSION') or ""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'L8QMIC'
    SESSION_COOKIE_HEADER = os.environ.get('SESSION_COOKIE_HEADER') or 'moJrFe'
    SQLALCHEMY_DATABASE_USERNAME = os.environ.get('MYSQL_USER') or ""
    SQLALCHEMY_DATABASE_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ""
    SQLALCHEMY_DATABASE_HOST = os.environ.get('MYSQL_HOST') or ""
    SQLALCHEMY_DATABASE_DB = os.environ.get('MYSQL_DATABASE') or ""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    KUBERNETES_SERVICE_PORT = os.environ.get('KUBERNETES_SERVICE_PORT') or ""
    #REMOTE_DEBUG = os.environ.get('REMOTE_DEBUG') or "True"
    DB_INIT = False
    GUNICORN_LOGGER = logging.getLogger('gunicorn.error') or "info"
    #Integration Parameters
    AUTH_INTEGRATION =  False
    # Generate URI from Parameters
    SQLALCHEMY_DATABASE_URI = create_uri(SQLALCHEMY_DATABASE_USERNAME, SQLALCHEMY_DATABASE_PASSWORD, SQLALCHEMY_DATABASE_HOST,
                                         SQLALCHEMY_DATABASE_DB)
 



def myclassvariables():
    '''Function to help return classvariables'''
    temp = {}
    result = vars(Config)
    global METADATA
    for key in result:
        if "__" not in key and "<" not in key and "myclassvariables" not in key:
            temp.update({key: result[key]})
    temp2 = temp.copy()
    if METADATA == {} and temp["HOSTNAME"] != "":
        if COUNT_PULL == 0:
            METADATA = dict(pullmetadata(
                temp["HOSTNAME"], temp["METADATA_PORT"]))
    if METADATA != {}:
        for key in METADATA:
            temp2.update({key: METADATA[key]})
    return temp2
