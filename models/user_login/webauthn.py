import uuid

# from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref
from models import db

class WebAuthnCredential(db.Model):
    """Stored WebAuthn Credentials as a replacement for passwords."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    credential_id = db.Column(db.LargeBinary, nullable=False)
    credential_public_key = db.Column(db.LargeBinary, nullable=False)
    current_sign_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<Credential {self.credential_id}>"