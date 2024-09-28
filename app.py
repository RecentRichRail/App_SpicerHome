import logging
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
import os
from sqlalchemy.exc import SQLAlchemyError
import json
from dotenv import load_dotenv
import uuid

from models import db, User, CommandsModel, PermissionsModel
# from db import db
# CommandsModel.__table__.create(db.engine)

# from db import db
# import resources
from resources.external.external import external_blueprint
from resources.external.auth import auth as external_auth
from resources.internal.auth import auth as internal_auth
from resources.internal.internal import internal_blueprint
from resources.internal.admin import admin_blueprint
from resources.api.search import api_blueprint

# from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "external_auth.login"

logging.basicConfig(level=logging.DEBUG)

# short_session_cookie_name = os.environ.get('short_session_cookie_name')
host_port = os.environ.get('host_port')
# app.authentication_server = os.environ.get('authentication_server')
app.mysql_database_api = os.environ.get('mysql_database_api')
app.allow_logging = os.environ.get('allow_logging')
app.public_verification_key = os.environ.get('public_verification_key')
app.BRAVE_API_KEY = os.environ.get('BRAVE_API_KEY')
app.dev_server = os.environ.get('dev_server')
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

app.config["SQLALCHEMY_DB_HOST"] = os.environ.get('SQLALCHEMY_DB_HOST')
app.config["SQLALCHEMY_DB_USER"] = os.environ.get('SQLALCHEMY_DB_USER')
app.config["SQLALCHEMY_DB_PASSWORD"] = os.environ.get('SQLALCHEMY_DB_PASSWORD')
app.config["SQLALCHEMY_DB_NAME"] = os.environ.get('SQLALCHEMY_DB_NAME')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PROPAGATE_EXCEPTIONS"] = True

if app.config["SQLALCHEMY_DB_HOST"] == 'sqlite':
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{app.config['SQLALCHEMY_DB_USER']}:{app.config['SQLALCHEMY_DB_PASSWORD']}@{app.config['SQLALCHEMY_DB_HOST']}/{app.config['SQLALCHEMY_DB_NAME']}"

app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT"))
app.config["MAIL_FROM"] = os.getenv("MAIL_FROM")
    
db.init_app(app)
with app.app_context():
    # try:
    #     CommandsModel.__table__.create(db.engine)
    # except SQLAlchemyError:
    #     print("Table Exists")
    db.create_all()
    print("Creating database.")

    try:
        with open('src/commands.json', 'r') as file:
            commands_data = json.load(file)
            logging.error(f"commands.json file was loaded.")
    except FileNotFoundError:
        logging.error(f"{os.system('pwd')} - Could not find commands.json file.")
        commands_data = {'commands': []}

    for single_command in commands_data['commands']:
        for single_command_single_prefix in single_command['prefix']:
            command_for_data = single_command
            command_for_data['prefix'] = single_command_single_prefix
            cmd_query = CommandsModel.query.filter_by(prefix=command_for_data['prefix']).first()
            command_model = CommandsModel(category=command_for_data['category'], prefix=command_for_data['prefix'], url=command_for_data['url'], search_url=command_for_data.get('search_url'), permission_level=command_for_data.get('permission_level'))
            if not cmd_query:
                try:
                    if not cmd_query:
                        db.session.add(command_model)
                        db.session.commit()
                        single_command_single_category = command_for_data['category']
                        print(f"Command created successfully - {single_command_single_category} - {single_command_single_prefix}")
                except SQLAlchemyError as e:
                    print(e)
            else:
                print("Command already exists")

    if User.query.count() == 0:
        cmd_query = CommandsModel.query.filter_by(category="default_search").first()
        user = User(name='spicerhome-admin', username='spicerhome-admin', email='admin@spicerhome.net', default_search_id=cmd_query.id)
        
        try:
            db.session.add(user)
            db.session.commit()  # Commit to get the user.id

            # Retrieve the user again to ensure the id is set
            user = User.query.filter_by(username='spicerhome-admin').first()
            
            if user:
                user_permissions = [
                    PermissionsModel(user_id=user.id, permission_name="commands", permission_level=0),
                    PermissionsModel(user_id=user.id, permission_name="admin", permission_level=0)
                ]
                
                for permission in user_permissions:
                    db.session.add(permission)
                db.session.commit()
                logging.info('User created successfully')
            else:
                logging.error('User creation failed, user not found after commit')
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Error creating user: {e}")

@login_manager.user_loader
def load_user(user_uid):
    user = User.query.filter_by(uid=user_uid).first()
    # if user:
        # print(user.permissions)
    return user


@app.context_processor
def utility_processor():
    def random_id():
        return uuid.uuid4().hex

    return dict(random_id=random_id)

# from flask import Flask, render_template, flash
# from flask_login import LoginManager
# from flask_migrate import Migrate

# from models import db, User
# from auth.views import auth

app.register_blueprint(external_blueprint, url_prefix="/external")
app.register_blueprint(internal_blueprint, url_prefix="/internal")
app.register_blueprint(external_auth, url_prefix="/external/auth")
app.register_blueprint(internal_auth, url_prefix="/internal/auth")
app.register_blueprint(admin_blueprint, url_prefix="/internal/admin")
app.register_blueprint(api_blueprint, url_prefix="/apiv1")

# @app.route("/")
# @login_required
# def index():
#     """The main homepage. This is a stub since it's a demo project."""
#     return render_template("index.html")

@app.route('/')
@login_required
def redirect_to_url():
    return redirect(url_for("internal.internal_search"))

@app.route('/search=<user_query>')
@login_required
def redirect_old_search_command(user_query):
    return redirect(f"/internal/search?q={user_query}")

@app.route('/external/status', methods=['GET'])
def status():
    return {"status": 200}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=host_port, debug=True)