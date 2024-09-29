from flask import Blueprint, render_template, request, current_app, jsonify
from flask_login import login_user, login_required, current_user, logout_user
from sqlalchemy import or_, func
from models import User, NetworkPasswordModel
from resources.utils import security, util
import hmac, logging

external_blueprint = Blueprint("external", __name__, template_folder="templates")

@external_blueprint.route("/captive-portal/login")
def captiveportallogin():
    # Extract query parameters
    login_url = request.args.get('login_url')
    client_mac = request.args.get('client_mac')
    client_ip = request.args.get('client_ip')
    ap_mac = request.args.get('ap_mac')
    continue_url = request.args.get('continue_url')
    status = request.args.get('status')

    print(f"login_url: {login_url}")
    print(f"client_mac: {client_mac}")
    print(f"client_ip: {client_ip}")
    print(f"ap_mac: {ap_mac}")
    print(f"continue_url: {continue_url}")
    print(f"status: {status}")

    if current_user.is_anonymous:
        return render_template("external/captive-portal/captive-index.html")
    else:
        return "login success"

@external_blueprint.route("/captive-portal/authenticate", methods=["POST"])
def authenticate():
    data = request.get_json()
    username_input = data.get('username')
    password_input = data.get('password')

    username_or_email = username_input
    print(username_or_email)
    user = User.query.filter(
        or_(
            func.lower(User.username) == username_or_email,
            func.lower(User.email) == username_or_email,
        )
    ).first()
    if user:
        router_API_Key = current_app.router_API_Key

        # Check if the user has a password in the NetworkPasswordModel
        password_entry = NetworkPasswordModel.query.filter_by(user_id=user.id).first()

        # Dummy authentication logic
        if user.username and hmac.compare_digest(password_input, password_entry.password):
            headers = {'x-api-key': router_API_Key, 'accept': 'application/json', 'CF-Access-Client-Secret': current_app.CF_Access_Client_Secret, 'CF-Access-Client-Id': current_app.CF_Access_Client_Id}

            logging.info(f"User {user.username} authenticated")

            return jsonify({"message": "Success"}), 200

    logging.info(f"User {username_input} failed to authenticate - {password_input}")
    return jsonify({"message": "Bad username or password"}), 401

@external_blueprint.route('/captive-portal/send_email', methods=['POST'])
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
            return jsonify({"message": "API key not found"}), 500

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
        return jsonify({'message': 'success'}), 200

    return jsonify({"message": "User data not found in response"}), 500