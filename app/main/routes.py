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
import requests
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
# Functions we want access maybe without authentication
ANONYMOUS_ACCESS_FUNCTIONS = ["ready"]
INDEX_COUNT = 0
INDEX_CALLED = "false"


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

def sum_total_insert_statement_count():
    sum = InsertCountMetric.query.with_entities(db.func.sum(InsertCountMetric.count).label('total')).first().total
    return sum

def sum_total_delete_statement_count():
    sum = DeleteCountMetric.query.with_entities(db.func.sum(DeleteCountMetric.count).label('total')).first().total
    return sum

def sum_note_count():
    sum = User.query.with_entities(db.func.sum(User.user_note_count).label('total')).first().total
    return sum

def note_count(user_id):
    '''Meant to return counts of user notes'''
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return None
    return user.user_note_count


def refresh_notes_view(url, user_id) -> list:
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


def get_user(user_id, **kwargs) -> User:
    '''Method is to Get User Information'''
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return None
    return user


def get_user_username(user_id, **kwargs) -> str:
    '''Method is to Get UserName'''
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return None
    return user.username


def get_user_by_authmethod(auth_method, username) -> User:
    user = User.query.filter_by(
        username=username, auth_method=auth_method).first()
    if user is None:
        return None
    return user


def check_db_init():
    '''Make Sure DB is Initialized with Our Tables before we start'''
    # Variable stores global INIT Flag for database
    current_app.logger.debug("Check If DB is Initalized Method was called")
    if not Config.DB_INIT:
        try:
            current_app.logger.info("Initalized Database")
            db.create_all()
            Config.DB_INIT = True
        except Exception as error:
            current_app.logger.error("{}".format(error))


def update_user_action_counter(user_id, action):
    '''Method to help keep track how many times a specfic user inserts or delete from the DB,Does not commit expects the calling function to commit'''

    if action == "insert":
        insert_counter = InsertCountMetric.query.filter_by(
            user_id=user_id).first()
        if insert_counter == None:
            db.session.add(
                InsertCountMetric(count=1, user_id=user_id))
        else:
            insert_counter.count = insert_counter.count + 1
    elif action == "delete":
        delete_counter = DeleteCountMetric.query.filter_by(
            user_id=user_id).first()
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
        update_user_action_counter(user_id, "insert")
        db.session.commit()
    else:
        db.session.add(
            Note(title=kwargs["title"], note=kwargs["note"], user_id=note_user.id))
        update_user_action_counter(user_id, "insert")
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
    update_user_action_counter(user_id, "delete")
    db.session.commit()
    return {"status": "OK"}


def create_user(firstname, **kwargs) -> User:
    '''Method is Used to Create a User in The DB'''
    current_app.logger.debug("User Creation Method Called")

    # Generate Username if not Provided
    if "username" not in kwargs:
        username = "{}{}".format(firstname, randrange(0, 100))
    else:
        username = kwargs["username"]

    # Set auth_method if not provided
    if "auth_method" not in kwargs:
        auth_method = "no_authentication"
    else:
        auth_method = kwargs["auth_method"]

    # Check if User Already Exists
    user = User.query.filter_by(
        username=username, auth_method=auth_method).first()
    if user is None:
        if "id" in kwargs:
            # Try to set ID if provided
            db.session.add(
                User(firstname=firstname, username=username, auth_method=auth_method, id=kwargs["id"]))
        else:
            db.session.add(
                User(firstname=firstname, username=username, auth_method=auth_method))
    else:
        current_app.logger.debug(
            "User with Username {} already exists, will skip creation".format("username"))

    try:
        db.session.commit()
    except Exception as error:
        current_app.logger.error("{}".format(error))
        return None

    created_user = User.query.filter_by(
        username=username, auth_method=auth_method).first()
    return created_user


def custom_logoutmodule(user, response) -> dict:
    '''Enables logout based on user auth_method specificed'''
    response = response
    error = ""
    info = ""
    redirect = False
    redirect_url = ""

    try:
        auth_method = user.auth_method
    except:
        current_app.logger.error(
            "Could not get error when trying to logout User")

    if auth_method == "openshift_oauth_proxy":
        redirect = True
        redirect_url = Config.OPENSHIFT_OAUTH_PROXY_SIGNIN_ENDPOINT

    return {"response": response,
            "error": error,
            "info": info,
            "redirect": redirect,
            "redirect_url": redirect_url}


