from models import db
from resources.utils.util import EncryptedType
# from models.user_data.requests import RequestsModel

class CommandsModel(db.Model):
    __tablename__ = "commands"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    category = db.Column(db.String(500))
    prefix = db.Column(db.String(255), nullable=False)
    url = db.Column(EncryptedType(1500))
    search_url = db.Column(EncryptedType(1500), nullable=True)
    permission_name = db.Column(db.String(255), unique=False, nullable=False, default="commands")
    permission_level = db.Column(db.Integer, unique=False, nullable=False, default=999)
    is_command_for_sidebar = db.Column(db.Boolean, unique=False, nullable=False, default=False)
    is_command_public = db.Column(db.Boolean, unique=False, nullable=False, default=True)
    is_command_household = db.Column(db.Boolean, unique=False, nullable=False, default=False)
    is_command_hidden = db.Column(db.Boolean, unique=False, nullable=False, default=False)
    household_id = db.Column(db.Integer, db.ForeignKey("households.id"), unique=False, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=False, nullable=True)
    requests = db.relationship("RequestsModel", back_populates="command", lazy="dynamic")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    @classmethod
    def create_command(cls, category, prefix, url, search_url = None, permission_name = "commands", permission_level = 999, is_command_for_sidebar = False, is_command_public = False, is_command_household = False, is_command_hidden = False, household_id = None, owner_id = None):
        new_command = cls(
            category=category,
            prefix=prefix,
            url=url,
            search_url=search_url,
            permission_name=permission_name,
            permission_level=permission_level,
            is_command_for_sidebar=is_command_for_sidebar,
            is_command_public=is_command_public,
            is_command_household=is_command_household,
            is_command_hidden=is_command_hidden,
            household_id=household_id,
            owner_id=owner_id
        )
        db.session.add(new_command)
        db.session.commit()
        return new_command