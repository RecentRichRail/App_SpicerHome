import logging
import requests
from flask import Flask, render_template, redirect, url_for, request, session, make_response
from flask_login import LoginManager, login_user, login_required, current_user, logout_user, UserMixin
from flask_migrate import Migrate
import jinja_partials
import os
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import json
from dotenv import load_dotenv
import uuid
import traceback
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session

from resources.utils.util import send_email
from models import db, User, CommandsModel, PermissionsModel, NetworkPasswordModel, ChoresUser
# from resources.utils import util
# from db import db
# CommandsModel.__table__.create(db.engine)

# from db import db
# import resources
from resources.external.external import external_blueprint
# from resources.external.auth import auth as external_auth
# from resources.internal.auth import auth as internal_auth
from resources.internal.internal import internal_blueprint
from resources.internal.admin import admin_blueprint
from resources.api.search import api_blueprint
from resources.internal.chores import chores_blueprint

# from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy.pool import QueuePool

load_dotenv()

app = Flask(__name__)
jinja_partials.register_extensions(app)

login_manager = LoginManager()
login_manager.init_app(app)
migrate = Migrate(app, db)

# login_manager.login_view = "external_auth.login"

logging.basicConfig(level=logging.DEBUG)

# short_session_cookie_name = os.environ.get('short_session_cookie_name')
host_port = os.environ.get('host_port')
# app.authentication_server = os.environ.get('authentication_server')
app.mysql_database_api = os.environ.get('mysql_database_api')
app.allow_logging = os.environ.get('allow_logging')
app.public_verification_key = os.environ.get('public_verification_key')
app.BRAVE_API_KEY = os.environ.get('BRAVE_API_KEY')
app.dev_server = os.environ.get('dev_server')
app.server_env = os.environ.get('server_env')
app.router_API_Key = os.environ.get('router_API_Key')
app.CF_Access_Client_Id = os.environ.get('CF-Access-Client-Id')
app.CF_Access_Client_Secret = os.environ.get('CF-Access-Client-Secret')
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

if app.server_env == 'dev':
    # If current dir is not the same as the script dir, change to the script dir
    if os.getcwd() != os.path.dirname(os.path.realpath(__file__)):
        os.chdir(os.path.dirname(os.path.realpath(__file__)))

CLOUDFLARE_TEAM_NAME = "SpicerHome"  # Replace with your team name
IDENTITY_ENDPOINT = f"https://{CLOUDFLARE_TEAM_NAME}.cloudflareaccess.com/cdn-cgi/access/get-identity"

app.config["SQLALCHEMY_DB_HOST"] = os.environ.get('SQLALCHEMY_DB_HOST')
app.config["SQLALCHEMY_DB_USER"] = os.environ.get('SQLALCHEMY_DB_USER')
app.config["SQLALCHEMY_DB_PASSWORD"] = os.environ.get('SQLALCHEMY_DB_PASSWORD')
app.config["SQLALCHEMY_DB_NAME"] = os.environ.get('SQLALCHEMY_DB_NAME')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PROPAGATE_EXCEPTIONS"] = True

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 30,
    "pool_recycle": 1800,  # Recycle connections after 30 minutes
}

if app.config["SQLALCHEMY_DB_HOST"] == 'sqlite':
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{app.config['SQLALCHEMY_DB_USER']}:{app.config['SQLALCHEMY_DB_PASSWORD']}@{app.config['SQLALCHEMY_DB_HOST']}/{app.config['SQLALCHEMY_DB_NAME']}"
    app.config['SESSION_TYPE'] = 'sqlalchemy'
    app.config['SESSION_SQLALCHEMY'] = db
    app.config['SESSION_SQLALCHEMY_TABLE'] = 'user_session_data'
    app.config['SESSION_COOKIE_SECURE'] = True

app.config["DEVELOPER_EMAIL"] = os.getenv("DEVELOPER_EMAIL")
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT"))
app.config["MAIL_FROM"] = os.getenv("MAIL_FROM")