def custom_authmodule(route_func):
    '''Module is a method we use to simulate different kinds of authentication options'''

    @wraps(route_func)
    def no_authentication(*args, **kwargs):
        '''Module assumes no authentication is in use'''
        check_db_init()
        # Check if user exists
        user = get_user_by_authmethod("no_authentication", "Administrator")
        if user is None:
            current_app.logger.error(
                "Application is working with no Authentication, Will create a default Administrator user")
            user = create_user(firstname="Administrator",
                               id=1, username="Administrator", auth_method="no_authentication")
        user = get_user_by_authmethod("no_authentication", "Administrator")
        kwargs["authenticated_user"] = user
        kwargs["authenticated"] = True
        return route_func(*args, **kwargs)

    @wraps(route_func)
    def openshift_oauth_proxy(*args, **kwargs):
        '''Oauth Authentication using OpenShift's integrated Oauth Proxy - https://github.com/MoOyeg/testFlask-Oauth-Proxy'''

        # Check if we can reach the oauth_proxy
        try:
            check_code = requests.get(
                Config.OPENSHIFT_OAUTH_PROXY_HEALTH_ENDPOINT)
        except:
            current_app.logger.error(
                "Openshift Oauth-Proxy was selected but we could not reach proxy server at {}".format(Config.OPENSHIFT_OAUTH_PROXY_HEALTH_ENDPOINT))
            current_app.logger.error(
                "We will Switch to using No Authentication")
            return no_authentication(*args, **kwargs)

        # Check if DB is initalized
        check_db_init()

        # Check if user already logged and if not redirect back to fullurl where proxy should be listening
        try:
            fullurl = request.base_url
            if request.authorization.username is None:
                return redirect(fullurl)
        except AttributeError:
            fullurl = request.base_url
            return redirect(fullurl)

        authenticated_username = request.authorization.username
        auth_method = "openshift_oauth_proxy"

        # Check if user already exists
        if get_user_by_authmethod(username=authenticated_username, auth_method=auth_method) is None:
            create_user(authenticated_username,
                        username=authenticated_username, auth_method=auth_method)

        # Get User Information
        User = get_user_by_authmethod(
            username=authenticated_username, auth_method=auth_method)
        kwargs["authenticated_user"] = User
        kwargs["authenticated"] = True
        return route_func(*args, **kwargs)

    @wraps(route_func)
    def anonymous_access(*args, **kwargs):
        current_app.logger.debug(
            "Anonymous access enabled for {}".format(route_func.__name__))
        return route_func(*args, **kwargs)

    if route_func.__name__ in Config.ANONYMOUS_ACCESS_FUNCTIONS:
        return anonymous_access

    if Config.AUTH_INTEGRATION.lower() == "false":
        return no_authentication

    if Config.AUTH_TYPE.lower() == "openshift_oauth_proxy":
        return openshift_oauth_proxy

    if Config.AUTH_TYPE.lower() == "":
        return no_authentication


@bp.route('/base', methods=['GET', 'POST'])
@custom_authmodule
def base():
    """ Render Base HTML WebPage"""
    return render_template('base2.html')


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@custom_authmodule
def index(**kwargs):
    '''Starting Index Page'''
    global INDEX_CALLED
    global INDEX_COUNT

    PostForm()
    fullurl = ""
    INDEX_COUNT += 1
    if INDEX_COUNT > 1:
        INDEX_CALLED = "true"
    try:
        if not kwargs["authenticated_user"]:
            return redirect('/error-not-authenticated')
    except KeyError:
        return redirect('/error-not-authenticated')

    authenticated_user = kwargs["authenticated_user"]
    current_app.logger.debug("Loading Index Page")
    fullurl = request.base_url
    healthdown_url = fullurl.replace("/index", "/health_down")
    readydown_url = fullurl.replace("/index", "/ready_down")

    # Need to confirm health_down applied since / and /index might be diff
    if "health_down" not in healthdown_url:
        healthdown_url = "{}{}".format(healthdown_url, "health_down")
    if "ready_down" not in readydown_url:
        readydown_url = "{}{}".format(readydown_url, "ready_down")
    return render_template('index.html', authenticated_user=authenticated_user, new_session=INDEX_CALLED)


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

    authenticated_user = kwargs["authenticated_user"]

    if form.validate_on_submit():
        current_app.logger.debug("Notes Page View - Submit was clicked")
        input_key = request.form["title"]
        input_value = request.form["text"]
        insertime = datetime.utcnow()

        output = notes_insert(user_id=authenticated_user.id, insertime=insertime,
                              title=input_key, note=input_value)

        # if output["status"] == "error":
        # if output["error"] == DUPLICATE_KEY_DB_MESSAGE:
        #     flash(DUPLICATE_KEY_DB_MESSAGE, 'error')
        # notes_list = note_read(user_id)
        # return render_template('notes.html', form=form, configs=configs, notes_list=notes_list)

    notes_list = note_read(authenticated_user.id)
    return render_template('notes.html', postform=form,
                           configs=configs, notes_list=notes_list,
                           authenticated_user=authenticated_user,
                           user_id=authenticated_user.id,
                           delete_url=url_for('main.delete_note'))


@bp.route('/insert', methods=['POST'])
@custom_authmodule
def insert(**kwargs):
    '''Insert into DB via API'''
    current_app.logger.debug("Insert API is being called")
    authenticated_user = kwargs["authenticated_user"]

    try:
        input_key = str(request.args.get("key"))
        input_value = str(request.args.get("value"))
        insertime = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    except:
        current_app.logger.error(
            "Error something wrong doing a DB insert on values")
        return make_response(jsonify({'Status': 'Server could not process Input Values'}), 503)

    output = notes_insert(user_id=authenticated_user.id, insertime=insertime,
                          key=input_key, value=input_value)

    if output["status"] == "error":
        return make_response(jsonify({'Status': "{}".format(output["error"])}), 503)
    return make_response(jsonify({'Status': 'OK'}), 200)


