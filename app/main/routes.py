from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required
from app import db
from app.main import bp
from app.main.forms import PostForm
from app.models import KeyStore
from config import Config



@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    form = PostForm()
    message = "Messages: "
    db_value = {}
    db_time = {}
    configs = Config.myclassvariables()

    stored_values={}
    if not Config.DB_INIT:
        try:
            db.create_all()
        except:
            pass
        Config.DB_INIT = True;
    stored_values = KeyStore.query.all()
    for val in stored_values:
        db_time.update({val.key:val.timestamp})
        db_value.update({val.key:val.value})

        print(val.key)
        print(val.value)
        print(val.timestamp)

    if form.validate_on_submit():
        key = request.form["key"]
        value = request.form["value"]
        insertime = datetime.utcnow()

        #Check if Key Already Exists
        if KeyStore.query.filter_by(key=key).first() is None:
            temp = KeyStore(timestamp=insertime, key=request.form["key"], value=request.form["value"])
            db.session.add(temp)
            db.session.commit()
            message = "Messages: Key {} Added".format(request.form["key"])
        else:
            flash('Value already exists for key {}'.format(key))
            message = "Key {} Added".format(request.form["key"])
            return render_template('index.html', form=form, configs=configs,message=message,
            db_value=db_value,db_time=db_time)

        #if value_remove is not None:
            #Check if key is in DB
        #    tempkey = KeyStore.query.filter_by(key=value_remove).first()
        #    if tempkey is not None:
        #        db.session.remove(tempkey)
        #key = KeyStore.query.filter_by(key=form.key.data).first()
        #value = KeyStore.query.filter_by(value=form.value.data).first()

        #return redirect('/index')
        return render_template('index.html', form=form, configs=configs,message=message,
            db_value=db_value,db_time=db_time)
    
    return render_template('index.html', form=form, configs=configs,message=message,
            db_value=db_value,db_time=db_time)

@bp.route('/Database', methods=['GET', 'POST'])
def db_view():
    return """  
    """