import urllib.parse
from flask import current_app
import logging
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

from models import db, CommandsModel, RequestsModel

# data = [current_user, search_query_prefix, search_query, offset]

def run(data):
    search_query_prefix = data[1]
    user_query = data[2]
    current_user = data[0]

    search_query = user_query.replace(search_query_prefix, '', 1).strip()
    if search_query == "":
        search_query = None
        is_search = False
    else:
        is_search = True

    # print(data['user_commands'])
    user_commands = current_user.json_user_commands()

    shortcut_command = next((cmd for cmd in user_commands if cmd['prefix'] == search_query_prefix), None)
    # shortcut_command_model = CommandsModel.query.filter_by(prefix=data['user_query']['prefix']).first()
    # if shortcut_command_model != None:
    if shortcut_command:
        if is_search:
            # Need to see if shortcut_command['search_url'] is a valid URL
            if shortcut_command['search_url']:
                encoded_query = urllib.parse.quote_plus(search_query)
            else:
                print("No search URL found.")
                return {"funtion_triggered": False}
            # user_query['encoded_query'] = encoded_query
        else:
            encoded_query = None
    else:
        return {"function_triggered": False}
    
    # print(data['user_query']['encoded_query'])

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

    # print("search_request data = ", request_dict_format)

    request_model = RequestsModel(**request_dict_format)

    try:
        db.session.add(request_model)
        db.session.commit()
        print("Search request recorded.")
    except SQLAlchemyError as e:
        print(e)
        print("Failed to record search request.")

    # if shortcut_command['search_url'].beginswith("/internal/search?"):
    #     "internal_search": script_return.get("internal_search", False),

    if is_search:
        # if "/internal/search" == shortcut_command['url']:
        #     return {"internal_search": True, "funtion_triggered": True, "funtion_return": shortcut_command['search_url'].format(data['user_query']['encoded_query'])}
        # print(f"redirecting to {shortcut_command['search_url'].format(encoded_query)}")
        return {"funtion_triggered": True, "funtion_return": shortcut_command['search_url'].format(encoded_query)}

    else:
        # print(f"redirecting to {shortcut_command['url']}")
        return {"funtion_triggered": True, "funtion_return": shortcut_command['url']}