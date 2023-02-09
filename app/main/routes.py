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
    jsonify, current_app, make_response, has_app_context
from functools import wraps
from flask_openid import OpenID
from flask_login import current_user, login_required
from app import db
from app.main import bp
from app.main.forms import PostForm
from app.errors import ValidationError
from app.models import User, Note, InsertCountMetric, DeleteCountMetric
from config import Config

import sys
from config import myclassvariables
from random import randrange

# Initalize Variables
# Used as flag to store application health
HEALTH_STATUS_OK = True
# Used as flag to store application readiness
READY_STATUS_OK = True
# Duplicate Key in DB Error Message
DUPLICATE_KEY_DB_MESSAGE = "Duplicate Key Error"


def check_health():
    """ Simulates Application Health Status for Kubernetes Probes
        Will Store Application Health in Variable HEALTH_STATUS_OK for now """
    if HEALTH_STATUS_OK:
        current_app.logger.info(
            "Checking if Application is Healthy - Application is Healthy")
    else:
        current_app.logger.error(
            "Checking if Application is Healthy - Application is Unhealthy")
    return HEALTH_STATUS_OK

def check_ready():
    """ Simulates Application Readiness for Kubernetes Probes
        Will Store Application Health in Variable READY_STATUS_OK for now """
    # insertime = datetime.utcnow()
    if READY_STATUS_OK:
        current_app.logger.info(
            "Checking if Application is Ready - Application is Ready")
    else:
        current_app.logger.error(
            "Checking if Application is Ready - Application is not Ready")
    return READY_STATUS_OK

def note_read(user_id, note_id=None, title=None):
    '''Meant to Read a note Object and return it's contents'''

    if note_id is not None:
        user_notes = Note.query.filter_by(user_id=user_id, id=note_id).first()
    elif title is not None:
        user_notes = Note.query.filter_by(user_id=user_id, title=title).first()
    else:
        user_notes = Note.query.filter_by(user_id=user_id)
    return user_notes

def insert_statement_count(user_id):
    '''Return Number of Insert Statments by User'''
    insert_count = InsertCountMetric.query.filter_by(user_id=user_id).first()
    if insert_count is None:
        return None
    return insert_count.count

def delete_statement_count(user_id):
    '''Return Number of Delete Statments by User'''
    delete_count = DeleteCountMetric.query.filter_by(user_id=user_id).first()
    if delete_count is None:
        return None
    return delete_count.count

def note_count(user_id):
    '''Meant to return counts of user notes'''
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return None
    return user.user_note_count

def refresh_notes_view(url, user_id):
    """ Refresh Database View"""

    current_app.logger.debug("Refresh DB view")
    refresh_db_note = {}
    refresh_db_time = {}
    refresh_db_title = {}
    refresh_db_remove = {}
    refresh_db_count = 0

    url = url.replace("/notes", "")
    present_notes = note_read(user_id)
    # count_values = note_count(note)
    for temp_note in present_notes:
        refresh_db_time.update({"key": temp_note.timestamp})
        refresh_db_note.update({"key": temp_note.note})
        refresh_db_title.update({"key": temp_note.title})
        refresh_db_remove.update({"key": "{}{}?id={}".format(
            url, url_for('main.db_remove'), temp_note.id)})
        refresh_db_count += 1
    return [refresh_db_note, refresh_db_time, refresh_db_remove, refresh_db_count]

def get_user(user_id, **kwargs):
    '''Method is to Get User Information'''
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return None
    return user

def get_user_username(user_id, **kwargs):
    '''Method is to Get UserName'''
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return None
    return user.username

def check_db_init():
    '''Make Sure DB is Initialized with Our Table before we start'''
    # Variable stores global INIT Flag for database
    current_app.logger.debug("Check If DB is Initalized Method was called")
    if not Config.DB_INIT:
        try:
            current_app.logger.info("Initalized Database")
            db.create_all()
            Config.DB_INIT = True
        except Exception as error:
            current_app.logger.error("{}".format(error))

