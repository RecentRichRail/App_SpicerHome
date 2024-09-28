import datetime
import json
import os
import secrets
from urllib.parse import urlparse

import bcrypt
import webauthn
from flask import request, url_for
from webauthn.helpers.structs import PublicKeyCredentialDescriptor

from models import WebAuthnCredential, db
from sqlalchemy import Column, String, DateTime, LargeBinary
from sqlalchemy.ext.declarative import declarative_base

# Base = declarative_base()
Base = db.Model

class RegistrationChallenge(Base):
    __tablename__ = 'registration_challenges'
    user_uid = Column(String(40), primary_key=True)
    challenge = Column(LargeBinary)
    expires_at = Column(DateTime)

class AuthenticationChallenge(Base):
    __tablename__ = 'authentication_challenges'
    user_uid = Column(String(40), primary_key=True)
    challenge = Column(LargeBinary)
    expires_at = Column(DateTime)

class EmailAuthSecret(Base):
    __tablename__ = 'email_auth_secrets'
    user_uid = Column(String(40), primary_key=True)
    secret_hash = Column(LargeBinary)
    expires_at = Column(DateTime)