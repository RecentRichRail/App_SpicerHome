from models import db

class ChoresUser(db.Model):
    __tablename__ = "chores"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    dollar_amount = db.Column(db.Integer, nullable=False, default=0)
    household_id = db.Column(db.Integer, db.ForeignKey('households.id'), nullable=True)
    household_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<User {self.name}>'
    
    def get_dollar_amount(self):
        return f"${self.dollar_amount / 100:.2f}"