# class CFUser(UserMixin):
#     def __init__(self, identity):
#         self.uid = identity.get("user_uuid")
#         self.user_uuid = identity.get("user_uuid")
#         self.email = identity.get("email")
#         self.idp = identity.get("idp")
#         self.geo = identity.get("geo")
#         self.devicePosture = identity.get("devicePosture")
#         self.account_id = identity.get("account_id")
#         self.iat = identity.get("iat")
#         self.ip = identity.get("ip")
#         self.auth_status = identity.get("auth_status")
#         self.common_name = identity.get("common_name")
#         self.service_token_id = identity.get("service_token_id")
#         self.service_token_status = identity.get("service_token_status")
#         self.is_warp = identity.get("is_warp")
#         self.is_gateway = identity.get("is_gateway")
#         self.gateway_account_id = identity.get("gateway_account_id")
#         self.device_id = identity.get("device_id")
#         self.version = identity.get("version")
#         self.device_sessions = identity.get("device_sessions")

#     @staticmethod
#     def from_identity(identity):
#         return CFUser(identity)

db.init_app(app)
with app.app_context():
    # try:
    #     CommandsModel.__table__.create(db.engine)
    # except SQLAlchemyError:
    #     print("Table Exists")
    db.create_all()
    Session(app)
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

# def get_user():
#     """
#     Retrieve the most up-to-date user data, preferring CFUser if available.
#     """
#     identity = get_identity_from_cloudflare()
#     if identity:
#         return CFUser.from_identity(identity)
    
#     # Fallback to User table
#     return User.query.filter_by(uid=session.get("user_uuid")).first()

def get_identity_from_cloudflare():
    """Fetch user's identity from Cloudflare."""
    cf_authorization = request.cookies.get("CF_Authorization")
    session['cloudflare']['cf_authorization'] = cf_authorization
    if not cf_authorization:
        logging.error("CF_Authorization cookie missing.")
        return None

    try:
        response = requests.get(
            IDENTITY_ENDPOINT,
            headers={"cookie": f"CF_Authorization={cf_authorization}"}
        )
        response.raise_for_status()
        identity = response.json()
        logging.info(f"Fetched identity for user: {identity.get('email')}")
        return identity
    except requests.RequestException as e:
        logging.error(f"Error fetching Cloudflare identity: {e}")
        return None

# def create_user():
#     if not current_user:
#         return redirect(url_for("external_auth.login"))

#     # Extract form data
#     name = request.form.get("name")
#     username = request.form.get("username")
#     email = request.form.get("email")

#     # Fetch default search command
#     cmd_query = CommandsModel.query.filter_by(category="default_search").first()
#     if not cmd_query:
#         return {"error": "Default search command not found"}, 500

#     # Create new user instance
#     user = User(
#         uid=current_user.uid,
#         name=name,
#         username=username,
#         email=email,
#         default_search_id=cmd_query.id,
#     )

#     try:
#         db.session.add(user)
#         db.session.commit()
#     except IntegrityError as e:
#         logging.error(f"Error adding user: {e}")
#         return render_template(
#             "auth/_partials/user_creation_form.html",
#             error="That username or email address is already in use. Please enter a different one.",
#         )

#     # Assign permissions to the newly created user
#     user_model = User.query.filter_by(username=username).first()
#     if not user_model:
#         return {"error": "User creation failed. User not found after creation."}, 500

#     user_permissions = PermissionsModel(
#         user_id=user_model.id, 
#         permission_name="commands", 
#         permission_level=999
#     )
#     try:
#         db.session.add(user_permissions)
#         db.session.commit()
#     except IntegrityError as e:
#         logging.error(f"Error adding user permissions: {e}")
#         return render_template(
#             "auth/_partials/user_creation_form.html",
#             error="Error creating user account. Please try again later.",
#         )

#     # Handle network password creation and router API interaction
#     try:
#         router_api_key = app.config.get("ROUTER_API_KEY")
#         cf_client_secret = app.config.get("CF_ACCESS_CLIENT_SECRET")
#         cf_client_id = app.config.get("CF_ACCESS_CLIENT_ID")
        
