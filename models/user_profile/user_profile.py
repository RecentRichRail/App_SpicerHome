import uuid
from datetime import datetime
from resources.utils.util import EncryptedType

from models import db, CommandsModel
from sqlalchemy.orm import backref

def _str_uuid():
    return str(uuid.uuid4())

class User(db.Model):
    """A user in the database"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(EncryptedType(255), nullable=False)
    default_search_id = db.Column(db.Integer, db.ForeignKey("commands.id"), unique=False, nullable=False)
    user_theme = db.Column(db.String(255), nullable=False, default="coffee")
    uid = db.Column(db.String(40), nullable=False, unique=True)
    username = db.Column(EncryptedType(255), unique=True, nullable=False)
    name = db.Column(EncryptedType(255), nullable=True)
    geo = db.Column(EncryptedType(255), nullable=True, default="Unknown")
    requests = db.relationship("RequestsModel", back_populates="user", lazy="dynamic")
    permissions = db.relationship("PermissionsModel", back_populates="user", lazy="dynamic")
    # network_password = db.relationship("NetworkPasswordModel", back_populates="user", lazy="dynamic")
    datetime_of_create_on_database = db.Column(db.DateTime, unique=False, nullable=True, default=datetime.utcnow)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return f"<User {self.username}>"

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_active(self):
        return True

    def get_id(self):
        return self.uid
    
    def json_user_permissions(self):
        user_permissions = []
        permissions_model = self.permissions
        if permissions_model:
            for permission in permissions_model:
                permissions_dict = permission.to_dict()
                user_permissions.append(permissions_dict)
        return user_permissions
    
    def json_user_commands(self):
        user_commands = []
        json_user_permissions = self.json_user_permissions()
        for permission in json_user_permissions:
            if permission['permission_name'] == "commands":
                # Retrieve all commands
                commands_model = CommandsModel.query.all()
                
                for command in commands_model:
                    command_dict = command.to_dict()
                    
                    # Filter commands based on permission level
                    if command_dict['permission_level'] is None or command_dict['permission_level'] >= permission['permission_level']:
                        user_commands.append(command_dict)
                    # else:
                    #     print(f"No permission to {command.prefix}")
        return user_commands
    
    def json_sidebar_links(self):
        sidebar_links = []
        added_urls = []
        json_user_commands = self.json_user_commands()
        for command in json_user_commands:
            if command["category"] == "shortcut" and command["url"].startswith("/internal/") and command["url"] not in added_urls:
                sidebar_links.append({"href": command["url"], "text": command["prefix"].capitalize(), "data_tab": command["prefix"]})
                added_urls.append(command["url"])

        return sidebar_links

    def json_user_search_commands(self):
        user_search_commands = []
        added_urls = []
        json_user_commands = self.json_user_commands()
        for command in json_user_commands:
            if "search" in command["category"]:
                if command["url"] in added_urls:
                    for user_command in user_search_commands:
                        if user_command["id"] == command["id"]:
                            if len(command["prefix"]) > len(user_command["text"]):
                                user_command["text"] = command["prefix"].capitalize()
                            break
                else:
                    user_search_commands.append({"id": command["id"], "text": command["prefix"].capitalize(), "prefix": command["prefix"]})
                    added_urls.append(command["url"])

        return user_search_commands
    
    def is_in_household(self):
        from models.user_data.chores.chores import ChoresUser
        user_household_model = ChoresUser.query.filter_by(user_id=self.id).first()
        if user_household_model:
            if self.is_household_admin():
                return user_household_model.household_id
            else:
                return user_household_model.household_id
        else:
            return False
    
    def get_dollar_amount(self):
        from models.user_data.chores.chores import ChoresUser
        user_points_model = ChoresUser.query.filter_by(user_id=self.id).first()
        if user_points_model:
            return user_points_model.get_dollar_amount()
        else:
            return False
        
    def is_household_admin(self):
        from models.user_data.chores.chores import ChoresUser
        user_points_model = ChoresUser.query.filter_by(user_id=self.id).first()
        if user_points_model and user_points_model.household_admin:
            return True
        else:
            return False