import logging
from flask import Flask, render_template, redirect, url_for, request, session
from flask_login import LoginManager, login_user, login_required, current_user
from flask_migrate import Migrate
import jinja_partials
import os
from dotenv import load_dotenv
import traceback
from flask_session import Session

# Encrypt and Decrypt functions
from resources.utils.util import encrypt

from resources.utils.util import send_email
from resources.utils.script_first_run import create_commands
from models import db, User
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
from resources.internal.household import household_blueprint

load_dotenv()

app = Flask(__name__)
jinja_partials.register_extensions(app)

login_manager = LoginManager()
login_manager.init_app(app)
migrate = Migrate(app, db)

# login_manager.login_view = "external_auth.login"

logging.basicConfig(level=logging.DEBUG)

host_port = os.environ.get('host_port')
app.BRAVE_API_KEY = os.environ.get('BRAVE_API_KEY')
app.dev_server = os.environ.get('dev_server')
app.server_env = os.environ.get('server_env')
# app.router_API_Key = os.environ.get('router_API_Key')
app.CF_Access_Client_Id = os.environ.get('CF-Access-Client-Id')
app.CF_Access_Client_Secret = os.environ.get('CF-Access-Client-Secret')
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

if app.server_env == 'alpha':
    import subprocess
    # If current dir is not the same as the script dir, change to the script dir
    if os.getcwd() != os.path.dirname(os.path.realpath(__file__)):
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
    try:
        output = subprocess.check_output(['pgrep', '-f', __name__])
        for pid in output.decode().strip().split('\n'):
            subprocess.check_call(['kill', '-9', pid])
    except subprocess.CalledProcessError:
        pass

CLOUDFLARE_TEAM_NAME = "SpicerHome"
app.config['IDENTITY_ENDPOINT'] = f"https://{CLOUDFLARE_TEAM_NAME}.cloudflareaccess.com/cdn-cgi/access/get-identity"

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

db.init_app(app)
with app.app_context():
    db.create_all()
    logging.debug("Database created.")
    Session(app)
    logging.debug("Session created.")
    create_commands()
    logging.debug("Commands created.")

@login_manager.user_loader
def load_user(user_id):
    # Load the user from the database
    # User class can handle the user loading
    cf_authorization = request.cookies.get("CF_Authorization")
    if not cf_authorization:
        logging.error("CF_Authorization cookie missing.")
        return None
    
    return User.get_user_from_cloudflare_cookie()

@app.before_request
def before_request_def():
    cf_authorization = request.cookies.get("CF_Authorization")
    if cf_authorization:
        if session.get('cloudflare', {}).get('cf_authorization') and session.get('cloudflare', {}).get('user_uuid'):
            # Check if the session data is already set
            # also check for possible session hijacking

            # if session['cloudflare']['cf_authorization'] == cf_authorization:
                
            #     # User logged in and userdata is already fetched
            #     # No need to get the identity again
            #     # Check for session hijacking

            #     # logging.debug(f"Identity already fetched, User logged in.")
            #     # logging.debug(f"Session hijack check: User-Agent matched.")
            #     # logging.debug(f"User-Agent: {session['user_device']['user_agent']}")
            #     # logging.debug(f"Session hijack check: Language matched.")
            #     # logging.debug(f"Language: {session['user_device']['accept_language']}")
            #     # logging.debug(f"User passed session hijack check.")

            #     if decrypt(session['user_device']['ip_address']) != request.headers.get('X-Forwarded-For', request.remote_addr):
            #         logging.debug(f"User IP address changed, Updating session data.")
            #         session['user_device']['ip_address'] = encrypt(request.headers.get('X-Forwarded-For', request.remote_addr))
            #     # logging.debug(f"Session data: {session}")
            # else:
            #     # This would mean that the user has logged out and logged back in
            #     # or possible session hijacking
            #     # Delete the session cookie and start a new session
            #     logging.debug(f"Session hijack check failed or Session deleted, User logged out.")
            #     # session.clear()
            #     # response = make_response(redirect(url_for("internal.internal_search")))
            #     response = make_response(redirect(url_for("internal.internal_search", q="logout")))
            #     response.delete_cookie("CF_Authorization")
            #     response.delete_cookie("session")
            #     return response
            pass
            
        else:
            # This would mean that the session data was not set
            # New session, We need to get the userdata
            session['cloudflare'] = {}
            session['cloudflare']['cf_authorization'] = cf_authorization
            identity = User.get_user_identity_from_cloudflare()
            logging.debug(f"Identity Set from 'get_identity_from_cloudflare'")
            session['cloudflare']['user_uuid'] = identity["user_uuid"]
            session['user_device'] = {}

            session['user_device'] = {
                'user_agent': encrypt(request.headers.get('User-Agent')),
                'ip_address': encrypt(request.headers.get('X-Forwarded-For', request.remote_addr)),
                'accept_language': encrypt(request.headers.get('Accept-Language'))
            }
            user_uid_for_logging = identity["user_uuid"]
            logging.debug(f"Fetching user by UID: {user_uid_for_logging}")
            user = User.get_user_from_cloudflare_cookie()
            if user:
                session['user_data'] = user.to_dict()
                logging.debug(f"User email: {user.email}")
                login_user(user)
            else:
                logging.debug(f"User not found.")
    else:
        # User is not logged in
        # This would be an anonymous user, No support for anonymous users yet
        logging.debug(f"This would be an anonymous user, No support for anonymous users yet.")
        return redirect(url_for("handle_exception", e="User error, Contact the developer."))

app.register_blueprint(external_blueprint, url_prefix="/external")
app.register_blueprint(internal_blueprint, url_prefix="/internal")
app.register_blueprint(admin_blueprint, url_prefix="/internal/admin")
app.register_blueprint(api_blueprint, url_prefix="/apiv1")
app.register_blueprint(chores_blueprint, url_prefix="/internal/chores")
app.register_blueprint(household_blueprint, url_prefix="/internal/household")

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
    return render_template('external/error.html', error_details=error_details)

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