#         if not (router_api_key and cf_client_secret and cf_client_id):
#             return {"error": "Missing API credentials for router"}, 500

#         headers = {
#             'x-api-key': router_api_key,
#             'accept': 'application/json',
#             'CF-Access-Client-Secret': cf_client_secret,
#             'CF-Access-Client-Id': cf_client_id,
#         }

#         # Create a new network password entry
#         password_entry = NetworkPasswordModel(user_id=user_model.id, user=user_model)
#         db.session.add(password_entry)
#         db.session.commit()

#         # Prepare request body for router API
#         request_body = {
#             "id": user_model.id,
#             "name": user_model.username,
#             "password": password_entry.password,
#             "priv": ["user-services-captiveportal-login"],
#             "disabled": False,
#             "descr": f"{user_model.uid}",
#             "expires": None,
#             "cert": None,
#             "authorizedkeys": None,
#             "ipsecpsk": None,
#         }

#         # Send user creation request to router
#         response = requests.post(
#             "https://router.spicerhome.net/api/v2/user",
#             headers=headers,
#             json=request_body,
#             allow_redirects=True
#         )
#         if response.status_code != 200:
#             logging.error(f"Router API error: {response.text}")
#             return {"error": "Failed to create user on router"}, 500

#     except Exception as e:
#         logging.error(f"Error during router API interaction: {e}")
#         return {"error": "Error creating user on router"}, 500

#     # return redirect(url_for("user.dashboard"))

def synchronize_user_with_identity(identity):
    """
    Synchronize a user with their identity. If the user does not exist, create one.
    """
    email = identity.get("email")
    uid = identity.get("user_uuid")
    geo = identity.get("country")
    name = identity.get("name", email.split('@')[0])  # Fallback to email prefix if name is not provided
    username = identity.get("username", email.split('@')[0])  # Fallback to email prefix if username is not provided

    try:
        # Check if user exists
        user = User.query.filter_by(uid=identity.get("user_uuid")).first()
        logging.info(f"Fetching user by UID: {uid}")
        if user:
            logging.info(f"User already exists: {email}")
            return None

        # Fetch default search command
        cmd_query = CommandsModel.query.filter_by(category="default_search").first()
        logging.info(f"Fetching default search command")
        if not cmd_query:
            logging.error("Default search command not found")
            raise ValueError("Default search command is required but not available")

        # Create new user
        user = User(
            uid=uid,
            name=name,
            geo=geo,
            username=username,
            email=email,
            default_search_id=cmd_query.id,
        )

        logging.info(f"Creating new user: {email}")
        db.session.add(user)
        db.session.commit()
        logging.info(f"User created successfully: {email}")

        # Assign permissions
        logging.info(f"Assigning permissions to user: {email}")
        user_permissions = PermissionsModel(
            user_id=user.id,
            permission_name="commands",
            permission_level=999
        )
        logging.info(f"Adding permissions to user: {email}")
        db.session.add(user_permissions)
        db.session.commit()
        logging.info(f"Permissions added successfully: {email}")

        # Add router integration if needed (optional based on your system)
        # router_api_key = app.config.get("ROUTER_API_KEY")
        # if router_api_key:
        #     headers = {
        #         'x-api-key': router_api_key,
        #         'accept': 'application/json',
        #         'CF-Access-Client-Secret': app.config.get("CF_ACCESS_CLIENT_SECRET"),
        #         'CF-Access-Client-Id': app.config.get("CF_ACCESS_CLIENT_ID"),
        #     }
        #     password_entry = NetworkPasswordModel(user_id=user.id, user=user)
        #     db.session.add(password_entry)
        #     db.session.commit()

        #     request_body = {
        #         "id": user.id,
        #         "name": user.username,
        #         "password": password_entry.password,
        #         "priv": ["user-services-captiveportal-login"],
        #         "disabled": False,
        #         "descr": f"{user.uid}",
        #         "expires": None,
        #         "cert": None,
        #         "authorizedkeys": None,
        #         "ipsecpsk": None,
        #     }

        #     response = requests.post(
        #         "https://router.spicerhome.net/api/v2/user",
        #         headers=headers,
        #         json=request_body,
        #         allow_redirects=True
        #     )
        #     if response.status_code != 200:
        #         logging.error(f"Router API error: {response.text}")

        logging.info(f"User created successfully: {email}")
        return user

    except IntegrityError as e:
        logging.error(f"Database integrity error: {e}")
        db.session.rollback()
    except Exception as e:
        logging.error(f"Error synchronizing user: {e}")
        db.session.rollback()

