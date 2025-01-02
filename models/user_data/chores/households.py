from models import db, CommandsModel
from resources.utils.util import EncryptedType
from datetime import datetime
import logging

from models import ChoresUser

class Household(db.Model):
    __tablename__ = "households"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(EncryptedType(255), unique=False, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    owner = db.relationship('User', backref='owned_households', foreign_keys=[owner_id])
    members = db.relationship('ChoresUser', backref='household', lazy=True)
    datetime_of_create_on_database = db.Column(db.DateTime, unique=False, nullable=True, default=datetime.utcnow)

    def __repr__(self):
        return f'<Household {self.name}>'
    
    @classmethod
    def create_household(cls, name, owner_id):
        if cls.query.filter_by(owner_id=owner_id).first():
            return None
        
        try:
            new_household = Household(name=name, owner_id=owner_id)
            db.session.add(new_household)
            db.session.commit()
            return new_household
        except:
            return None
    
    def add_user_to_household(self, user_id, household_admin = False):
        if ChoresUser.query.filter_by(user_id=user_id).first():
            return None
        
        new_user = ChoresUser(user_id=user_id, household_id=self.id, household_admin=household_admin)
        points_command = CommandsModel.create_command(category="shortcut", prefix=f"points", url=f"/internal/chores/", permission_level=999, is_command_for_sidebar=True, is_command_public=False, is_command_household=False, household_id=self.id, owner_id=user_id)
        db.session.add_all([new_user, points_command])
        db.session.commit()
        return new_user
    
    def get_household_name_from_id(self, household_id):
        return Household.query.filter_by(id=household_id).first().name