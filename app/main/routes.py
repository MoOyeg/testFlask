'''
Module contains flask routing logic for application
'''
# Pylint Configurations
# pylint: disable=import-error
# pylint: disable=unused-import
# pylint: disable=wrong-import-order
# pylint: disable=bare-except
# pylint: disable=global-statement

from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, make_response
from flask_login import current_user, login_required
from app import db
from app.main import bp
from app.main.forms import PostForm
from app.models import KeyStore
from config import Config
import sys
from config import myclassvariables

#Initalize Variables
#Used as flag to store application health
HEALTH_STATUS_OK = True
#Used as flag to store application readiness
READY_STATUS_OK = True
#Used as flag to count amout of times Keystore has had an insert
COUNTER_DB_INSERTED = 0
#Used as flag to count amout of times Keystore has had a remove
COUNTER_DB_REMOVED = 0
#Duplicate Key in DB Error Message
DUPLICATE_KEY_DB_MESSAGE = "Duplicate Key Error"


def check_health():
    """ Simulates Application Health Status for Kubernetes Probes
        Will Store Application Health in Variable HEALTH_STATUS_OK for now """
    if HEALTH_STATUS_OK:
        print("Checking if Application is Healthy: Application is Healthy",
              file=sys.stderr)
    else:
        print("Checking if Application is Healthy: Application is Unhealthy", file=sys.stderr)
    return HEALTH_STATUS_OK

def check_ready():
    """ Simulates Application Readiness for Kubernetes Probes
        Will Store Application Health in Variable READY_STATUS_OK for now """
    # insertime = datetime.utcnow()
    if READY_STATUS_OK:
        print("Checking if Application is Ready: Application is Ready", file=sys.stderr)
    else:
        print("Checking if Application is Ready: Application is not Ready",
              file=sys.stderr)
    return READY_STATUS_OK

def keystore_read(keystore):
    '''Meant to Read a Keystore Object and return it's contents'''
    check_db_init()
    return keystore.query.all()

def keystore_count(keystore):
    '''Meant to Read a Keystore Object and return a count of it's objects'''
    check_db_init()
    return len(keystore.query.all())

def refresh_db(url):
    """ Refresh Database View
    """
    # form = PostForm()
    check_db_init()
    stored_values = {}
    refresh_db_value = {}
    refresh_db_time = {}
    refresh_db_remove = {}
    refresh_db_count = 0

    url = url.replace("/database", "")
    stored_values = keystore_read(KeyStore)
    # count_values = keystore_count(KeyStore)
    for val in stored_values:
        refresh_db_time.update({val.key: val.timestamp})
        refresh_db_value.update({val.key: val.value})
        refresh_db_remove.update({val.key: "{}{}?key={}".format(
            url, url_for('main.db_remove'), val.key)})
        refresh_db_count  += 1
    return [refresh_db_value, refresh_db_time, refresh_db_remove, refresh_db_count ]

@bp.route('/base', methods=['GET', 'POST'])
def base():
    """ Render Base HTML WebPage"""
    return render_template('base2.html')


@bp.route('/configuration', methods=['GET'])
def configuration():
    """ Render Configuration WebPage"""
    configs = myclassvariables()
    return render_template('configuration.html', configs=configs)

def check_db_init():
    '''Make Sure DB is Initialized with Our Table before we start'''
    #Variable stores global INIT Flag for database
    if not Config.DB_INIT:
        try:
            db.create_all()
            Config.DB_INIT = True
        except:
            pass

def database_insert(**kwargs):
    """ Method to handle insertion into DB
    """
    global COUNTER_DB_INSERTED
    check_db_init()

    try:
        keystore = kwargs["keystore"]
    except:
        print("Could not obtain keystore object from input parameter",file=sys.stderr)
        return {"status":"error","error":"Could not obtain keystore object from input parameter"}

    try:
        insertime = kwargs["insertime"]
    except:
        print("Could not obtain insertime from input parameter",file=sys.stderr)
        return {"status":"error","error":"Could not obtain insertime from input parameter"}

    try:
        key = kwargs["key"]
    except:
        print("Could not obtain key from input parameter",file=sys.stderr)
        return {"status":"error","error":"Could not obtain key from input parameter"}

    try:
        value = kwargs["value"]
    except:
        print("Could not obtain value from input parameter",file=sys.stderr)
        return {"status":"error","error":"Could not obtain value from input parameter"}

    # Check if Key Already Exists
    if keystore.query.filter_by(key=key).first() is None:
        temp = keystore(timestamp=insertime,key=key, value=value)
        db.session.add(temp)
        db.session.commit()
        COUNTER_DB_INSERTED += 1
    else:
        print("key:{0} -- {1}".format(key,DUPLICATE_KEY_DB_MESSAGE),file=sys.stderr)
        return {"status":"error","error":"{0}".format(DUPLICATE_KEY_DB_MESSAGE)}

    return {"status":"OK","error":"","key": key}

