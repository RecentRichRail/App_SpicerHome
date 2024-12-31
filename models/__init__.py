from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

from models.user_data.commands import CommandsModel
from models.user_data.tracking_numbers import TrackingNumbersModel
from models.user_data.requests import RequestsModel
# from models.user_data.network_passwords import NetworkPasswordModel

from models.user_profile.user_profile import User
from models.user_profile.permissions import PermissionsModel

# from models.user_login.webauthn import WebAuthnCredential
# from models.user_login.login_attempts import LoginAttemptModel
# from models.user_login.challenges import RegistrationChallenge, AuthenticationChallenge, EmailAuthSecret

# from models.user_data.banana_game.banana_game_button_press import BananaGameButtonPressModel
# from models.user_data.banana_game.banana_game_user_bananas import BananaGameUserBananasModel
# from models.user_data.banana_game.banana_game_user_bananas_lifetime import BananaGameLifetimeBananasModel

from models.user_data.chores.chores import ChoresUser
from models.user_data.chores.households import Household
from models.user_data.chores.requests import ChoreRequest
from models.user_data.chores.points_request import PointsRequest