@login_manager.user_loader
def load_user(user_id):
    """Load user from the database by ID for Flask-Login."""
    cf_authorization = request.cookies.get("CF_Authorization")
    if not cf_authorization:
        logging.error("CF_Authorization cookie missing.")
        return None

    try:
        response = requests.get(
            IDENTITY_ENDPOINT,
            headers={"cookie": f"CF_Authorization={cf_authorization}"}
        )
        response.raise_for_status()
        identity = response.json()
        logging.info(f"Fetched identity for user: {identity.get('email')}")
    except requests.RequestException as e:
        logging.error(f"Error fetching Cloudflare identity: {e}")
        return None
    cfcookieuseruid = identity["user_uuid"]
    if cfcookieuseruid == user_id:
        return User.query.filter_by(uid=cfcookieuseruid).first()
    else:
        return None

# @app.before_first_request
# def check_user_logged_in():
#     """Ensure the user is logged in using Cloudflare identity."""
#     if not current_user.is_authenticated:
#         # return  # User is already logged in
#         # Fetch identity from Cloudflare
#         identity = get_identity_from_cloudflare()
#         session['identity'] = identity
#         if identity:
#             # Synchronize with the database
#             user = synchronize_user_with_identity(identity)

#             # Log in the user with Flask-Login
#             user = User.query.filter_by(uid=identity["user_uuid"]).first()
#             if user:
#                 login_user(user)