def update_user_action_counter(user_id,action):
    '''Method to help keep track how many times a specfic user inserts or delete from the DB,Does not commit expects the calling function to commit'''

    if action == "insert":
        insert_counter = InsertCountMetric.query.filter_by(user_id=user_id).first()
        if insert_counter == None:
            db.session.add(
            InsertCountMetric(count=1, user_id=user_id))
        else:
            insert_counter.count = insert_counter.count + 1
    elif action == "delete":
        delete_counter = DeleteCountMetric.query.filter_by(user_id=user_id).first()
        if delete_counter == None:
            db.session.add(
            DeleteCountMetric(count=1, user_id=user_id))
        else:
            delete_counter.count = delete_counter.count + 1

def notes_insert(user_id, **kwargs):
    """ Method to handle insertion into DB
    """
    note_user = User.query.filter_by(id=user_id).first()
    if note_user is None:
        raise ValidationError("invalid User ID Provided")
    current_app.logger.debug("Database Insertion Method Called for {}".format(
        note_user.username))

    if "title" not in kwargs:
        raise ValidationError(
            "Could not obtain any Note Title from input parameter")

    if "note" not in kwargs:
        raise ValidationError(
            "Could not obtain any Note Text from input parameter")

    if "insertime" not in kwargs:
        raise ValidationError(
            "Could not obtain any Note InsertTime from input parameter")

    # Check if Title already Exists
    note = note_read(note_user.id, title=kwargs["title"])
    if note is not None:
        note.note = kwargs["note"]
        note.timestamp = kwargs["insertime"]
        update_user_action_counter(user_id,"insert")
        db.session.commit()
    else:
        db.session.add(
            Note(title=kwargs["title"], note=kwargs["note"], user_id=note_user.id))
        update_user_action_counter(user_id,"insert")
        db.session.commit()

def notes_delete(user_id, note_id, **kwargs):
    """ Method to handle deletion from db
    """

    note_user = User.query.filter_by(id=user_id).first()
    if note_user is None:
        raise ValidationError("invalid User ID Provided")
    current_app.logger.debug("Database Deletion method called for UserID {})".format(
        note_user.username))

    notes = note_read(user_id, note_id)
    if notes is None:
        current_app.logger.debug("Could not delete note_id:{} for user {})".format(
            note_id, note_user.username))
        return {"status": "BAD"}
    
    db.session.delete(notes)
    update_user_action_counter(user_id,"delete")
    db.session.commit()
    return {"status": "OK"}

def create_user(firstname, **kwargs):
    '''Method is Used to Create a User in The DB'''
    check_db_init()
    current_app.logger.debug("User Creation Method Called")
    if "username" not in kwargs:
        username = "{}{}".format(firstname, randrange(0, 100))
    else:
        username = kwargs["username"]

    #Check if User Already Exists
    user = User.query.filter_by(username=username).first()
    if user is None:
        if "id" in kwargs:
            # Try to set ID if provided
            db.session.add(
                User(firstname=firstname, username=username, id=kwargs["id"]))
        else:       
            db.session.add(User(firstname=firstname, username=username))
    else:
        current_app.logger.debug("User with Username {} already exists, will skip creation".format("username"))

    try:
        db.session.commit()
    except Exception as error:
        current_app.logger.error("{}".format(error))
        return None
        
    created_user = User.query.filter_by(username=username).first()
    return_dict = {"id": created_user.id, "username": username}
    return return_dict
  
def custom_render_template(*args, **kwargs):
    '''Custom Render Template Function to insert extra values'''
    try:
        kwargs["logged_in_user"] = current_app.config["authenticated_username"]
    except:
        pass
    return render_template(*args, **kwargs)

