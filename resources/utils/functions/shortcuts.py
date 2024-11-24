import urllib.parse
from flask import current_app
import logging
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

from models import db, CommandsModel, RequestsModel

def run(data):
    current_user, search_query_prefix, user_query, _ = data

    search_query = user_query.replace(search_query_prefix, '', 1).strip()
    is_search = bool(search_query)

    user_commands = current_user.json_user_commands()
    shortcut_command = next((cmd for cmd in user_commands if cmd['prefix'] == search_query_prefix), None)

    if not shortcut_command:
        logging.info(f"User search '{user_query}' was not a shortcut.")
        return {"function_triggered": False}

    encoded_query = urllib.parse.quote_plus(search_query) if is_search and shortcut_command.get('search_url') else None

    if is_search and not encoded_query:
        logging.info(f"User search '{user_query}' shortcut does not have 'search_url'.")
        return {"function_triggered": False}

    request_dict_format = {
        "original_request": user_query,
        "user_id": current_user.id,
        "prefix": search_query_prefix,
        "search_query": search_query,
        "encoded_query": encoded_query,
        "is_search": is_search,
        "command_id": shortcut_command['id'],
        "datetime_of_request": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    }

    request_model = RequestsModel(**request_dict_format)

    try:
        db.session.add(request_model)
        db.session.commit()
        print("Search request recorded.")
    except SQLAlchemyError as e:
        print(e)
        print("Failed to record search request.")

    function_return = shortcut_command['search_url'].format(encoded_query) if is_search else shortcut_command['url']
    logging.info(f"Shortcuts return - '{function_return}'.")

    return {"function_triggered": True, "internal_search": False, "function_return": function_return}