from models import db
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
        
        new_household = Household(name=name, owner_id=owner_id)
        new_choreuser = ChoresUser(user_id=owner_id, household_id=new_household.id, household_admin=True)
        db.session.add_all([new_household, new_choreuser])
        db.session.commit()
        return new_household
    
    def add_user_to_household(self, user_id):
        if ChoresUser.query.filter_by(user_id=user_id).first():
            return None
        
        new_user = ChoresUser(user_id=user_id, household_id=self.id)
        db.session.add(new_user)
        db.session.commit()
        return new_user