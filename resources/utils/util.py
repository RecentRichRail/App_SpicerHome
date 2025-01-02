import json, logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlparse, urljoin

from sqlalchemy.types import TypeDecorator, String
from cryptography.fernet import Fernet, InvalidToken
import base64

from flask import make_response, request, current_app

class EncryptedType(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return encrypt(value)

    def process_result_value(self, value, dialect):
        if value is not None:
            return decrypt(value)

def encrypt(value):
    try:
        secret = current_app.config["SECRET_KEY"]
        key = base64.urlsafe_b64encode(secret.encode('utf-8'))
        cipher_suite = Fernet(key)
        value = value.encode('utf-8')
        encrypted_value = cipher_suite.encrypt(value)
        return base64.b64encode(encrypted_value).decode('utf-8')
    except Exception as e:
        logging.error(f"Encryption error: {e}")
        raise

def decrypt(value):
    try:
        secret = current_app.config["SECRET_KEY"]
        key = base64.urlsafe_b64encode(secret.encode('utf-8'))
        cipher_suite = Fernet(key)
        encrypted_value = base64.b64decode(value.encode('utf-8'))
        decrypted_value = cipher_suite.decrypt(encrypted_value)
        return decrypted_value.decode('utf-8')
    except InvalidToken:
        logging.error("InvalidToken error: Decryption failed for value: %s", value)
        return None  # or handle it in a way that suits your application
    except Exception as e:
        logging.error(f"Decryption error: {e}")
        return None  # or handle it in a way that suits your application


def make_json_response(body, status=200):
    res = make_response(json.dumps(body), status)
    res.headers["Content-Type"] = "application/json"
    return res


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def send_email(to, subject, body_text, body_html=None):
    """Utility function for sending email with smtplib."""
    mail_from = current_app.config["MAIL_FROM"]
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = mail_from
    message["To"] = to
    part1 = MIMEText(body_text, "plain")
    message.attach(part1)
    if body_html:
        part2 = MIMEText(body_html, "html")
        message.attach(part2)
    with smtplib.SMTP(
        current_app.config["MAIL_SERVER"], current_app.config["MAIL_PORT"]
    ) as server:
        server.starttls()
        server.login(
            current_app.config["MAIL_USERNAME"], current_app.config["MAIL_PASSWORD"]
        )
        server.sendmail(mail_from, to, message.as_string())
