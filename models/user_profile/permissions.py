from models import db
from datetime import datetime

class PermissionsModel(db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=False, nullable=False)
    user = db.relationship("User", back_populates="permissions")
    permission_name = db.Column(db.String(80), nullable=False, default="commands")
    permission_level = db.Column(db.Integer, unique=False, default=999)
    datetime_of_update_on_database = db.Column(db.DateTime, unique=False, nullable=True, default=datetime.utcnow)
    datetime_of_create_on_database = db.Column(db.DateTime, unique=False, nullable=True, default=datetime.utcnow)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}