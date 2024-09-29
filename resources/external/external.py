from flask import Blueprint, render_template, request, current_app, jsonify, redirect
from flask_login import login_user, login_required, current_user, logout_user
from sqlalchemy import or_, func
from models import User, NetworkPasswordModel
from resources.utils import security, util
import hmac, logging

external_blueprint = Blueprint("external", __name__, template_folder="templates")

@external_blueprint.route("/captive-portal", methods=["GET", "POST"])
def captive_portal():
    if request.method == "GET":
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

        redirect(continue_url)

        return render_template("external/captive-portal/captive-index.html")

    elif request.method == "POST":
        data = request.get_json()
        action = data.get('action')
        username_or_email = data.get('username')
        password_input = data.get('password')
        continue_url = request.args.get('continue_url')  # Extract continue_url from request arguments

        if action == "authenticate":
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

                    logging.info(f"User {user.username} authenticated captive portal")

                    return jsonify({"message": "Login successful", "continue_url": continue_url}), 200

            logging.info(f"User {username_or_email} failed to authenticate captive portal")
            return jsonify({"message": "Bad username or password"}), 401

        elif action == "send_email":
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
                return jsonify({'message': 'success', 'continue_url': continue_url}), 200

            return jsonify({"message": "User data not found in response"}), 500

        return jsonify({"message": "Invalid action"}), 400