@bp.route('/database', methods=['GET', 'POST'])
def database():
    '''
    Function Handles Insert into with DB from Form/WebPage
    '''
    configs = myclassvariables()
    form = PostForm()
    fullurl = request.base_url
    check_db_init()

    if form.validate_on_submit():
        input_key = request.form["key"]
        input_value = request.form["value"]
        insertime = datetime.utcnow()

        output = database_insert(keystore=KeyStore,insertime=insertime,
                                 key=input_key,value=input_value)

        if output["status"] == "error":
            if output["error"] == DUPLICATE_KEY_DB_MESSAGE:
                flash(DUPLICATE_KEY_DB_MESSAGE,'error')
            temp_db = refresh_db(fullurl)
            return render_template('database.html', form=form, configs=configs,
                                   db_value=temp_db[0], db_time=temp_db[1], db_remove=temp_db[2])

    temp_db = refresh_db(fullurl)
    return render_template('database.html', form=form, configs=configs,
                           db_value=temp_db[0], db_time=temp_db[1], db_remove=temp_db[2])

@bp.route('/insert', methods=['POST'])
def insert():
    '''Insert into DB via API'''
    check_db_init()

    try:
        input_key = str(request.args.get("key"))
        input_value = str(request.args.get("value"))
        insertime = datetime.utcnow()
    except:
        return make_response(jsonify({'Status': 'Server could not process Input Values'}), 503)

    output = database_insert(keystore=KeyStore,insertime=insertime,
                                 key=input_key,value=input_value)

    if output["status"] == "error":
        return make_response(jsonify({'Status': "{}".format(output["error"])}), 503)
    return make_response(jsonify({'Status': 'OK'}), 200)

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    '''Starting Index Page'''
    PostForm()
    fullurl = ""

    configs = myclassvariables()
    fullurl = request.base_url
    healthdown_url = fullurl.replace("/index", "/health_down")
    readydown_url = fullurl.replace("/index", "/ready_down")

    # Need to confirm health_down applied since / and /index might be diff
    if "health_down" not in healthdown_url:
        healthdown_url = "{}{}".format(healthdown_url, "health_down")
    if "ready_down" not in readydown_url:
        readydown_url = "{}{}".format(readydown_url, "ready_down")
    return render_template('index.html')

@bp.route('/health_status', methods=['GET', 'POST'])
def health_status():
    '''Web Page for Health Route'''
    form = PostForm()
    fullurl = ""
    configs = myclassvariables()
    fullurl = request.base_url
    healthdown_url = fullurl.replace("/health_status", "/health_down")
    readydown_url = fullurl.replace("/health_status", "/ready_down")

    # Need to confirm health_down applied since / and /index might be diff
    if "health_down" not in healthdown_url:
        healthdown_url = "{}{}".format(healthdown_url, "health_down")
    if "ready_down" not in readydown_url:
        readydown_url = "{}{}".format(readydown_url, "ready_down")

    return render_template('health_status.html', form=form, configs=configs,
                           health_url=healthdown_url, ready_url=readydown_url, ready=check_ready(), health=check_health())


@bp.route('/remove', methods=['GET', 'POST'])
def db_remove():
    '''Method to remove key from DB'''
    global COUNTER_DB_REMOVED

    value_remove = request.args.get("key")
    if value_remove is not None:
        # Check if key is in DB
        tempkey = KeyStore.query.filter_by(key=value_remove).first()
        if tempkey is not None:
            db.session.delete(tempkey)
            db.session.commit()
            COUNTER_DB_REMOVED += 1
    return redirect('/database')


@bp.route('/metrics', methods=['GET'])
def metrics():
    '''Provides internal Application metrics to outside world'''
    global COUNTER_DB_INSERTED
    global COUNTER_DB_REMOVED

    print("Metrics Are Being Scraped", file=sys.stdout)
    # Provide Some Metrics to External Platforms
    db_count = keystore_count(KeyStore)
    response = make_response(
        """Available_Keys {},Total_Insert_Statements {},Total_Remove_Statements {}""".format(
            db_count,COUNTER_DB_INSERTED, COUNTER_DB_REMOVED), 200)
    response.content_type = "text/plain"
    return response

@bp.route('/health', methods=['GET'])
def health():
    '''Provide Application Health Status to the Outside World'''
    if check_health():
        return make_response(jsonify({'Status': 'OK'}), 200)
    return make_response(jsonify({'Status': 'Unavailable'}), 503)


@bp.route('/ready', methods=['GET'])
def ready():
    '''Provide Application Ready Status to the Outside World'''
    if check_ready():
        return make_response(jsonify({'Status': 'Ready'}), 200)
    return make_response(jsonify({'Status': 'Unavailable'}), 503)


@bp.route('/health_down', methods=['GET', 'POST'])
def health_down():
    '''Set Application Health down'''
    global HEALTH_STATUS_OK
    value = request.args.get("status")
    if value == "down":
        HEALTH_STATUS_OK = False
    else:
        HEALTH_STATUS_OK = True
    return redirect('/health_status')


@bp.route('/ready_down', methods=['GET'])
def ready_down():
    '''Set Application Ready down'''
    global READY_STATUS_OK
    value = request.args.get("status")
    if value == "down":
        READY_STATUS_OK = False
    else:
        READY_STATUS_OK = True
    return redirect('/health_status')
