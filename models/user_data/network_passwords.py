import secrets
import string
from models import db
from models.user_data.commands import CommandsModel
from models.user_profile.user_profile import User

class NetworkPasswordModel(db.Model):
    __tablename__ = "network_passwords"

    id = db.Column(db.Integer, primary_key=True, unique=False, nullable=False, autoincrement=True)
    password = db.Column(db.String(16), nullable=False, default=lambda: NetworkPasswordModel.generate_password())
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=False, nullable=False)
    user = db.relationship("User", back_populates="network_password")

    @staticmethod
    def generate_password(length=16):
        alphabet = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(alphabet) for _ in range(length))