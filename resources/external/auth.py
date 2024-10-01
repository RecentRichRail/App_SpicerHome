import datetime
import json, base64
import webauthn

from flask import (
    Blueprint,
    render_template,
    request,
    make_response,
    session,
    abort,
    url_for,
    redirect,
    flash,
)
from flask_login import login_user, login_required, current_user, logout_user
from sqlalchemy import or_, func
from sqlalchemy.exc import IntegrityError
from webauthn.helpers.exceptions import (
    InvalidRegistrationResponse,
    InvalidAuthenticationResponse,
)
from webauthn.helpers.structs import RegistrationCredential, AuthenticationCredential

from resources.utils import security, util
from models import User, db, CommandsModel, PermissionsModel

auth = Blueprint("external_auth", __name__, template_folder="///templates")

class Response:
    def __init__(self, client_data_json, authenticator_data, signature, userHandle):
        self.client_data_json = client_data_json
        self.authenticator_data = authenticator_data
        self.signature = signature
        self.userHandle = userHandle

def base64url_decode(base64url_str):
        """Decode a Base64URL string into bytes."""
        padding = '=' * (4 - len(base64url_str) % 4)
        base64_str = base64url_str + padding
        base64_bytes = base64_str.replace('-', '+').replace('_', '/')
        return base64.b64decode(base64_bytes)

# @auth.route("/register")
# def register():
#     # Can only register is the IP address matches a list of IP's
#     """Show the form for new users to register"""
#     return render_template("auth/register.html")

# @auth.route("/create-user", methods=["POST"])
# def create_user():
#     """Handle creation of new users from the user creation form."""
#     name = request.form.get("name")
#     username = request.form.get("username")
#     email = request.form.get("email")

#     cmd_query = CommandsModel.query.filter_by(category="default_search").first()
#     print(f"{name}, {username}, {email}, {cmd_query.id}")

#     user = User(name=name, username=username, email=email, default_search_id = cmd_query.id)
#     try:
#         db.session.add(user)
#         db.session.commit()
#     except IntegrityError as e:
#         print(f"Yeah, Some error {e}")
#         return render_template(
#             "auth/_partials/user_creation_form.html",
#             error="That username or email address is already in use. "
#             "Please enter a different one.",
#         )
    
#     user_model = User.query.filter_by(username=username).first()
#     user_permissions_model = PermissionsModel(user_id = user_model.id, permission_name = "commands", permission_level = 999)
#     try:
#         db.session.add(user_permissions_model)
#         db.session.commit()
#     except IntegrityError as e:
#         print(f"Yeah, Some error {e}")
#         return render_template(
#             "auth/_partials/user_creation_form.html",
#             error="Error creating user account. "
#             "Please enter a different one.",
#         )

#     if not current_user:
#         login_user(user)
#         session["used_webauthn"] = False

#         pcco = security.prepare_credential_creation(user)
#         return make_response(
#             render_template(
#                 "auth/_partials/register_credential.html",
#                 public_credential_creation_options=pcco,
#             )
#         )

# @auth.route("/login", methods=["GET"])
# def login():
#     """Prepare to log in the user with biometric authentication"""
#     user_uid = request.cookies.get("user_uid")
#     user = User.query.filter_by(uid=user_uid).first()

#     # If the user is not remembered from a previous session, we'll need to get
#     # their username.
#     if not user:
#         return render_template("auth/login.html", username=None, auth_options=None, next=request.args.get("next"))

#     # If they are remembered, we can skip directly to biometrics.
#     auth_options = security.prepare_login_with_credential(user)

#     # Set the user uid on the session to get when we are authenticating
#     session["login_user_uid"] = user.uid
#     return render_template(
#         "auth/login.html", username=user.username, auth_options=auth_options, next=request.args.get("next")
#     )

@auth.route("/login", methods=["GET"])
def login():
    """Prepare to log in the user with biometric authentication"""
    user_uid = request.cookies.get("user_uid")
    user = User.query.filter_by(uid=user_uid).first()

    # If the user is not remembered from a previous session, we'll need to get
    # their username.
    if not user:
        return render_template("auth/sp_login.html", username=None, auth_options=None, next=request.args.get("next"))

    # If they are remembered, we can skip directly to biometrics.
    auth_options = security.prepare_login_with_credential(user)

    # Set the user uid on the session to get when we are authenticating
    session["login_user_uid"] = user.uid
    return render_template(
        "auth/sp_login.html", username=user.username, auth_options=auth_options, next=request.args.get("next")
    )