@app.before_request
def before_request_def():
    cf_authorization = request.cookies.get("CF_Authorization")
    if cf_authorization:
        if session.get('cloudflare', {}).get('cf_authorization') and session.get('cloudflare', {}).get('identity'):
            # Check if the session data is already set
            # also check for possible session hijacking

            if (session['cloudflare']['cf_authorization'] == cf_authorization and
                session['cloudflare']['identity'] and
                session['user_device']['user_agent'] == request.headers.get('User-Agent') and
                session['user_device']['accept_language'] == request.headers.get('Accept-Language')):
                
                # User logged in and userdata is already fetched
                # No need to get the identity again
                # Check for session hijacking

                logging.debug(f"Identity already fetched, User logged in.")
                logging.debug(f"Session hijack check: User-Agent matched.")
                logging.debug(f"User-Agent: {session['user_device']['user_agent']}")
                logging.debug(f"Session hijack check: Language matched.")
                logging.debug(f"Language: {session['user_device']['accept_language']}")
                logging.debug(f"User passed session hijack check.")

                if session['user_device']['ip_address'] != request.headers.get('X-Forwarded-For', request.remote_addr):
                    logging.debug(f"User IP address changed, Updating session data.")
                    session['user_device']['ip_address'] = request.headers.get('X-Forwarded-For', request.remote_addr)
                # logging.debug(f"Session data: {session}")
            else:
                # This would mean that the user has logged out and logged back in
                # or possible session hijacking
                # Delete the session cookie and start a new session
                logging.debug(f"Session hijack check failed or Session deleted, User logged out.")
                session.clear()
                response = make_response(redirect(url_for("internal.internal_search")))
                # response = make_response(redirect(url_for("internal.internal_search", q="logout")))
                response.delete_cookie("CF_Authorization")
                response.delete_cookie("session")
                return response
            
        else:
            # This would mean that the session data was not set
            # New session, We need to get the userdata
            session['cloudflare'] = {}
            session['cloudflare']['cf_authorization'] = cf_authorization
            identity = get_identity_from_cloudflare()
            session['cloudflare']['identity'] = identity
            session['user_device'] = {}

            session['user_device'] = {
                'user_agent': request.headers.get('User-Agent'),
                'ip_address': request.headers.get('X-Forwarded-For', request.remote_addr),
                'accept_language': request.headers.get('Accept-Language')
            }
            user = User.query.filter_by(uid=identity["user_uuid"]).first()
            if user:
                session['user_data'] = user.to_dict()
                login_user(user)
            else:
                # This will create the user if it does not exist
                # This will mean that the identity is provided by Cloudflare
                synchronize_user_with_identity(identity)
                user = User.query.filter_by(uid=identity["user_uuid"]).first()
                session['user_data'] = user.to_dict()
                login_user(user)
    else:
        # User is not logged in
        # This would be an anonymous user, No support for anonymous users yet
        return redirect(url_for("handle_exception", e="User error, Contact the developer."))

    # if "first_request" not in session or session["first_request"] == True:
    #     if not current_user.is_authenticated:
    #         # Fetch identity from Cloudflare
    #         identity = get_identity_from_cloudflare()
    #         # session['identity'] = identity
    #         if identity:
    #             # Synchronize with the database
    #             user = User.query.filter_by(uid=identity["user_uuid"]).first()
    #             if not user:
    #                 # Just saying.. If it cannot find the user then why does it not create the user?
    #                 # This needs to create a user if there is not one.
    #                 user = synchronize_user_with_identity(identity)
    #                 user = User.query.filter_by(uid=identity["user_uuid"]).first()
    #                 login_user(user)

    #             # Log in the user with Flask-Login
    #             if user:
    #                 login_user(user)
    #     session["first_request"] = False

    # Log session data for debugging
    # logging.debug(f"Session data: {session}")

    # Detect infinite redirects
    # current_url = request.url
    # previous_url = session.get('previous_url')
    # redirect_count = session.get('redirect_count', 0)
    # logging.debug(f"Redirect count: {redirect_count}, Current URL: {current_url}, Previous URL: {previous_url}")

    # if previous_url == current_url:
    #     redirect_count += 1
    #     session['redirect_count'] = redirect_count
    #     if redirect_count <= 5:
    #         return redirect(current_url)
    #     elif redirect_count >= 5:
    #         # Handle infinite redirect error
    #         error_details = {
    #             "previous_url": previous_url,
    #             "url": current_url,
    #             "redirect_count": redirect_count,
    #             "user_id": current_user.id if current_user.is_authenticated else "Anonymous",
    #             "user_uid": current_user.uid if current_user.is_authenticated else "Anonymous",
    #             "user_email": current_user.email if current_user.is_authenticated else "Anonymous",
    #             "user_ip": request.headers.get('X-Forwarded-For', request.remote_addr),
    #             "permissions": [perm.permission_name for perm in current_user.permissions] if current_user.is_authenticated else "N/A",
    #         }

    #         subject = f"Infinite Redirect Detected - {app.server_env} Enviroment"
    #         body_text = (
    #             f"An infinite redirect was detected:\n"
    #             f"Previous URL: {error_details['previous_url']}\n"
    #             f"Current URL: {error_details['url']}\n"
    #             f"Redirect Count: {error_details['redirect_count']}\n"
    #             f"User ID: {error_details['user id']}\n"
    #             f"User UID: {error_details['user uid']}\n"
    #             f"User Email: {error_details['user email']}\n"
    #             f"User IP: {error_details['user ip']}\n"
    #             f"Permissions: {error_details['permissions']}\n"
    #         )
    #         body_html = (
    #             f"<p>An infinite redirect was detected:</p>"
    #             f"<p><strong>Previous URL:</strong> {error_details['previous_url']}</p>"
    #             f"<p><strong>Current URL:</strong> {error_details['url']}</p>"
    #             f"<p><strong>Redirect Count:</strong> {error_details['redirect_count']}</p>"
    #             f"<p><strong>User ID:</strong> {error_details['user id']}</p>"
    #             f"<p><strong>User UID:</strong> {error_details['user uid']}</p>"
    #             f"<p><strong>User Email:</strong> {error_details['user email']}</p>"
    #             f"<p><strong>User IP:</strong> {error_details['user ip']}</p>"
    #             f"<p><strong>Permissions:</strong> {error_details['permissions']}</p>"
    #         )
    #         send_email(app.config["DEVELOPER_EMAIL"], subject, body_text, body_html)
    #         return render_template('external/error.html', error_details=error_details), 500
    # else:
    #     session['redirect_count'] = 0
    #     return

    # session['previous_url'] = current_url
    # return


