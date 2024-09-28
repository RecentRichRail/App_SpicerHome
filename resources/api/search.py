from flask import Blueprint, request, jsonify, current_app
import os
import requests
from models import User, CommandsModel, BananaGameUserBananasModel, BananaGameLifetimeBananasModel, BananaGameButtonPressModel, RequestsModel, TrackingNumbersModel, PermissionsModel
from models import db
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from tracking_numbers import get_tracking_number
from flask_login import login_user, login_required, current_user, logout_user

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