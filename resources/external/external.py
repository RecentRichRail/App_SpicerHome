from flask import Blueprint, render_template, request, redirect, url_for, current_app
import logging
from urllib.parse import urlparse, urlunparse
from flask_login import current_user

external_blueprint = Blueprint("external", __name__, template_folder="templates")

def is_valid_url(url):
    """
    Validate the provided URL to ensure it has a valid scheme and netloc.
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def normalize_url(url):
    """
    Normalize a URL by stripping query parameters and fragments for comparison.
    """
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

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

        # Log parameters for debugging
        logging.info(f"Received captive portal request: "
                     f"login_url={login_url}, client_mac={client_mac}, client_ip={client_ip}, "
                     f"ap_mac={ap_mac}, continue_url={continue_url}, status={status}")

        # Ensure the user is authenticated (check current_user)
        if current_user.is_authenticated:
            logging.info(f"Authenticated user {current_user.username} detected.")

            # Redirect to continue_url (grant internet access)
            if continue_url and is_valid_url(continue_url):
                redirect_url = (
                    f"/external/captive-portal?login_url=https://spicerhome.cloudflareaccess.com&client_mac={client_mac}&"
                    f"client_ip={client_ip}&ap_mac={ap_mac}&continue_url={continue_url}&status=1"
                )
                # logging.info(f"Redirecting authenticated user to continue_url: {continue_url}")
                # return redirect(continue_url)
                logging.info(f"Redirecting authenticated user to continue_url: {redirect_url}")
                return redirect(redirect_url)
                
            else:
                logging.warning("Invalid or missing continue_url, redirecting to fallback.")
                return {"message": "Authentication successful, no continue_url provided."}, 200

        # If the user is not authenticated (status=0 or missing status)
        if status == "0":
            # The user is unauthenticated; render the captive portal page
            logging.info("Rendering captive portal page for unauthenticated user.")
            return render_template("external/captive-portal/captive-index.html")

        # Default fallback
        logging.warning("Unexpected flow, redirecting to login_url.")
        return redirect(login_url)

    # Handle POST requests (optional, depending on the portal logic)
    if request.method == "POST":
        # Add POST handling logic if necessary
        return "POST method not supported", 405