def custom_authmodule(route_func):
    '''Module is a method we use to simulate different kinds of authentication options'''
    def setauthenticated_user(user_id, username):
        '''Set Authenticated User Credentials'''
        current_app.config["authenticated_id"] = user_id
        current_app.config["authenticated_username"] = username
        current_app.config["authenticated"] = True

    @wraps(route_func)
    def user_authentication_valid(*args, **kwargs):
        # To-do Add methods for validation
        current_app.logger.debug("Check Authentication Validity")
        kwargs["authenticated_user_id"] = current_app.config["authenticated_id"]
        kwargs["authenticated_username"] = current_app.config["authenticated_username"]
        kwargs["authenticated"] = True
        return route_func(*args, **kwargs)

    def user_already_logged_in():
        '''Check if user already logged in'''
        current_app.logger.debug("check if User is already logged in")

        try:
            user_id = request.cookies.get("{}-user_id".format(
                current_app.config["SESSION_COOKIE_HEADER"]))
        except:
            pass

        if user_id is not None:
            return True

        if "authenticated" in current_app.config:
            if current_app.config["authenticated"]:
                return True
        return False

    @wraps(route_func)
    def decorated_view(*args, **kwargs):
        return route_func(*args, **kwargs)

    @wraps(route_func)
    def no_authentication(*args, **kwargs):
        '''Module assumes no authentication is in use'''

        # Check if user already logged in
        if user_already_logged_in():
            return user_authentication_valid(*args, **kwargs)

        current_app.logger.error(
            "Application is working with no Authentication, Will create a default Administrator user")
        user_dict = create_user(firstname="Administrator",
                                id=1, username="Administrator")
        kwargs["authenticated_user"] = "Administrator"
        kwargs["authenticated"] = True
        kwargs["authenticated_user_id"] = user_dict["id"]
        kwargs["authenticated_username"] = user_dict["username"]
        setauthenticated_user(user_dict["id"], user_dict["username"])
        return route_func(*args, **kwargs)

    if not Config.AUTH_INTEGRATION:
        return no_authentication
    else:
        return decorated_view


@bp.route('/base', methods=['GET', 'POST'])
@custom_authmodule
def base():
    """ Render Base HTML WebPage"""
    return custom_render_template('base2.html')


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@custom_authmodule
def index(**kwargs):
    '''Starting Index Page'''
    PostForm()
    fullurl = ""

    try:
        if not kwargs["authenticated"]:
            return redirect('/error-not-authenticated')
    except KeyError:
        return redirect('/error-not-authenticated')

    current_app.logger.debug("Loading Index Page")
    fullurl = request.base_url
    healthdown_url = fullurl.replace("/index", "/health_down")
    readydown_url = fullurl.replace("/index", "/ready_down")

    # Need to confirm health_down applied since / and /index might be diff
    if "health_down" not in healthdown_url:
        healthdown_url = "{}{}".format(healthdown_url, "health_down")
    if "ready_down" not in readydown_url:
        readydown_url = "{}{}".format(readydown_url, "ready_down")
    return custom_render_template('index.html')


@bp.route('/notes', methods=['GET', 'POST'])
@custom_authmodule
def notes(**kwargs):
    '''
    Function Handles Insert into with DB from Form/WebPage
    '''
    current_app.logger.debug("Database Page View Called")
    configs = myclassvariables()
    form = PostForm()
    fullurl = request.base_url

    user_id = kwargs["authenticated_user_id"]

    if form.validate_on_submit():
        current_app.logger.debug("Notes Page View - Submit was clicked")
        input_key = request.form["title"]
        input_value = request.form["text"]
        insertime = datetime.utcnow()

        output = notes_insert(user_id=user_id, insertime=insertime,
                              title=input_key, note=input_value)

        # if output["status"] == "error":
        # if output["error"] == DUPLICATE_KEY_DB_MESSAGE:
        #     flash(DUPLICATE_KEY_DB_MESSAGE, 'error')
        # notes_list = note_read(user_id)
        # return custom_render_template('notes.html', form=form, configs=configs, notes_list=notes_list)

    notes_list = note_read(user_id)
    return custom_render_template('notes.html', postform=form, configs=configs, notes_list=notes_list, user_id=user_id)


@bp.route('/insert', methods=['POST'])
@custom_authmodule
def insert(**kwargs):
    '''Insert into DB via API'''
    current_app.logger.debug("Insert API is being called")
    username = kwargs["authenticated_username"]
    id = kwargs["authenticated_user_id"]

    try:
        input_key = str(request.args.get("key"))
        input_value = str(request.args.get("value"))
        insertime = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    except:
        current_app.logger.error(
            "Error something wrong doing a DB insert on values")
        return make_response(jsonify({'Status': 'Server could not process Input Values'}), 503)

    output = notes_insert(user_id=id, insertime=insertime,
                          key=input_key, value=input_value)

    if output["status"] == "error":
        return make_response(jsonify({'Status': "{}".format(output["error"])}), 503)
    return make_response(jsonify({'Status': 'OK'}), 200)


