from models import db

class ChoresUser(db.Model):
    __tablename__ = "chores"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    dollar_amount = db.Column(db.Float, nullable=False, default=0.0)
    household_id = db.Column(db.Integer, db.ForeignKey('households.id'), nullable=True)
    household_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<User {self.name}>'