from models import db
from datetime import datetime

class ChoresUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    points = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<User {self.name}>'
    
class ChoreLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('chores_user.id'), nullable=False)
    action = db.Column(db.String(10), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('ChoresUser', backref=db.backref('logs', lazy=True))

    def __repr__(self):
        return f'<ChoreLog {self.action} {self.points} points for {self.user_id}>'