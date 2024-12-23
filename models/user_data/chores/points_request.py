from models import db, User
from datetime import datetime

class PointsRequest(db.Model):
    __tablename__ = "pointsrequests"

    id = db.Column(db.Integer, primary_key=True)
    request_name = db.Column(db.String(999), nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    household_id = db.Column(db.Integer, db.ForeignKey('households.id'), nullable=False)
    is_request_active = db.Column(db.Boolean, default=True)
    request_created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    points_requested = db.Column(db.Integer, nullable=False, default=0)
    daily_limit = db.Column(db.Integer, nullable=False, default=2)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def get_dollar_amount(self):
        return float(f"{self.requested_point_amount_requested / 100:.2f}")
    
    def created_by_name(self):
        if self.request_created_by_user_id is None:
            return None
        return User.query.filter_by(id=self.request_created_by_user_id).first().name
    
