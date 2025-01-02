from models import db

class ChoresUser(db.Model):
    __tablename__ = "chore_users"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    user = db.relationship("User", back_populates="household")
    dollar_amount = db.Column(db.Integer, nullable=False, default=0)
    household_id = db.Column(db.Integer, db.ForeignKey('households.id'), nullable=False)
    household_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<User {self.name}>'
    
    def get_dollar_amount(self):
        return float(f"{self.dollar_amount / 100:.2f}")
    
    def get_user_name(self):
        if self.user.name:
            return self.user.name
        elif self.user.username:
            return self.user.username
        else:
            return self.user.email