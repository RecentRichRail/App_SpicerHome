from flask import Blueprint, request, jsonify, current_app
import requests
from models import UsersModel, CommandsModel, BananaGameUserBananasModel, BananaGameLifetimeBananasModel, BananaGameButtonPressModel, RequestsModel, TrackingNumbersModel, PermissionsModel
from models import db
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from tracking_numbers import get_tracking_number


def get_user(user):
    data = {}
    data['user_info'] = {
        'user_id': user_sub['sub'],
        'default_search_id': user_query['default_search_id'],
        'user_theme': user_query['user_theme'],
        'user_email': {'email': user_sub['email']['address'],
        'is_email_valid': user_sub['email']['is_verified']}
        }

    user_permissions = []
    permissions_model = PermissionsModel.query.filter_by(user_id=user_sub['sub']).all()
    if permissions_model:
        for permission in permissions_model:
            permissions_dict = permission.to_dict()
            user_permissions.append(permissions_dict)
    data['user_permissions'] = user_permissions
    print(f"User Permissions = {data['user_permissions']}")

    user_commands = []
    for permission in data['user_permissions']:
        if permission['permission_name'] == "commands":
            # Retrieve all commands
            commands_model = CommandsModel.query.all()
            
            for command in commands_model:
                command_dict = command.to_dict()
                
                # Filter commands based on permission level
                if command_dict['permission_level'] is None or command_dict['permission_level'] >= permission['permission_level']:
                    user_commands.append(command_dict)
                else:
                    print(f"No permission to {command.prefix}")

    data['user_commands'] = user_commands

    sidebar_links = []
    added_urls = []
    for command in data['user_commands']:
        if command["category"] == "shortcut" and command["url"].startswith("/internal/") and command["url"] not in added_urls:
            sidebar_links.append({"href": command["url"], "text": command["prefix"].capitalize(), "data_tab": command["prefix"]})
            added_urls.append(command["url"])

    data['user_sidebar_links'] = sidebar_links

    user_search_commands = []
    added_urls = []

    for command in data['user_commands']:
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

    data['user_search_commands'] = user_search_commands

    return jsonify(data)