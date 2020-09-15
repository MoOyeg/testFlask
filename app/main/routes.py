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

health_status_ok = True
ready_status_ok= True
counter_db_inserted = 0
counter_db_removed = 0
counter_db_available = 0


def check_health():
    #Nothing Fancy will Store Application Health in Variable for now
    if health_status_ok:
        print("Checking if Application is Healthy: Application is Healthy", file=sys.stderr)
        return True
    else:
        print("Checking if Application is Healthy: Application is Unhealthy", file=sys.stderr)
        return False

def check_ready():
    #To Check Readiness we will attempt to add and remove from the db
    insertime = datetime.utcnow()
    if ready_status_ok:
        print("Checking if Application is Ready: Application is Ready", file=sys.stderr)
        return True
    else:
        print("Checking if Application is Ready: Application is not Ready", file=sys.stderr)
        return False
    
    try:
        temp = KeyStore(timestamp=insertime, key="test123", value="test123")
        db.session.add(temp)
        db.session.commit()
    except:
        print("Application Not Ready we could not insert into Database", file=sys.stderr)
        return False
    
    try:
        tempkey = KeyStore.query.filter_by(key="test123").first()
        db.session.delete(tempkey)
        db.session.commit()
    except:
        print("Application Not Ready we could not remove from Database", file=sys.stderr)
        return False

    return True
    

def refresh_db(url):
    form = PostForm()
    stored_values={}
    db_value = {}
    db_time = {}
    db_remove = {}
    count = 0

    url=url.replace("/index","")
    stored_values = KeyStore.query.all()
    for val in stored_values:
        db_time.update({val.key:val.timestamp})
        db_value.update({val.key:val.value})
        db_remove.update({val.key:"{}{}?key={}".format(url,url_for('main.db_remove'),val.key)})
        count += 1
    return [db_value, db_time, db_remove, count]


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    form = PostForm()
    fullurl = ""
    db_value = {}
    db_time = {}
    db_remove = {}
    configs = myclassvariables()
    fullurl = request.base_url
    healthdown_url=fullurl.replace("/index","/health_down")
    readydown_url=fullurl.replace("/index","/ready_down")
    
    #Need to confirm health_down applied since / and /index might be diff
    if "health_down" not in healthdown_url:
        healthdown_url = "{}{}".format(healthdown_url,"health_down")
    if "ready_down" not in readydown_url:
        readydown_url = "{}{}".format(readydown_url,"ready_down")

    global counter_db_inserted

    if not Config.DB_INIT:
        try:
            db.create_all()
        except:
            pass
        Config.DB_INIT = True;
   
    if form.validate_on_submit():
        key = request.form["key"]
        value = request.form["value"]
        insertime = datetime.utcnow()

        #Check if Key Already Exists
        if KeyStore.query.filter_by(key=key).first() is None:
            temp = KeyStore(timestamp=insertime, key=request.form["key"], value=request.form["value"])
            db.session.add(temp)
            db.session.commit()
            counter_db_inserted += 1
        else:
            print("key - {}: Already in DB".format(key), file=sys.stderr)
            #flash('Value already exists for key {}'.format(key))
            temp_db = refresh_db(fullurl)
            return render_template('index.html', form=form, configs=configs,
            db_value=temp_db[0],db_time=temp_db[1], db_remove=temp_db[2],
            health_url=healthdown_url,ready_url=readydown_url,ready=str(check_ready()),health=str(check_health()))
 
        temp_db = refresh_db(fullurl)
        return render_template('index.html', form=form, configs=configs,
            db_value=temp_db[0],db_time=temp_db[1], db_remove=temp_db[2],
            health_url=healthdown_url,ready_url=readydown_url,ready=str(check_ready()),health=str(check_health()))
    
    temp_db = refresh_db(fullurl)
    return render_template('index.html', form=form, configs=configs,
            db_value=temp_db[0],db_time=temp_db[1], db_remove=temp_db[2],
            health_url=healthdown_url,ready_url=readydown_url,ready=str(check_ready()),health=str(check_health()))

@bp.route('/remove', methods=['GET', 'POST'])
def db_remove():
    global counter_db_removed

    value_remove=request.args.get("key")
    if value_remove is not None:
        #Check if key is in DB
        tempkey = KeyStore.query.filter_by(key=value_remove).first()
        if tempkey is not None:
            db.session.delete(tempkey)
            db.session.commit()
            counter_db_removed += 1
    return redirect('/index')
    
@bp.route('/metrics', methods=['GET'])
def metrics():
    count = 0
    global counter_db_available
    global counter_db_inserted
    global counter_db_removed
    
    print("Metrics Been Scraped", file=sys.stderr)
    #Provide Some Metrics to External Platforms
    if Config.DB_INIT:
        stored_values = KeyStore.query.all()
        for val in stored_values:
            count += 1
        counter_db_available = count
        # return make_response(jsonify({"Available Keys":"{}".format(counter_db_available)},
        # {"Total Insert Statements":"{}".format(counter_db_inserted)},
        # {"Total Remove Statements":"{}".format(counter_db_removed)}))
        response=make_response("Available_Keys {}\nTotal_Insert_Statements {}\nTotal_Remove_Statements {}".format(counter_db_available,
        counter_db_inserted,counter_db_removed), 200)
        response.content_type = "text/plain"
        return response
    else:
        response=make_response("Available_Keys {}\nTotal_Insert_Statements {}\nTotal_Remove_Statements {}".format(counter_db_available,
        counter_db_inserted,counter_db_removed), 200)
        response.content_type = "text/plain"
        return response
        # return make_response(jsonify({"Available Keys":""},
        # {"Total Insert Statements":""},
        # {"Total Remove Statements":""}))


@bp.route('/health', methods=['GET'])
def health():
    #Provide Application Health Status to the Outside World
    if check_health():
        return make_response(jsonify({'Status': 'OK'}), 200)
    else:
        return make_response(jsonify({'Status': 'Unavailable'}), 503)

@bp.route('/ready', methods=['GET'])
def ready():
    #Provide Application Ready Status to the Outside World
    if check_ready():
        return make_response(jsonify({'Status': 'Ready'}), 200)
    else:
        return make_response(jsonify({'Status': 'Unavailable'}), 503)


@bp.route('/health_down', methods=['GET','POST'])
def health_down():
    global health_status_ok
    value=request.args.get("status")
    if value == "down":
        health_status_ok = False
    else:
        health_status_ok = True
    return redirect('/index')


@bp.route('/ready_down', methods=['GET'])
def ready_down():
    global ready_status_ok
    value=request.args.get("status")
    if value == "down":
        ready_status_ok = False
    else:
        ready_status_ok = True

    return redirect('/index')


@bp.route('/insert', methods=['POST'])
def insert():    
    try:
        temp_key = request.args.get("key")
        temp_value = request.args.get("value")
        insertime = datetime.utcnow()
        
        #Check if Key Already Exists
        if KeyStore.query.filter_by(key=temp_key).first() is None:
            temp = KeyStore(timestamp=insertime, key=temp_key, value=temp_value)
            db.session.add(temp)
            db.session.commit()
            counter_db_inserted += 1
            return make_response(jsonify({'Status': 'OK'}), 200)
        else:
            print("key - {}: Already in DB".format(temp_key), file=sys.stderr)
            return make_response(jsonify({'Status': 'Duplicate Key Could Not Be Added'}), 503)  
    except:
        return make_response(jsonify({'Status': 'Server Could Not Process'}), 503)

        
 