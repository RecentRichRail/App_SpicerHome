from models import db
from resources.utils.util import EncryptedType

class Household(db.Model):
    __tablename__ = "households"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(EncryptedType(255), unique=True, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    owner = db.relationship('User', backref='owned_households', foreign_keys=[owner_id])
    members = db.relationship('ChoresUser', backref='household', lazy=True)

    def __repr__(self):
        return f'<Household {self.name}>'