@auth.route("/prepare-login", methods=["POST"])
def prepare_login():
    """Prepare login options for a user based on their username or email"""
    username_or_email = request.form.get("username_email", "").lower()
    # The lower function just does case insensitivity for our.
    user = User.query.filter(
        or_(
            func.lower(User.username) == username_or_email,
            func.lower(User.email) == username_or_email,
        )
    ).first()

    # if no user matches, send back the form with an error message
    if not user:
        return render_template(
            "auth/_partials/username_form.html", error="No matching user found"
        )

    auth_options = security.prepare_login_with_credential(user)

    res = make_response(
        # render_template(
        #     "auth/_partials/select_login.html",
        #     auth_options=auth_options,
        #     username=user.username,
        # )
        render_template(
            "auth/sp_login.html",
            username=user.username,
            auth_options=auth_options
        )
    )

    # set the user uid on the session to get when we are authenticating later.
    session["login_user_uid"] = user.uid
    res.set_cookie(
        "user_uid",
        user.uid,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=datetime.timedelta(days=30),
    )
    return res


@auth.route("/login-switch-user")
def login_switch_user():
    """Remove a remembered user and show the username form again."""
    session.pop("login_user_uid", None)
    res = make_response(redirect(url_for("external_auth.login")))
    res.delete_cookie("user_uid")
    return res

@auth.route("/verify-login-credential", methods=["POST"])
def verify_login_credential():
    """Log in a user with a submitted credential"""
    user_uid = session.get("login_user_uid")
    user = User.query.filter_by(uid=user_uid).first()
    if not user:
        abort(make_response('{"verified": false}', 400))

    # authentication_credential = AuthenticationCredential.parse_raw(request.get_data())

    # data = json.loads(request.get_data())
    data = request.get_json()
    print(data)

    # auth_cred = AuthResponse(data)
    # authentication_credential = auth_cred

    raw_id_bytes = base64.urlsafe_b64decode(data.get("rawId") + '==')
        
    # Extract and decode the response data
    response_data = data.get("response")
    client_data_json_bytes = base64.urlsafe_b64decode(response_data.get("clientDataJSON") + '==')
    authenticator_data_object_bytes = base64.urlsafe_b64decode(response_data.get("authenticatorData") + '==')
    signature_object_bytes = base64.urlsafe_b64decode(response_data.get("signature") + '==')
    userHandle_object_bytes = base64.urlsafe_b64decode(response_data.get("userHandle") + '==')

    response_obj = Response(
        client_data_json=client_data_json_bytes,
        authenticator_data=authenticator_data_object_bytes,
        signature=signature_object_bytes,
        userHandle=userHandle_object_bytes
    )

    authentication_credential = AuthenticationCredential(
        id=data.get("id"),
        raw_id=raw_id_bytes,
        response=response_obj,
        type=data.get("type"),
        )

    # authentication_credential = AuthenticationCredential(
    #         id=data['id'],
    #         raw_id=base64url_decode(data['rawId']),
    #         response=response,
    #         type=data.get('type'),
    #         authenticator_attachment=data.get('authenticatorAttachment')
    #         # clientExtensionResults=data.get('clientExtensionResults')
    #     )

    try:
        security.verify_authentication_credential(user, authentication_credential)
        login_user(user, duration = datetime.timedelta(days=30))
        session["used_webauthn"] = True
        flash("Login Complete", "success")

        next_ = request.args.get("next")
        if not next_ or not util.is_safe_url(next_):
            next_ = url_for("internal.internal_search")
        return util.make_json_response({"verified": True, "next": next_})
    except InvalidAuthenticationResponse:
        abort(make_response('{"verified": false}', 400))

@auth.route("/email-login")
def email_login():
    """Request login by emailed link."""
    user_uid = session.get("login_user_uid")
    user = User.query.filter_by(uid=user_uid).first()

    # This is probably impossible, but seems like useful protection
    if not user:
        res = make_response(
            render_template(
                "auth/_partials/username_form.html", error="No matching user found."
            )
        )
        session.pop("login_user_uid", None)
        return res
    login_url = security.generate_magic_link(user.uid)
    # TODO: make a template for an html version of the email.
    util.send_email(
        user.email,
        "Flask WebAuthn Login",
        "Click or copy this link to log in. You must use the same browser that "
        f"you were using when you requested to log in. {login_url}",
        render_template(
            "auth/email/login_email.html", username=user.username, login_url=login_url
        ),
    )
    res = make_response(render_template("auth/_partials/email_login_message.html"))
    res.set_cookie(
        "magic_link_user_uid",
        user.uid,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=datetime.timedelta(minutes=15),
    )
    return res

@auth.route("/magic-link")
def magic_link():
    """Handle incoming magic link authentications."""
    url_secret = request.args.get("secret")
    user_uid = request.cookies.get("magic_link_user_uid")
    user = User.query.filter_by(uid=user_uid).first()

    if not user:
        flash("Could not log in. Please try again", "failure")
        return redirect(url_for("external_auth.login"))

    if security.verify_magic_link(user_uid, url_secret):

        login_user(user, duration = datetime.timedelta(days=30))
        session["used_webauthn"] = False
        flash("Logged in", "success")
        return redirect(url_for("internal_auth.user_profile"))

    return redirect(url_for("external_auth.login"))