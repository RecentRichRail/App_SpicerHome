import datetime

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
    Response,
    current_app,
)
import base64, logging
import requests
from flask_login import login_required, current_user, logout_user
from sqlalchemy import or_, func
from sqlalchemy.exc import IntegrityError
from webauthn.helpers.exceptions import (
    InvalidRegistrationResponse,
    InvalidAuthenticationResponse,
)
from webauthn.helpers.structs import RegistrationCredential, AuthenticationCredential

from resources.utils import security_old, util
from models import User, db, CommandsModel, PermissionsModel
# from models import User, db

auth = Blueprint("internal_auth", __name__, template_folder="templates")

class Response:
    def __init__(self, client_data_json, attestation_object):
        self.client_data_json = client_data_json
        self.attestation_object = attestation_object

# @auth.route("/add-credential", methods=["POST"])
# @login_required
# def add_credential():
#     """Receive a newly registered credentials to validate and save."""
#     print(request)
#     data = request.get_json()
#     print(data)

#     try:
#         raw_id_bytes = base64.urlsafe_b64decode(data.get("rawId") + '==')
        
#         # Extract and decode the response data
#         response_data = data.get("response")
#         client_data_json_bytes = base64.urlsafe_b64decode(response_data.get("clientDataJSON") + '==')
#         attestation_object_bytes = base64.urlsafe_b64decode(response_data.get("attestationObject") + '==')

#         response_obj = Response(
#             client_data_json=client_data_json_bytes,
#             attestation_object=attestation_object_bytes
#         )

#         registration_credential = RegistrationCredential(
#             id=data.get("id"),
#             raw_id=raw_id_bytes,
#             response=response_obj,
#             type=data.get("type"),
#         )
#         security_old.verify_and_save_credential(current_user, registration_credential)
#         session["used_webauthn"] = True
#         flash("Setup Complete!", "success")

#         res = util.make_json_response(
#             {"verified": True, "next": url_for("internal_auth.user_profile")}
#         )
#         res.set_cookie(
#             "user_uid",
#             current_user.uid,
#             httponly=True,
#             secure=True,
#             samesite="strict",
#             max_age=datetime.timedelta(days=30),
#         )
#         return res
#     except InvalidRegistrationResponse as e:
#         print(f"InvalidRegistrationResponse: {e}")
#         abort(make_response('{"verified": false}', 400))

#     except TypeError as e:
#         print(f"Error: {e}")
#         flash("Failed to add credential.", "danger")
#         return redirect(url_for("external_auth.register"))

@auth.route("/logout")
@login_required
def logout():
    # Remove the CF_Authorization cookie
    response = make_response(redirect(url_for("redirect_to_url")))
    response.delete_cookie("CF_Authorization")
    response.delete_cookie("cf_clearance")
    response.delete_cookie("CF_AppSession")

    # Log the user out and show a flash message
    logout_user()
    flash("Logged out", "success")
    
    return response


# @auth.route("/user-profile")
# @login_required
# def user_profile():
#     return render_template("auth/user_profile.html")


# @auth.route("/create-credential")
# @login_required
# def create_credential():
#     """Start creation of new credentials by existing users."""
#     pcco = security_old.prepare_credential_creation(current_user)
#     flash("Click the button to start setup", "warning")
#     print(pcco)
#     return make_response(
#         render_template(
#             "auth/_partials/register_credential.html",
#             public_credential_creation_options=pcco,
#         )
#     )

# @auth.route("/register")
# @login_required
# def register():
#     # Can only register is the IP address matches a list of IP's
#     """Show the form for new users to register"""
#     return render_template("auth/register.html")

# @auth.route("/create-user", methods=["POST"])
# @login_required
# def create_user():
#     if not current_user:
#         return redirect(url_for("external_auth.login"))
    
#     """Handle creation of new users from the user creation form."""
#     name = request.form.get("name")
#     username = request.form.get("username")
#     email = request.form.get("email")

#     cmd_query = CommandsModel.query.filter_by(category="default_search").first()
#     # print(f"{name}, {username}, {email}, {cmd_query.id}")

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
    
#     try:
#         router_API_Key = current_app.router_API_Key
#         if not router_API_Key:
#             return {"message": "API key not found"}, 500

#         headers = {'x-api-key': router_API_Key, 'accept': 'application/json', 'CF-Access-Client-Secret': current_app.CF_Access_Client_Secret, 'CF-Access-Client-Id': current_app.CF_Access_Client_Id}

            
#         # Create a new NetworkPasswordModel entry
#         password_entry = NetworkPasswordModel(
#             user_id=user_model.id,
#             user=user_model
#         )

#         # Add the new entry to the session and commit
#         db.session.add(password_entry)
#         db.session.commit()

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
#             "ipsecpsk": None
#         }

#         requests.post("https://router.spicerhome.net/api/v2/user", headers=headers, json=request_body, allow_redirects=True)
#     except:
#         logging.error("Error creating user on router")
#     # if not current_user:
#     #     login_user(user)
#     #     session["used_webauthn"] = False

#     #     pcco = security.prepare_credential_creation(user)
#     #     return make_response(
#     #         render_template(
#     #             "auth/_partials/register_credential.html",
#     #             public_credential_creation_options=pcco,
#     #         )
#     #     )
#     # else:
#     login_url = url_for(
#         "external_auth.login", _external=True, _scheme="https"
#     )
#     util.send_email(
#         user.email,
#         "Flask WebAuthn Login",
#         "Welcome! Finish setting up your account by using passwordless authentication to access resources on this network! {login_url}",
#         render_template(
#             "auth/email/register_email.html", username=user.username, login_url=login_url
#         ),
#     )
#     return render_template(
#             "auth/_partials/user_creation_form.html",
#             success="User created successfully. Have them check their email to login.",
#         )
#     # return redirect(url_for("redirect_to_url"))

#     # TODO: create a route to revoke all credentials
