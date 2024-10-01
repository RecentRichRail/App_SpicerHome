from flask import Blueprint, request, jsonify, current_app, render_template
import os
import requests
from models import User, NetworkPasswordModel, CommandsModel, BananaGameUserBananasModel, BananaGameLifetimeBananasModel, BananaGameButtonPressModel, RequestsModel, TrackingNumbersModel, PermissionsModel
from models import ChoresUser
from models import db
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from tracking_numbers import get_tracking_number
from flask_login import login_user, login_required, current_user, logout_user
from sqlalchemy import or_, func
import logging

import hmac
import hashlib
import base64

import importlib

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

    if current_user:

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
    new_search_id = request.json.get("search_id")

    if current_user:

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

        # Check if the user has a password in the NetworkPasswordModel
        password_entry = NetworkPasswordModel.query.filter_by(user_id=user.id).first()

        # Send email with encrypted password
        util.send_email(
            user.email,
            "Flask WebAuthn Login",
            f"Your password is: {password_entry.password}",
            render_template(
                "auth/email/login_captive.html", username=user.username, password=password_entry.password
            ),
        )
        return {'message': 'success'}, 200

    return {"message": "User data not found in response"}, 500

@api_blueprint.route('/chores/points', methods=['POST'])
def chores_test():
    data = request.get_json()
    name = data.get('name')
    action = data.get('action')
    points = data.get('points')

    if not action or (action != 'get' and (not name or points is None)):
        return {"message": "Invalid input"}, 400

    if action == 'get':
        if not name:
            users = ChoresUser.query.all()
            all_users_points = {user.name: user.points for user in users}
            return {"message": "success", "points": all_users_points}, 200
        user = ChoresUser.query.filter_by(name=name).first()
        if not user:
            return {"message": "User not found"}, 404
        return {"message": "success", "points": user.points}, 200

    user = ChoresUser.query.filter_by(name=name).first()
    if not user:
        user = ChoresUser(name=name, points=0)
        db.session.add(user)

    if action == 'add':
        user.points += points
    elif action == 'subtract':
        user.points -= points
    else:
        return {"message": "Invalid action"}, 400

    db.session.commit()
    return {"message": "success", "points": user.points}, 200