@bp.route('/profile', methods=['GET'])
@custom_authmodule
def profile(**kwargs):
    '''Returns Profile and User Information'''
    authenticated_user = kwargs["authenticated_user"]
    user = get_user(authenticated_user.id)
    if user is not None:
        username = user.username
        firstname = user.firstname
        lastname = user.lastname
    else:
        username = None
        firstname = None
        lastname = None
    return render_template('profile.html', username=username, firstname=firstname, lastname=lastname, authenticated_user=authenticated_user)


@bp.route('/configuration', methods=['GET'])
@custom_authmodule
def configuration(**kwargs):
    """ Render Configuration WebPage"""
    current_app.logger.debug("Obtain Application Configuration")
    authenticated_user = kwargs["authenticated_user"]
    configs = myclassvariables()
    return render_template('configuration.html', configs=configs, authenticated_user=authenticated_user)


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
    authenticated_user = kwargs["authenticated_user"]

    # Need to confirm health_down applied since / and /index might be diff
    if "health_down" not in healthdown_url:
        healthdown_url = "{}{}".format(healthdown_url, "health_down")
    if "ready_down" not in readydown_url:
        readydown_url = "{}{}".format(readydown_url, "ready_down")

    return render_template('health_status.html', form=form, configs=configs,
                           health_url=healthdown_url, ready_url=readydown_url, ready=check_ready(), health=check_health(), authenticated_user=authenticated_user)


@bp.route('/delete_note', methods=['GET', 'POST'])
@custom_authmodule
def delete_note(**kwargs):
    '''Method to remove key from DB'''

    authenticated_user = kwargs["authenticated_user"]
    try:
        value_remove = request.args.get("id")
        user_remove = request.args.get("user_id")
    except KeyError:
        current_app.logger.debug("Could not get values for deletion")

    try:
        notes_delete(user_remove, value_remove)
    except:
        pass

    return redirect('/notes')

# @bp.route('/get_note', methods=['GET', 'POST'])
# @custom_authmodule
# def get_note(**kwargs):
#     '''Get a note via api'''

#     authenticated_user = kwargs["authenticated_user"]
#     try:
#         note_id = request.args.get("id")
#         user_id = request.args.get("user_id")
#     except KeyError:
#         current_app.logger.debug("Could not get values for note")

#     try:
#         notes_read(user_id, note_id)
#     except:
#         pass

#     return redirect('/notes')

@bp.route('/metrics', methods=['GET'])
@custom_authmodule
def metrics(**kwargs):
    '''Provides internal Application metrics to outside world'''

    current_app.logger.info("Metric URL Was Called")
    # Provide Some Metrics to External Platforms
    if "authenticated_user" in kwargs:
        authenticated_user = kwargs["authenticated_user"]
        counts = note_count(authenticated_user.id)
        db_inserts = insert_statement_count(authenticated_user.id)
        db_deletes = delete_statement_count(authenticated_user.id)
    else:
        try:
            counts = sum_note_count()
            db_inserts = sum_total_insert_statement_count()
            db_deletes = sum_total_delete_statement_count()
        except:
            pass
    try:            
        if counts is None:
            counts = 0
        if db_inserts is None:
            db_inserts = 0
        if db_deletes is None:
            db_deletes = 0
    except:
        pass

    if "authenticated_user" in kwargs:
        response = make_response(
            """Current Metrics for user: {}\nCurrent Notes {}\nTotal_Insert_Statements {}\nTotal_Remove_Statements {}\n""".format(
                get_user_username(authenticated_user.id), counts, db_inserts, db_deletes), 200)
    else:
        response = make_response(
            """Total Metrics for platform:\n Current Notes {}\nTotal_Insert_Statements {}\nTotal_Remove_Statements {}\n""".format(
            counts, db_inserts, db_deletes), 200)
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


@bp.route('/logout', methods=['GET'])
@custom_authmodule
def logout(**kwargs):
    global INDEX_CALLED
    global INDEX_COUNT

    try:
        if not kwargs["authenticated_user"]:
            return redirect('/error-not-authenticated')
        user = kwargs["authenticated_user"]
    except KeyError:
        return redirect('/error-not-authenticated')

    try:
        user_id = request.args.get("user_id")
    except KeyError:
        return redirect('/error-not-authenticated')

    if str(user_id) != str(user.id):
        current_app.logger.debug(
            "User ID Provided did not match authenticated user ID")
        return redirect('/error-not-authenticated')

    INDEX_CALLED = "false"
    INDEX_COUNT = 0

    
    resp = make_response(render_template('logout.html'))
    updated_resp = custom_logoutmodule(kwargs["authenticated_user"], resp)
    if updated_resp["redirect"]:
        return redirect(updated_resp["redirect_url"])
    else:
        return updated_resp["response"]


@bp.route('/error-not-authenticated', methods=['GET'])
def display_unuauthenticated():
    '''Display Unauthenticated Error Page'''
    return render_template('unknown-user.html')
