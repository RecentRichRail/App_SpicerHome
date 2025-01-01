import json, logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlparse, urljoin

from sqlalchemy.types import TypeDecorator, String
from cryptography.fernet import Fernet, InvalidToken
import base64

from flask import make_response, request, current_app

from models import db, User, CommandsModel, PermissionsModel

def create_commands():
    try:
        with open('src/commands.json', 'r') as file:
            commands_data = json.load(file)
            logging.info(f"commands.json file was loaded.")
    except FileNotFoundError:
        logging.error(f"Could not find commands.json file.")
        commands_data = {'commands': []}

    for single_command in commands_data['commands']:
        for single_command_single_prefix in single_command['prefix']:
            # Find if the command prfix exists
            cmd_query = CommandsModel.query.filter_by(prefix=single_command_single_prefix).first()
            if cmd_query:
                logging.info(f"Command already exists - {single_command_single_prefix}")
            else:
                # The class will automatically create the entry in the database
                new_command = CommandsModel.create_command(
                    category=single_command['category'],
                    prefix=single_command_single_prefix,
                    url=single_command['url'],
                    search_url=single_command.get('search_url'),
                    permission_name=single_command.get('permission_name', 'commands'),
                    permission_level=single_command.get('permission_level'),
                    is_command_for_sidebar=single_command.get('for_sidebar', False),
                    is_command_public=True
                )
                logging.info(f"Command created successfully - {single_command_single_prefix}")