from models import db
from datetime import datetime

class ChoreRequest(db.Model):
    __tablename__ = "chorerequests"

    id = db.Column(db.Integer, primary_key=True)
    request_created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    request_created_for_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    requested_point_amount_requested = db.Column(db.Integer, nullable=False, default=0)
    household_id = db.Column(db.Integer, db.ForeignKey('households.id'), nullable=False)
    is_request_active = db.Column(db.Boolean, default=True)
    request_created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    request_fulfilled_at = db.Column(db.DateTime, nullable=True)
    request_fulfilled_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    request_reason_created = db.Column(db.String(999), nullable=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def get_dollar_amount(self):
        return float(f"{self.requested_point_amount_requested / 100:.2f}")
    
