from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, make_response
from flask_login import current_user, login_required
from app import db
from app.main import bp
from app.main.forms import PostForm
from app.models import KeyStore
from config import Config
from config import myclassvariables

health_status_ok = True
counter_db_inserted = 0
counter_db_removed = 0
counter_db_available = 0

def check_health():
    if health_status_ok:
        return True
    else:
        return False


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

    
    if not Config.DB_INIT:
        try:
            db.create_all()
        except:
            pass
        Config.DB_INIT = True;
   
    
    if form.validate_on_submit():
        key = request.form["key"]
        value = request.form["value"]
        fullurl = request.base_url
        insertime = datetime.utcnow()

        #Check if Key Already Exists
        if KeyStore.query.filter_by(key=key).first() is None:
            temp = KeyStore(timestamp=insertime, key=request.form["key"], value=request.form["value"])
            db.session.add(temp)
            db.session.commit()
            counter_db_inserted += 1
        else:
            flash('Value already exists for key {}'.format(key))
            temp_db = refresh_db(fullurl)
            return render_template('index.html', form=form, configs=configs,
            db_value=temp_db[0],db_time=temp_db[1], db_remove=temp_db[2])
 
        temp_db = refresh_db(fullurl)
        return render_template('index.html', form=form, configs=configs,
            db_value=temp_db[0],db_time=temp_db[1], db_remove=temp_db[2])
    
    temp_db = refresh_db(fullurl)
    return render_template('index.html', form=form, configs=configs,
            db_value=temp_db[0],db_time=temp_db[1], db_remove=temp_db[2])


@bp.route('/remove', methods=['GET', 'POST'])
def db_remove():
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
    #Provide Some Metrics to External Platforms
    temp_db = refresh_db
    counter_db_available = temp_db[3]
    return "Available Keys: {}, Total Insert Statements: {}, Total Remove Statements: {}".format(
        counter_db_available,counter_db_inserted,counter_db_removed)

@bp.route('/health', methods=['GET'])
def health():
    #Provide Application Health Status to the Outside World
    if check_health:
        return make_response(jsonify({'Status': 'OK'}), 200)
    else:
        return make_response(jsonify({'Status': 'Unavailable'}), 503)

