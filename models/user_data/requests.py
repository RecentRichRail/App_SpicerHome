from models import db
from models.user_data.commands import CommandsModel
from models.user_profile.user_profile import User

class RequestsModel(db.Model):
    __tablename__ = "requests"

    id = db.Column(db.Integer, primary_key=True, unique=False, nullable=False, autoincrement=True)
    original_request = db.Column(db.String(500), nullable=False)
    prefix = db.Column(db.String(500), unique=False)
    search_query = db.Column(db.String(500), unique=False)
    encoded_query = db.Column(db.String(500), unique=False)
    is_search = db.Column(db.Boolean, unique=False, nullable=False)
    command_id = db.Column(db.Integer, db.ForeignKey("commands.id"), unique=False, nullable=False)
    command = db.relationship("CommandsModel", back_populates="requests")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=False, nullable=False)
    # user_id = db.relationship("users", back_populates="requests")
    user = db.relationship("User", back_populates="requests")
    datetime_of_request = db.Column(db.DateTime, unique=False, nullable=False)