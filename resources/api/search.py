from flask import Blueprint, request, jsonify, current_app, render_template
import os
import requests
from models import User, CommandsModel, BananaGameUserBananasModel, BananaGameLifetimeBananasModel, BananaGameButtonPressModel, RequestsModel, TrackingNumbersModel, PermissionsModel
from models import db
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from tracking_numbers import get_tracking_number
from flask_login import login_user, login_required, current_user, logout_user
from sqlalchemy import or_, func

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import base64

from resources.utils import security, util

api_blueprint = Blueprint("apiv1", __name__, template_folder="templates")

def run_funtion(script_path, data):
    spec = importlib.util.spec_from_file_location("module.name", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run(data)

@api_blueprint.route('/data/user/change_theme', methods=['POST'])
def change_theme():
    print(current_user)
    selected_theme = request.json.get('theme')
    # jwt_token = request.json.get("jwt_token")

    # theme_list = ['coffee', 'mignight', 'dark']

    # if str(selected_theme) not in theme_list:
    #     print("selected_theme")
    #     return {"message": "Error"}

    # payload = requests.post(f"http://{current_app.authentication_server}/apiv1/auth/get_user_info", json={"jwt": jwt_token})
    # user_sub = payload.json()

    if current_user:
    #     user_model = User.query.filter_by(id=user_sub['sub']).first()


        current_user.user_theme = selected_theme

        try:
            db.session.commit()
            print(selected_theme)
            return {'message': 'success', 'theme': selected_theme}, 200
        except SQLAlchemyError as e:
            print(e)
            return {"message": "Error"}
    else:
        return {"message": "Error"}
    
@api_blueprint.route("/data/user/change_default_search", methods=['POST'])
def change_user_default_command():
    print('Request Incoming')
    # jwt_token = request.json.get("jwt_token")
    new_search_id = request.json.get("search_id")

    # payload = requests.post(f"http://{current_app.authentication_server}/apiv1/auth/get_user_info", json={"jwt": jwt_token})
    # user_sub = payload.json()

    if current_user:
        # user_model = UsersModel.query.filter_by(id=user_sub['sub']).first()


        current_user.default_search_id = new_search_id

        try:
            db.session.commit()
            return {"message": "Success"}, 200
        except SQLAlchemyError as e:
            print(e)
            return {"message": "Error"}
    return {"message": "Error"}

@api_blueprint.route('/data/user/search/track/update_note', methods=['POST'])
def tracking_update_note():
    track_id = request.json.get('track_id')
    updated_note = request.json.get('updated_note')
    # print(updated_note)
    # jwt_token = request.json.get("jwt_token")

    if len(updated_note) > 5000:
        return {"message": "Error"}

    # payload = requests.post(f"http://{current_app.authentication_server}/apiv1/auth/get_user_info", json={"jwt": jwt_token})
    # user_sub = payload.json()

    if current_user:
        selected_package = TrackingNumbersModel.query.filter_by(id=track_id).first()
        if selected_package.user_id == current_user.id:
            selected_package.note = updated_note
            try:
                db.session.commit()
                return {'message': 'success'}, 200
            except SQLAlchemyError as e:
                print(e)
                return {"message": "Error"}
    return {"message": "Error"}

@api_blueprint.route('/captive/send_email', methods=['POST'])
def captive_send_email():
    username_or_email = request.json.get('username')
    print(username_or_email)
    user = User.query.filter(
        or_(
            func.lower(User.username) == username_or_email,
            func.lower(User.email) == username_or_email,
        )
    ).first()
    if user:
        router_API_Key = current_app.router_API_Key
        if not router_API_Key:
            return {"message": "API key not found"}, 500

        headers = {'x-api-key': router_API_Key, 'accept': 'application/json', 'CF-Access-Client-Secret': current_app.CF_Access_Client_Secret, 'CF-Access-Client-Id': current_app.CF_Access_Client_Id}
        response = requests.get("https://router.spicerhome.net/api/v2/users?limit=0&offset=0", headers=headers, allow_redirects=True)

        # Log response details for debugging
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Content: {response.content}")

        if response.status_code == 200:
            if response.content:
                try:
                    user_data = response.json()

                    uid = user.uid
                    uid_16_bit = uid & 0xFFFF  # Convert to 16-bit integer

                    # Encrypt the 16-bit uid
                    secret_key = current_app.config['SECRET_KEY'].encode('utf-8')
                    iv = b'\x00' * 16  # Initialization vector
                    cipher = Cipher(algorithms.AES(secret_key), modes.CBC(iv), backend=default_backend())
                    encryptor = cipher.encryptor()

                    # Pad the data to be a multiple of the block size
                    padder = padding.PKCS7(algorithms.AES.block_size).padder()
                    padded_data = padder.update(uid_16_bit.to_bytes(2, 'big')) + padder.finalize()

                    encrypted_password = encryptor.update(padded_data) + encryptor.finalize()
                    encrypted_password_b64 = base64.b64encode(encrypted_password).decode('utf-8')


                    if not user_data and 'data' in user_data and len(user_data['data']) > 0:

                        request_body = {
                            "name": user.username,
                            "password": encrypted_password_b64,
                            "priv": ["user-services-captiveportal-login"],
                            "disabled": False,
                            "descr": f"{user.uid}",
                            "expires": None,
                            "cert": None,
                            "authorizedkeys": None,
                            "ipsecpsk": None
                        }

                        response = requests.post("https://router.spicerhome.net/api/v2/user", headers=headers, json=request_body, allow_redirects=True)
                        if response.status_code != 200:
                            return {"message": "Failed to create user"}, response.status_code
                    
                    # Send email with encrypted password
                    util.send_email(
                        user.email,
                        "Flask WebAuthn Login",
                        f"Your password is: {encrypted_password_b64}",
                        render_template(
                            "auth/email/login_captive.html", username=user.username, encrypted_password_b64=encrypted_password_b64
                        ),
                    )
                    return {'message': 'success', 'data': user_data}, 200
                
                except ValueError:
                    return {"message": "Error decoding JSON response"}, 500
            else:
                return {"message": "Empty response from router API"}, 500
            
    return {"message": "User data not found in response"}, 500