@bp.route('/profile', methods=['GET'])
@custom_authmodule
def profile(**kwargs):
    '''Returns Profile and User Information'''
    id = kwargs["authenticated_user_id"]
    user = get_user(id)
    if user is not None:
        username = user.username
        firstname = user.firstname
        lastname = user.lastname
    else:
        username = None
        firstname = None
        lastname = None
    return custom_render_template('profile.html', username=username, firstname=firstname, lastname=lastname)


@bp.route('/configuration', methods=['GET'])
@custom_authmodule
def configuration(**kwargs):
    """ Render Configuration WebPage"""
    current_app.logger.debug("Obtain Application Configuration")
    configs = myclassvariables()
    return custom_render_template('configuration.html', configs=configs)


@bp.route('/health_status', methods=['GET', 'POST'])
@custom_authmodule
def health_status(**kwargs):
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

    return custom_render_template('health_status.html', form=form, configs=configs,
                                  health_url=healthdown_url, ready_url=readydown_url, ready=check_ready(), health=check_health())


@bp.route('/delete_title', methods=['GET', 'POST'])
@custom_authmodule
def delete_title(**kwargs):
    '''Method to remove key from DB'''

    try:
        value_remove = request.args.get("id")
        user_remove = request.args.get("user_id")
    except KeyError:
        current_app.logger.debug("Could not get values for deletion")

    notes_delete(user_remove, value_remove)
    return redirect('/notes')


@bp.route('/metrics', methods=['GET'])
@custom_authmodule
def metrics(**kwargs):
    '''Provides internal Application metrics to outside world'''

    current_app.logger.info("Metric URL Was Called")
    # Provide Some Metrics to External Platforms
    user_id = kwargs["authenticated_user_id"]

    counts = note_count(user_id)
    if counts is None:
        counts = 0

    db_inserts = insert_statement_count(user_id)
    if db_inserts is None:
        db_inserts = 0

    db_deletes = delete_statement_count(user_id)
    if db_deletes is None:
        db_deletes = 0
    response = make_response(
    """Current Metrics for user: {}\nCurrent Notes {}\nTotal_Insert_Statements {}\nTotal_Remove_Statements {}\n""".format(
        get_user_username(user_id),counts, db_inserts, db_deletes), 200)
    response.content_type = "text/plain"
    return response


@bp.route('/health', methods=['GET'])
@custom_authmodule
def health(**kwargs):
    '''Provide Application Health Status to the Outside World'''
    if check_health():
        return make_response(jsonify({'Status': 'OK'}), 200)
    return make_response(jsonify({'Status': 'Unavailable'}), 503)


@bp.route('/ready', methods=['GET'])
@custom_authmodule
def ready(**kwargs):
    '''Provide Application Ready Status to the Outside World'''
    if check_ready():
        return make_response(jsonify({'Status': 'Ready'}), 200)
    return make_response(jsonify({'Status': 'Unavailable'}), 503)


@bp.route('/health_down', methods=['GET', 'POST'])
@custom_authmodule
def health_down(**kwargs):
    '''Set Application Health down'''
    global HEALTH_STATUS_OK
    value = request.args.get("status")
    if value == "down":
        HEALTH_STATUS_OK = False
    else:
        HEALTH_STATUS_OK = True
    return redirect('/health_status')


@bp.route('/ready_down', methods=['GET'])
@custom_authmodule
def ready_down(**kwargs):
    '''Set Application Ready down'''
    global READY_STATUS_OK
    value = request.args.get("status")
    if value == "down":
        READY_STATUS_OK = False
    else:
        READY_STATUS_OK = True
    return redirect('/health_status')


@bp.route('/error-not-authenticated', methods=['GET'])
def display_unuauthenticated():
    '''Display Unauthenticated Error Page'''
    return render_template('unknown-user.html')
