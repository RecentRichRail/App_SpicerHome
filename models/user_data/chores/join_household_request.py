from models import db, User
from datetime import datetime
from resources.utils.util import EncryptedType

class HouseholdJoinRequest(db.Model):
    __tablename__ = "household_join_requests"

    id = db.Column(db.Integer, primary_key=True)
    request_created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    request_created_for_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    household_id = db.Column(db.Integer, db.ForeignKey('households.id'), nullable=False)
    is_request_active = db.Column(db.Boolean, default=True)
    request_created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    request_fulfilled_at = db.Column(db.DateTime, nullable=True)
    request_fulfilled_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    request_cancelled_at = db.Column(db.DateTime, nullable=True)
    requst_cancelled_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def created_by_name(self):
        if self.request_created_by_user_id is None:
            return None
        return User.query.filter_by(id=self.request_created_by_user_id).first().name
    
    def created_for_name(self):
        if self.request_created_for_user_id is None:
            return None
        return User.query.filter_by(id=self.request_created_for_user_id).first().name
    
    def cancelled_by_name(self):
        if self.requst_cancelled_by is None:
            return None
        return User.query.filter_by(id=self.requst_cancelled_by).first().name
    
    def approved_by_name(self):
        if self.request_fulfilled_by is None:
            return None
        return User.query.filter_by(id=self.request_fulfilled_by).first().name
    
    def get_household_name_from_id(self):
        from models import Household
        try:
            return Household.query.filter_by(id=self.household_id).first().name
        except:
            return None
        pass
        
    
    @classmethod
    def create_request(cls, request_created_by_user_id, request_created_for_user_id, household_id):
        new_request = cls(
            request_created_by_user_id=request_created_by_user_id,
            request_created_for_user_id=request_created_for_user_id,
            household_id=household_id
        )
        db.session.add(new_request)
        db.session.commit()
        return new_request

    def approve_request(self, request_fulfilled_by):
        from models import Household
        self.is_request_active = False
        self.request_fulfilled_at = datetime.utcnow()
        self.request_fulfilled_by = request_fulfilled_by
        db.session.commit()
        created_household_user = Household.query.filter_by(id=self.household_id).first().add_user_to_household(self.request_created_for_user_id)
        return created_household_user
    
    def deny_request(self, request_cancelled_by):
        self.is_request_active = False
        self.request_cancelled_at = datetime.utcnow()
        self.requst_cancelled_by = request_cancelled_by
        db.session.commit()
        return self