# @app.context_processor
# def utility_processor():
#     def random_id():
#         return uuid.uuid4().hex

#     return dict(random_id=random_id)

# from flask import Flask, render_template, flash
# from flask_login import LoginManager
# from flask_migrate import Migrate

# from models import db, User
# from auth.views import auth

app.register_blueprint(external_blueprint, url_prefix="/external")
app.register_blueprint(internal_blueprint, url_prefix="/internal")
# app.register_blueprint(external_auth, url_prefix="/external/auth")
# app.register_blueprint(internal_auth, url_prefix="/internal/auth")
app.register_blueprint(admin_blueprint, url_prefix="/internal/admin")
app.register_blueprint(api_blueprint, url_prefix="/apiv1")
app.register_blueprint(chores_blueprint, url_prefix="/internal/chores")

# @app.route("/")
# @login_required
# def index():
#     """The main homepage. This is a stub since it's a demo project."""
#     return render_template("index.html")

@app.errorhandler(Exception)
def handle_exception(e = 'Request Error'):
    # Log the error
    logging.error(f"An error occurred: {e}")

    # Send an email to the developer
    error_details = {
        "error": str(e),
        "url": request.url,
        "method": request.method,
        "user id": current_user.id if current_user.is_authenticated else "Anonymous",
        "user uid": current_user.uid if current_user.is_authenticated else "Anonymous",
        "user email": current_user.email if current_user.is_authenticated else "Anonymous",
        "user ip": request.headers.get('X-Forwarded-For', request.remote_addr),
        "permissions": [perm.permission_name for perm in current_user.permissions] if current_user.is_authenticated else "N/A",
        "traceback": traceback.format_exc()
    }

    subject = f"Application Error - {app.server_env} Environment"
    body_text = (
        f"An error occurred:\n"
        f"Error: {error_details['error']}\n"
        f"URL: {error_details['url']}\n"
        f"Method: {error_details['method']}\n"
        f"User ID: {error_details['user id']}\n"
        f"User UID: {error_details['user uid']}\n"
        f"User Email: {error_details['user email']}\n"
        f"User IP: {error_details['user ip']}\n"
        f"Permissions: {error_details['permissions']}\n"
        f"Traceback:\n{error_details['traceback']}"
    )
    body_html = (
        f"<p>An error occurred:</p>"
        f"<p><strong>Error:</strong> {error_details['error']}</p>"
        f"<p><strong>URL:</strong> {error_details['url']}</p>"
        f"<p><strong>Method:</strong> {error_details['method']}</p>"
        f"<p><strong>User ID:</strong> {error_details['user id']}</p>"
        f"<p><strong>User UID:</strong> {error_details['user uid']}</p>"
        f"<p><strong>User Email:</strong> {error_details['user email']}</p>"
        f"<p><strong>User IP:</strong> {error_details['user ip']}</p>"
        f"<p><strong>Permissions:</strong> {error_details['permissions']}</p>"
        f"<p><strong>Traceback:</strong><pre>{error_details['traceback']}</pre></p>"
    )

    send_email(app.config["DEVELOPER_EMAIL"], subject, body_text, body_html)

    # Redirect to a custom error page
    return render_template('external/error.html', error_details=error_details)

@app.route('/')
@login_required
def redirect_to_url():
    print()
    return redirect(url_for("internal.internal_search"))

@app.route('/search=<user_query>')
@login_required
def redirect_old_search_command(user_query):
    return redirect(f"/internal/search?q={user_query}")

@app.route('/external/status', methods=['GET'])
def status():
    return {"status": 200}

# @app.route('/external/redirect', methods=['GET'])
# def redirect_test():
#     return redirect(url_for("redirect_test"))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=host_port, debug=True)