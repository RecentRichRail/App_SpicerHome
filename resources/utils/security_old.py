# import datetime
# import json
# import os
# import secrets
# from urllib.parse import urlparse

# import bcrypt
# import webauthn
# from flask import request, url_for
# from webauthn.helpers.structs import PublicKeyCredentialDescriptor

# from models import WebAuthnCredential, db, RegistrationChallenge, AuthenticationChallenge, EmailAuthSecret
# from sqlalchemy import Column, String, DateTime, LargeBinary
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.exc import IntegrityError

# # Base = declarative_base()

# # class RegistrationChallenge(Base):
# #     __tablename__ = 'registration_challenges'
# #     user_uid = Column(String, primary_key=True)
# #     challenge = Column(LargeBinary)
# #     expires_at = Column(DateTime)

# # class AuthenticationChallenge(Base):
# #     __tablename__ = 'authentication_challenges'
# #     user_uid = Column(String, primary_key=True)
# #     challenge = Column(LargeBinary)
# #     expires_at = Column(DateTime)

# # class EmailAuthSecret(Base):
# #     __tablename__ = 'email_auth_secrets'
# #     user_uid = Column(String, primary_key=True)
# #     secret_hash = Column(LargeBinary)
# #     expires_at = Column(DateTime)


# def _hostname():
#     return str(urlparse(request.base_url).hostname)


# def prepare_credential_creation(user):
#     """Generate the configuration needed by the client to start registering a new
#     WebAuthn credential."""
#     public_credential_creation_options = webauthn.generate_registration_options(
#         rp_id=_hostname(),
#         rp_name="Flask WebAuthn Demo",
#         user_id=str(user.uid).encode('utf-8'),  # Convert user_id to bytes
#         user_name=user.username,
#     )

#     # Store the challenge in the database
#     challenge = RegistrationChallenge(
#         user_uid=user.uid,
#         challenge=public_credential_creation_options.challenge,
#         expires_at=datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
#     )
#     try:
#         db.session.add(challenge)
#         db.session.commit()
#     except IntegrityError:
#         db.session.rollback()  # Rollback the session to clear the failed transaction
#         db.session.query(RegistrationChallenge).filter_by(user_uid=user.uid).update(
#             {
#                 "challenge": public_credential_creation_options.challenge,
#                 "expires_at": datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
#             }
#         )
#         db.session.commit()

#     return json.loads(webauthn.options_to_json(public_credential_creation_options))


# def verify_and_save_credential(user, registration_credential):
#     """Verify that a new credential is valid for the"""
#     challenge = db.session.query(RegistrationChallenge).filter_by(user_uid=user.uid).first()

#     # If the credential is somehow invalid (i.e. the challenge is wrong),
#     # this will raise an exception. It's easier to handle that in the view
#     # since we can send back an error message directly.
#     auth_verification = webauthn.verify_registration_response(
#         credential=registration_credential,
#         expected_challenge=challenge.challenge,
#         expected_origin=f"https://{_hostname()}",
#         expected_rp_id=_hostname(),
#     )

#     # At this point verification has succeeded and we can save the credential
#     credential = WebAuthnCredential(
#         user=user,
#         credential_public_key=auth_verification.credential_public_key,
#         credential_id=auth_verification.credential_id,
#     )

#     db.session.add(credential)
#     db.session.commit()

#     # Remove the used challenge
#     db.session.delete(challenge)
#     db.session.commit()


# def prepare_login_with_credential(user):
#     """
#     Prepare the authentication options for a user trying to log in.
#     """
#     allowed_credentials = [
#         PublicKeyCredentialDescriptor(id=credential.credential_id)
#         for credential in user.credentials
#     ]

#     authentication_options = webauthn.generate_authentication_options(
#         rp_id=_hostname(),
#         allow_credentials=allowed_credentials,
#     )

#     # Store the challenge in the database
#     challenge = AuthenticationChallenge(
#         user_uid=user.uid,
#         challenge=authentication_options.challenge,
#         expires_at=datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
#     )
#     try:
#         db.session.add(challenge)
#         db.session.commit()
#     except IntegrityError:
#         db.session.rollback()  # Rollback the session to clear the failed transaction
#         db.session.query(AuthenticationChallenge).filter_by(user_uid=user.uid).update(
#             {
#                 "challenge": authentication_options.challenge,
#                 "expires_at": datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
#             }
#         )
#         db.session.commit()

#     return json.loads(webauthn.options_to_json(authentication_options))


# def verify_authentication_credential(user, authentication_credential):
#     """
#     Verify a submitted credential against a credential in the database and the
#     challenge stored in the database.
#     """
#     challenge = db.session.query(AuthenticationChallenge).filter_by(user_uid=user.uid).first()
#     print(authentication_credential.id)
#     stored_credential = (
#         WebAuthnCredential.query.with_parent(user)
#         .filter_by(
#             credential_id=webauthn.base64url_to_bytes(authentication_credential.id)
#         )
#         .first()
#     )

#     # This will raise if the credential does not authenticate
#     # It seems that safari doesn't track credential sign count correctly, so we just
#     # have to leave it on zero so that it will authenticate
#     webauthn.verify_authentication_response(
#         credential=authentication_credential,
#         expected_challenge=challenge.challenge,
#         expected_origin=f"https://{_hostname()}",
#         expected_rp_id=_hostname(),
#         credential_public_key=stored_credential.credential_public_key,
#         credential_current_sign_count=0,
#     )

#     # Remove the used challenge
#     db.session.delete(challenge)
#     db.session.commit()

#     # Update the credential sign count after using, then save it back to the database.
#     # This is mainly for reference since we can't use it because of Safari's weirdness.
#     stored_credential.current_sign_count += 1
#     db.session.add(stored_credential)
#     db.session.commit()


# salt = bcrypt.gensalt()


# def generate_magic_link(user_uid):
#     """Generate a special secret link to log in a user and save a hash of the secret."""
#     url_secret = secrets.token_urlsafe()
#     secret_hash = bcrypt.hashpw(url_secret.encode('utf-8'), salt)
#     expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)

#     # Store the secret hash in the database
#     email_auth_secret = EmailAuthSecret(
#         user_uid=user_uid,
#         secret_hash=secret_hash,
#         expires_at=expires_at
#     )

#     try:
#         db.session.add(email_auth_secret)
#         db.session.commit()
#     except IntegrityError:
#         db.session.rollback()  # Rollback the session to clear the failed transaction
#         db.session.query(EmailAuthSecret).filter_by(user_uid=user_uid).update(
#             {
#                 "secret_hash": secret_hash,
#                 "expires_at": expires_at
#             }
#         )
#         db.session.commit()
    
#     # db.session.add(email_auth_secret)
#     # db.session.commit()

#     return url_for(
#         "external_auth.magic_link", secret=url_secret, _external=True, _scheme="https"
#     )


# def verify_magic_link(user_uid, secret):
#     """Verify the secret from a magic login link against the saved hash for that
#     user."""
#     email_auth_secret = db.session.query(EmailAuthSecret).filter_by(user_uid=user_uid).first()
#     try:
#         if bcrypt.checkpw(secret.encode('utf-8'), email_auth_secret.secret_hash):
#             db.session.delete(email_auth_secret)
#             db.session.commit()
#             return True
#     except ValueError:
#         return False
#     return False