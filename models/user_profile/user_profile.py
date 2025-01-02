import uuid, logging
from datetime import datetime
from resources.utils.util import EncryptedType

from models import db, CommandsModel
from sqlalchemy.orm import backref
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from flask import request, session, current_app
import requests

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
    household = db.relationship("ChoresUser", back_populates="user", lazy="dynamic")
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
        json_user_permissions = {perm['permission_name']: perm['permission_level'] for perm in self.json_user_permissions()}
        json_public_user_commands = CommandsModel.query.filter_by(is_command_hidden=False, is_command_public=True).all()
        json_private_user_commands = CommandsModel.query.filter_by(is_command_hidden=False, is_command_public=False, owner_id=self.id).all()
        if self.is_in_household():
            json_household_commands = CommandsModel.query.filter_by(is_command_hidden=False, is_command_household=True, household_id=self.is_in_household()).all()
        else:
            json_household_commands = []
        for command_list in (json_public_user_commands, json_private_user_commands, json_household_commands):
            for command in command_list:
                if command:
                    command = command.to_dict()
                if command["permission_name"] in json_user_permissions and command["permission_level"] >= json_user_permissions[command["permission_name"]]:
                    user_commands.append(command)

        # for permission in json_user_permissions:
        #     if permission['permission_name'] == "commands":
                
        #         for command in commands_model:
        #             command_dict = command.to_dict()
                    
        #             # Filter commands based on permission level
        #             if command_dict['permission_level'] is None or command_dict['permission_level'] >= permission['permission_level']:
        #                 user_commands.append(command_dict)
        #             # else:
        #             #     print(f"No permission to {command.prefix}")
        return user_commands
    
    def json_sidebar_links(self):
        sidebar_links = []
        added_urls = []
        # json_user_commands = self.json_user_commands()
        json_user_permissions = {perm['permission_name']: perm['permission_level'] for perm in self.json_user_permissions()}
        json_public_user_commands = CommandsModel.query.filter_by(is_command_hidden=False, is_command_for_sidebar=True, is_command_public=True).all()
        json_private_user_commands = CommandsModel.query.filter_by(is_command_hidden=False, is_command_for_sidebar=True, is_command_public=False, owner_id=self.id).all()
        if self.is_in_household():
            json_household_commands = CommandsModel.query.filter_by(is_command_hidden=False, is_command_for_sidebar=True, is_command_household=True, household_id=self.is_in_household()).all()
        else:
            json_household_commands = []
        for command_list in (json_public_user_commands, json_private_user_commands, json_household_commands):
            for command in command_list:
                if command:
                    command = command.to_dict()
                if command["url"] not in added_urls and (command["permission_name"] in json_user_permissions and command["permission_level"] >= json_user_permissions[command["permission_name"]]):
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
    
    def pending_household_request(self):
            from models import HouseholdJoinRequest
            pending_request = HouseholdJoinRequest.query.filter_by(request_created_for_user_id=self.id, is_request_active=True).first()
            if pending_request:
                logging.info(f"Pending request found for user {self.id}")
                return pending_request

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
        
    def get_points_amount(self):
        from models.user_data.chores.chores import ChoresUser
        user_points_model = ChoresUser.query.filter_by(user_id=self.id).first()
        if user_points_model:
            return user_points_model.dollar_amount
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
        
    @classmethod
    def get_user_identity_from_cloudflare(cls):
        logging.debug(f"Syncronizing user object with identity.")
        cf_authorization = request.cookies.get("CF_Authorization")
        session['cloudflare']['cf_authorization'] = cf_authorization
        if not cf_authorization:
            logging.error("CF_Authorization cookie missing.")
            return None

        try:
            response = requests.get(
                current_app.config['IDENTITY_ENDPOINT'],
                headers={"cookie": f"CF_Authorization={cf_authorization}"}
            )
            response.raise_for_status()
            identity = response.json()
            logging.info(f"Fetched identity for user: {identity.get('email')}")
            # logging.debug(f"Identity: {identity}")
            return identity
        except requests.RequestException as e:
            logging.error(f"Error fetching Cloudflare identity: {e}")
            return None
        
    @classmethod
    def get_user_from_cloudflare_cookie(cls):
        cf_authorization = request.cookies.get("CF_Authorization")
        if not cf_authorization:
            # No cookie found
            logging.error("CF_Authorization cookie missing.")
            return None

        # Fetch user identity from Cloudflare
        user_identity = cls.get_user_identity_from_cloudflare()
        if user_identity:
            # Check if user exists in database
            user = User.query.filter_by(uid=user_identity.get("user_uuid")).first()
            if user:
                # If the user exists, return the user object
                logging.info(f"User found in database: {user_identity.get('email')}")
                return user
            else:
                # If the user does not exist, create a new user
                logging.info(f"User not found in database: {user_identity.get('email')}")
                return cls.create_user(user_identity)
        else:
            # If the user identity is not found, return None
            logging.error("User identity not found.")
            return None


    @classmethod
    def create_user(cls, identity = None):
        if identity is None:
            logging.error("Identity not provided")
            identity = cls.get_user_identity_from_cloudflare()
            if identity is None:
                logging.error("Identity not found, aborting user creation.")
                return None

        from models import PermissionsModel
        email = identity.get("email")
        uid = identity.get("user_uuid")
        geo = identity.get("country")
        name = identity.get("name", email.split('@')[0])  # Fallback to email prefix if name is not provided
        username = identity.get("username", email.split('@')[0])  # Fallback to email prefix if username is not provided

        try:
            # Check if user exists
            logging.debug(f"Fetching user by UID: {uid}")
            user = User.query.filter_by(uid=identity.get("user_uuid")).first()
            if user:
                logging.info(f"User already exists: {email}")
                return None

            # Fetch default search command
            cmd_query = CommandsModel.query.filter_by(category="default_search").first()
            logging.info(f"Fetching default search command")
            if not cmd_query:
                logging.error("Default search command not found")
                raise ValueError("Default search command is required but not available")

            # Create new user
            user = User(
                uid=uid,
                name=name,
                geo=geo,
                username=username,
                email=email,
                default_search_id=cmd_query.id,
            )

            logging.info(f"Creating new user: {email}")
            db.session.add(user)
            db.session.commit()
            logging.info(f"User created successfully: {email}")

            # Assign permissions
            logging.info(f"Assigning permissions to user: {email}")
            user_permissions = PermissionsModel(
                user_id=user.id,
                permission_name="commands",
                permission_level=999
            )
            logging.info(f"Adding permissions to user: {email}")
            db.session.add(user_permissions)
            db.session.commit()
            logging.info(f"Permissions added successfully: {email}")
            logging.info(f"User created successfully: {email}")
            return user

        except IntegrityError as e:
            logging.error(f"Database integrity error: {e}")
            db.session.rollback()
        except Exception as e:
            logging.error(f"Error synchronizing user: {e}")
            db.session.rollback()